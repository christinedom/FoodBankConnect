#!/usr/bin/env python3
# ============================================================================
#  © 2025 Francisco Vivas Puerto (aka “DaFrancc”)
#  All rights reserved. This file is part of the FoodBankConnect tooling.
#  You may use and distribute with proper attribution to the author.
# ============================================================================

from __future__ import annotations

import os
import time
import sys
import logging
import pathlib
import traceback
import importlib.util
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import asyncio
import inspect
import queue

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
log = logging.getLogger(__name__)
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
SCRAPERS_DIR = pathlib.Path(os.environ.get("SCRAPERS_DIR", "/app/scrapers")).resolve()
LIST_FILE = (SCRAPERS_DIR / "scrapers.txt").resolve()

# Determine worker count
try:
    DEFAULT_WORKERS = max(os.cpu_count() or 2, 8)
except Exception:
    DEFAULT_WORKERS = 8
MAX_WORKERS = int(os.environ.get("SCRAPER_MAX_WORKERS", DEFAULT_WORKERS))

# Per-task timeout (seconds)
SCRAPER_TIMEOUT_SECS = float(os.environ.get("SCRAPER_TIMEOUT_SECS", "1000"))

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _read_list_file(path: pathlib.Path) -> List[pathlib.Path]:
    """
    Read `scrapers.txt` and return absolute paths of valid `.py` scraper files.
    - Ignores blank lines and comment lines starting with '#'
    - Supports absolute or relative paths (relative to SCRAPERS_DIR)
    - Logs warnings for invalid lines
    """
    if not path.exists():
        msg = f"[scraper] scrapers list file not found: {path}"
        print(msg, file=sys.stderr)
        log.warning(msg)
        return []

    out: List[pathlib.Path] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        fpath = (SCRAPERS_DIR / line).resolve() if not pathlib.Path(line).is_absolute() else pathlib.Path(line)
        if not (fpath.exists() and fpath.suffix == ".py"):
            print(f"[scraper] Line {i}: '{line}' is not a valid .py in {SCRAPERS_DIR} (skipping)", file=sys.stderr)
            log.error("Line %d invalid: %s", i, fpath)
            continue
        out.append(fpath)
    return out


def _load_module(pyfile: pathlib.Path):
    """
    Dynamically import a Python file as a module with a unique name.
    This prevents namespace collisions when loading multiple scrapers.
    """
    mod_name = f"scraper_file_{pyfile.stem}_{abs(hash(str(pyfile)))}"
    spec = importlib.util.spec_from_file_location(mod_name, str(pyfile))
    if not spec or not spec.loader:
        raise ImportError(f"Cannot import {pyfile}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _call_with_timeout(fn: Callable[[], Any], timeout_s: float) -> Any:
    """
    Run a callable in a helper thread with a timeout.
    Returns the callable's result or raises TimeoutError if it doesn't finish.
    """
    q: "queue.Queue[tuple[bool, Any]]" = queue.Queue(maxsize=1)

    def runner() -> None:
        try:
            q.put((True, fn()))
        except BaseException as e:
            q.put((False, e))

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    try:
        ok, val = q.get(timeout=timeout_s)
    except queue.Empty:
        raise TimeoutError(f"no progress within {timeout_s:.1f}s")
    if ok:
        return val
    raise val  # re-raise exception from worker

# ----------------------------------------------------------------------------
# Core runner for a single scraper (with timeout + robust error handling)
# ----------------------------------------------------------------------------
def _run_one(pyfile: pathlib.Path) -> List[Dict[str, Any]]:
    """
    Execute a single scraper and return a list of dictionaries.
    - Logs START/FINISH and elapsed time
    - Supports sync and async scrape()
    - Enforces a timeout via SCRAPER_TIMEOUT_SECS
    - Gracefully returns [] on error or timeout (does not raise)
    """
    started = time.perf_counter()
    print(f"[scraper] START  {pyfile.name}")
    try:
        mod = _load_module(pyfile)
        fn = getattr(mod, "scrape", None)

        if not callable(fn):
            print(f"[scraper] ERROR  {pyfile.name}: no top-level scrape()", file=sys.stderr)
            return []

        def call_sync() -> Any:
            if inspect.iscoroutinefunction(fn):
                return asyncio.run(asyncio.wait_for(fn(), timeout=SCRAPER_TIMEOUT_SECS))
            result = fn()
            if inspect.isawaitable(result):
                return asyncio.run(asyncio.wait_for(result, timeout=SCRAPER_TIMEOUT_SECS))
            return result

        data = _call_with_timeout(call_sync, SCRAPER_TIMEOUT_SECS)

        if data is None:
            data = []
        if not isinstance(data, list):
            print(f"[scraper] ERROR  {pyfile.name}: scrape() returned {type(data).__name__}, expected list -> []", file=sys.stderr)
            return []

        valid: List[Dict[str, Any]] = []
        for idx, item in enumerate(data, start=1):
            if isinstance(item, dict):
                valid.append(item)
            else:
                print(f"[scraper] WARN   {pyfile.name}: item #{idx} is {type(item).__name__}, skipping", file=sys.stderr)
        return valid

    except TimeoutError as te:
        print(f"[scraper] TIMEOUT {pyfile.name}: {te}", file=sys.stderr)
        return []
    except Exception:
        print(f"[scraper] ERROR  {pyfile.name} failed:\n{traceback.format_exc()}", file=sys.stderr)
        return []
    finally:
        dur = time.perf_counter() - started
        print(f"[scraper] FINISH {pyfile.name} in {dur:.2f}s")

# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------
def scrape() -> List[Dict[str, Any]]:
    """
    Run all scrapers listed in `scrapers.txt` concurrently.
    Returns a flat list of all valid rows; failures/timeouts yield [] for that task.
    """
    files = _read_list_file(LIST_FILE)
    if not files:
        print(f"[scraper] No scrapers to run (empty or missing {LIST_FILE}).")
        return []

    print(f"[scraper] Discovered {len(files)} script(s): " + ", ".join(f.name for f in files))
    print(f"[scraper] Running up to {MAX_WORKERS} in parallel ...")

    results: List[Dict[str, Any]] = []
    lock = threading.Lock()

    try:
        start_all = time.perf_counter()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            future_map = {ex.submit(_run_one, f): f for f in files}
            for fut in as_completed(future_map):
                pyfile = future_map[fut]
                try:
                    rows = fut.result()
                except Exception:
                    print(f"[scraper] ERROR  Unexpected crash in future for {pyfile.name}:\n{traceback.format_exc()}", file=sys.stderr)
                    rows = []
                with lock:
                    if rows:
                        results.extend(rows)

        dur_all = time.perf_counter() - start_all
        print(f"[scraper] ALL DONE in {dur_all:.2f}s — total items: {len(results)}")
        return results

    except Exception:
        print(f"[scraper] FATAL unexpected error; returning partial results ({len(results)} items)\n{traceback.format_exc()}", file=sys.stderr)
        return results
