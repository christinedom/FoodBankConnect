# ============================================================= #
# Copyright (c) 2025 Francisco Vivas Puerto (aka "DaFrancc").
# All rights reserved.
# ============================================================= #

from typing import Any, Dict, List, Optional, Tuple
import os
import sys
import logging

from sqlalchemy import String, TIMESTAMP, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from scraper import scrape as run_all_scrapers


# -------------------------------------------------------------
# ORM Models
# -------------------------------------------------------------
class Base(DeclarativeBase):
    """
    /* Base metadata class for all ORM tables. */
    """


class FoodBank(Base):
    """/* Table storing food bank data. */"""
    __tablename__ = "foodbanks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(256))
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[Any] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class Program(Base):
    """/* Table storing program data. */"""
    __tablename__ = "programs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(256))
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[Any] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class Sponsor(Base):
    """/* Table storing sponsor data. */"""
    __tablename__ = "sponsors"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(256))
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[Any] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


# -------------------------------------------------------------
# Database utilities
# -------------------------------------------------------------
def get_engine():
    """
    /* Builds a SQLAlchemy engine using discrete DB environment variables.
       Preconditions:
           - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD must be set.
           - DB_SCHEMA is optional (defaults to 'public').
       Postconditions:
           - Returns a live SQLAlchemy Engine for PostgreSQL.
    */
    """
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    schema = os.getenv("DB_SCHEMA", "public")

    missing = [v for v in ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"] if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing required database environment variable(s): {', '.join(missing)}")

    # Build connection string manually
    conn_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    engine = create_engine(conn_str, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        conn.execute(f"SET search_path TO {schema};")
    return engine


def get_session(engine) -> Session:
    """/* Returns a new Session bound to the given engine. */"""
    return Session(engine)


# -------------------------------------------------------------
# Helpers for data normalization and insertion
# -------------------------------------------------------------
def normalize_buckets(rows: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """/* Splits rows into (foodbanks, programs, sponsors) by 'type' or '__bucket__'. */"""
    fb, prg, spn = [], [], []
    for r in rows:
        t = r.get("type") or r.get("__bucket__")
        if t == "foodbank":
            fb.append(r)
        elif t == "program":
            prg.append(r)
        elif t == "sponsor":
            spn.append(r)
    return fb, prg, spn


def coerce_kwargs(model, rec: Dict[str, Any]) -> Dict[str, Any]:
    """/* Maps record dict to ORM fields; ensures id and name exist. */"""
    rid = rec.get("id") or rec.get("uuid") or rec.get("slug")
    if not rid:
        raise KeyError("Record missing id/uuid/slug field.")
    return {"id": rid, "name": rec.get("name"), "data": rec}


def truncate_tables(session: Session) -> None:
    """/* Clears all data from target tables in one transaction. */"""
    session.query(FoodBank).delete()
    session.query(Program).delete()
    session.query(Sponsor).delete()


def bulk_insert(session: Session, model, items: List[Dict[str, Any]]) -> int:
    """/* Inserts multiple items of a given model. */"""
    if not items:
        return 0
    objs = [model(**coerce_kwargs(model, r)) for r in items]
    session.add_all(objs)
    return len(objs)


# -------------------------------------------------------------
# Main Orchestration
# -------------------------------------------------------------
def run_once() -> int:
    """
    /* Runs scrapers, writes to DB, exits. */
    """
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    dry_run = os.getenv("DRY_RUN") == "1"
    do_truncate = os.getenv("TRUNCATE", "1") == "1"

    logging.info("Starting scrape...")
    payload = run_all_scrapers()
    rows = payload.get("results", [])
    errors = payload.get("errors", [])
    if errors:
        logging.warning("Scraper errors detected: %d", len(errors))

    fb, prg, spn = normalize_buckets(rows)
    logging.info("Buckets: foodbanks=%d programs=%d sponsors=%d", len(fb), len(prg), len(spn))

    if dry_run:
        logging.info("Dry run enabled. No database writes performed.")
        return 0

    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        with get_session(engine) as s:
            try:
                if do_truncate:
                    truncate_tables(s)
                n1 = bulk_insert(s, FoodBank, fb)
                n2 = bulk_insert(s, Program, prg)
                n3 = bulk_insert(s, Sponsor, spn)
                s.commit()
                logging.info("Load complete. Inserted: fb=%d prg=%d spn=%d", n1, n2, n3)
                return 0
            except Exception:
                s.rollback()
                raise
    except Exception as exc:
        logging.exception("Load failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(run_once())
