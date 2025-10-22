# ============================================================================
#  © 2025 Francisco Vivas Puerto (aka “DaFrancc”)
#  All rights reserved. This file is part of the FoodBankConnect API.
#  Use and distribution permitted with attribution to the author.
# ============================================================================

#!/usr/bin/env python3
"""
Lightweight read-only API layer for FoodBankConnect.

This module:
- Validates schema/table names and maps public resources to DB tables.
- Opens a pooled pg8000 connection with SSL (prefers AWS RDS bundle).
- Provides data-access helpers to fetch one item or a paginated list.
- Exposes an AWS Lambda-style `lambda_handler` router for GET-only endpoints.
- Returns JSON responses with CORS headers and friendly error messages.

Written by: Francisco Vivas Puerto (aka “DaFrancc”)
"""

from __future__ import annotations

import json
import os
import re
import ssl
import logging
from typing import Any, Dict, List, Optional, Tuple

import pg8000

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ------------------------------------------------------------------------------
# Config / schema & tables
# ------------------------------------------------------------------------------
ALLOWED_TYPES: Dict[str, str] = {
    "foodbanks": "foodbank",
    "programs": "program",
    "sponsors": "sponsor",
}

SCHEMA = os.environ.get("DB_SCHEMA", "app")
_ident_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")  # unquoted PG identifier


def _validate_ident(name: str) -> str:
    """Validate that `name` is a simple, unquoted Postgres identifier."""
    if not _ident_re.match(name):
        raise RuntimeError(
            "Invalid DB_SCHEMA; must be a simple identifier like 'app' or 'public'"
        )
    return name


_schema = _validate_ident(SCHEMA)

TABLE_MAP: Dict[str, str] = {
    "foodbanks": f"{_schema}.foodbanks",
    "programs": f"{_schema}.programs",
    "sponsors": f"{_schema}.sponsors",
}

# ------------------------------------------------------------------------------
# DB connection (env vars + SSL)
# ------------------------------------------------------------------------------
_conn = None  # module-level cached connection


def _missing_db_envs(cfg: Dict[str, Optional[str]]) -> List[str]:
    """Return a list of missing required DB env var names."""
    required = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    name_map = {"DB_HOST": "host", "DB_NAME": "dbname", "DB_USER": "username", "DB_PASSWORD": "password"}
    return [k for k in required if not cfg.get(name_map[k])]


def _get_db_config() -> Dict[str, Any]:
    """Assemble DB config from env and validate presence of required entries."""
    cfg = {
        "host": os.environ.get("DB_HOST"),
        "dbname": os.environ.get("DB_NAME"),
        "username": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "port": int(os.environ.get("DB_PORT", "5432")),
    }
    missing = _missing_db_envs(cfg)
    if missing:
        logger.error("Missing DB env vars: %s", ",".join(missing))
        raise RuntimeError("Server not configured")
    return cfg


def _rds_bundle_path() -> str:
    """Return path to the AWS RDS CA bundle (env override if provided)."""
    return os.environ.get("RDS_CA_BUNDLE", "/etc/ssl/certs/rds-ca-global-bundle.pem")


def _ssl_ctx() -> ssl.SSLContext:
    """Build an SSL context that prefers the AWS RDS trust bundle."""
    cafile = _rds_bundle_path()
    try:
        if os.path.exists(cafile):
            return ssl.create_default_context(cafile=cafile)
    except Exception:
        pass
    return ssl.create_default_context()


def _healthcheck(conn) -> bool:
    """Return True if the connection answers a trivial SELECT."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception:
        return False


def _set_statement_timeout(conn, ms: int = 2000) -> None:
    """Best-effort set of statement_timeout on the session."""
    try:
        with conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {int(ms)}")
    except Exception:
        # Permission may be missing; not fatal.
        pass


def _open_conn() -> Any:
    """Open a new pg8000 connection with autocommit and sane timeouts."""
    cfg = _get_db_config()
    conn = pg8000.connect(
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["dbname"],
        user=cfg["username"],
        password=cfg["password"],
        ssl_context=_ssl_ctx(),
        timeout=10,
    )
    conn.autocommit = True
    _set_statement_timeout(conn, 2000)
    return conn


def _get_conn():
    """Create or reuse a healthy connection (autocommit)."""
    global _conn
    if _conn and _healthcheck(_conn):
        return _conn
    _conn = _open_conn()
    return _conn


# ------------------------------------------------------------------------------
# Missing tables helpers
# ------------------------------------------------------------------------------
def _split_schema_table(qualified: str) -> Tuple[str, str]:
    """Split `schema.table` into (schema, table)."""
    s, t = qualified.split(".", 1)
    return s, t


def _table_exists(conn, qualified: str) -> bool:
    """True if the `schema.table` exists."""
    schema, table = _split_schema_table(qualified)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
              SELECT 1
              FROM information_schema.tables
              WHERE table_schema = %s AND table_name = %s
            )
        """,
            (schema, table),
        )
        return bool(cur.fetchone()[0])


def _ensure_table_or_error(resource_kind: str) -> None:
    """Raise a marker error if the table for `resource_kind` is missing."""
    table = TABLE_MAP[resource_kind]
    conn = _get_conn()
    if not _table_exists(conn, table):
        raise RuntimeError(f"__MISSING_TABLES__:{table}")


def _friendly_missing_tables_response(missing_tables: List[str]):
    """Return a structured 503 response for missing DB tables."""
    body = {
        "error": "ServiceNotReady",
        "message": "Service is not ready: required database table(s) are missing. Ask an administrator to create them or set DB_SCHEMA correctly.",
        "details": {"schema": _schema, "missing": missing_tables},
    }
    return response(503, body)


def _is_missing_relation_error(exc: Exception) -> Optional[List[str]]:
    """If error indicates 'relation does not exist', return the relation name(s)."""
    s = str(exc)
    if "42P01" in s or ("relation" in s and "does not exist" in s):
        import re as _re

        m = _re.search(r'relation\s+"?([a-zA-Z0-9_\.]+)"?\s+does not exist', s)
        return [m.group(1)] if m else []
    return None


# ------------------------------------------------------------------------------
# Row mappers
# ------------------------------------------------------------------------------
def _row_to_obj(type_value: str, r, kind: str) -> Dict[str, Any]:
    """Map a DB row to an API object for the given resource `kind`."""
    if kind == "foodbanks":
        return {
            "type": type_value,
            "id": r[0],
            "name": r[1],
            "about": r[2],
            "website": r[3],
            "phone": r[4],
            "image": r[5],
            "address": r[6],
            "city": r[7],
            "state": r[8],
            "zipcode": r[9],
            "urgency": r[10],
            "capacity": r[11],
            "languages": r[12],
            "services": r[13],
            "open_hours": r[14],
            "eligibility": r[15],
            "fetched_at": r[16],
            "created_at": r[17].isoformat() if r[17] else None,
        }
    if kind == "programs":
        return {
            "type": type_value,
            "id": r[0],
            "name": r[1],
            "about": r[2],
            "host": r[3],
            "program_type": r[4],
            "frequency": r[5],
            "eligibility": r[6],
            "cost": r[7],
            "image": r[8],
            "details_page": r[9],
            "sign_up_link": r[10],
            "links": r[11],
            "fetched_at": r[12],
            "created_at": r[13].isoformat() if r[13] else None,
        }
    # sponsors
    return {
        "type": type_value,
        "id": r[0],
        "name": r[1],
        "about": r[2],
        "affiliation": r[3],
        "image": r[4],
        "alt": r[5],
        "contribution": r[6],
        "contribution_amt": r[7],
        "past_involvement": r[8],
        "sponsor_link": r[9],
        "city": r[10],
        "state": r[11],
        "ein": r[12],
        "contact": r[13],
        "media": r[14],
        "fetched_at": r[15],
        "created_at": r[16].isoformat() if r[16] else None,
    }


def _row_to_summary_foodbank(r) -> Dict[str, Any]:
    """Compact foodbank summary: id, name, address, city, zipcode, capacity, open_hours, urgency, image."""
    return {
        "id": r[0],
        "name": r[1],
        "address": r[2],
        "city": r[3],
        "zipcode": r[4],
        "capacity": r[5],
        "open_hours": r[6],
        "urgency": r[7],
        "image": r[8],
    }


# ------------------------------------------------------------------------------
# Data access
# ------------------------------------------------------------------------------
def _table_for(resource_kind: str) -> str:
    """Return schema-qualified table for resource kind."""
    return TABLE_MAP[resource_kind]


def _type_label_for(resource_kind: str) -> str:
    """Return external type label for resource kind."""
    return ALLOWED_TYPES[resource_kind]


def _select_one_sql(resource_kind: str) -> str:
    """Return the SELECT statement to fetch a single item by id for the resource."""
    table = _table_for(resource_kind)
    if resource_kind == "foodbanks":
        return f"""
            SELECT
                id, name, about, website, phone, image,
                address, city, state, zipcode, urgency,
                capacity, languages, services, open_hours, eligibility,
                fetched_at, created_at
            FROM {table}
            WHERE id = %s
        """
    if resource_kind == "programs":
        return f"""
            SELECT
                id, name, about, host, program_type, frequency,
                eligibility, cost, image, details_page, sign_up_link,
                links, fetched_at, created_at
            FROM {table}
            WHERE id = %s
        """
    # sponsors
    return f"""
        SELECT
            id, name, about, affiliation, image, alt,
            contribution, contribution_amt, past_involvement,
            sponsor_link, city, state, ein,
            contact, media, fetched_at, created_at
        FROM {table}
        WHERE id = %s
    """


def get_one(resource_kind: str, item_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single record by id and map it to an API object."""
    sql = _select_one_sql(resource_kind)
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, (item_id,))
        row = cur.fetchone()
    if not row:
        return None
    return _row_to_obj(_type_label_for(resource_kind), row, resource_kind)


# Pagination & listing ---------------------------------------------------------
MAX_PAGE_SIZE = int(os.environ.get("MAX_REQUESTS"))  # env: MAX_REQUESTS


def _clamp_page_size(size: Optional[int]) -> int:
    """Clamp requested page size to [1, MAX_PAGE_SIZE], raising if exceeded."""
    n = MAX_PAGE_SIZE if size is None else int(size)
    if n < 1:
        n = 1
    if n > MAX_PAGE_SIZE:
        raise ValueError(f"Requested size exceeds maximum ({MAX_PAGE_SIZE})")
    return n


def _base_select_for_list(resource_kind: str) -> str:
    """Return base SELECT (no WHERE/ORDER/LIMIT) for list endpoints."""
    table = _table_for(resource_kind)
    if resource_kind == "foodbanks":
        return f"""
            SELECT id, name, address, city, zipcode,
                   capacity, open_hours, urgency, image
            FROM {table}
        """
    if resource_kind == "programs":
        return f"""
            SELECT id, name, host, program_type, frequency, image
            FROM {table}
        """
    # sponsors
    return f"""
        SELECT id, name, affiliation, image, city, state
        FROM {table}
    """


def _order_sql_numeric_first() -> str:
    """ORDER BY numeric id first (ascending), then lexicographic id."""
    return """
        ORDER BY
            CASE WHEN id ~ '^[0-9]+$' THEN 0 ELSE 1 END,
            (CASE WHEN id ~ '^[0-9]+$' THEN id::bigint END),
            id
    """


def _apply_cursoring_sql(base_select: str, start: Optional[str], n: int) -> Tuple[str, Tuple[Any, ...]]:
    """
    Build the full SELECT + cursoring + limit query and parameters.

    - If start is None: numeric-first ordering from beginning.
    - If start is numeric: include numeric ids >= start, plus any non-numeric ids after.
    - If start is non-numeric: lexicographic continuation WHERE id >= start.
    """
    if start is None:
        sql = base_select + _order_sql_numeric_first() + "\nLIMIT %s"
        return sql, (n,)

    if str(start).isdigit():
        sql = base_select + """
            WHERE
              (id ~ '^[0-9]+$' AND id::bigint >= %s::bigint)
              OR (NOT id ~ '^[0-9]+$')
        """ + _order_sql_numeric_first() + "\nLIMIT %s"
        return sql, (start, n)

    # string cursor
    sql = base_select + """
        WHERE id >= %s
        ORDER BY id
        LIMIT %s
    """
    return sql, (start, n)


def _fetch_rows(conn, sql: str, params: Tuple[Any, ...]) -> List[tuple]:
    """Execute a read-only query and return all rows."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _map_summaries(resource_kind: str, rows: List[tuple]) -> List[Dict[str, Any]]:
    """Map list rows into compact summary dictionaries per resource kind."""
    if resource_kind == "foodbanks":
        return [_row_to_summary_foodbank(r) for r in rows]
    if resource_kind == "programs":
        return [
            {
                "id": r[0],
                "name": r[1],
                "host": r[2],
                "program_type": r[3],
                "frequency": r[4],
                "image": r[5],
            }
            for r in rows
        ]
    # sponsors
    return [
        {
            "id": r[0],
            "name": r[1],
            "affiliation": r[2],
            "image": r[3],
            "city": r[4],
            "state": r[5],
        }
        for r in rows
    ]


def _next_start_from(items: List[Dict[str, Any]]) -> Optional[str]:
    """Compute the next pagination cursor from the last item (if present)."""
    return items[-1]["id"] if items else None


def list_range(
    resource_kind: str, start: Optional[str], size: Optional[int]
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Return a page of compact summaries and the next cursor."""
    n = _clamp_page_size(size)
    base_select = _base_select_for_list(resource_kind)
    sql, params = _apply_cursoring_sql(base_select, start, n)
    rows = _fetch_rows(_get_conn(), sql, params)
    items = _map_summaries(resource_kind, rows)
    return items, _next_start_from(items)


# ------------------------------------------------------------------------------
# Response builders
# ------------------------------------------------------------------------------
def response(status: int, body: Any) -> Dict[str, Any]:
    """Build a standard API Gateway/Lambda JSON response with CORS headers."""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
        "body": json.dumps(body, ensure_ascii=False),
        "isBase64Encoded": False,
    }


def not_found(message: str = "Not found"):
    """Return a 404 response."""
    return response(404, {"error": "NotFound", "message": message})


def bad_request(message: str):
    """Return a 400 response."""
    return response(400, {"error": "BadRequest", "message": message})


def server_error(message: str = "Internal error"):
    """Return a 500 response."""
    return response(500, {"error": "InternalServerError", "message": message})


# ------------------------------------------------------------------------------
# Routing utilities
# ------------------------------------------------------------------------------
def _method_from_event(event: Dict[str, Any]) -> str:
    """Extract HTTP method from API Gateway HTTP API event."""
    return event.get("requestContext", {}).get("http", {}).get("method", "")  # type: ignore[return-value]


def _raw_path_from_event(event: Dict[str, Any]) -> str:
    """Extract raw path (e.g., /v1/foodbanks/1) from event."""
    return event.get("rawPath", "")


def _path_parts(raw_path: str) -> List[str]:
    """Split the raw path into non-empty parts."""
    return [p for p in raw_path.split("/") if p]


def _query_params(event: Dict[str, Any]) -> Dict[str, str]:
    """Extract querystring parameters (empty dict if none)."""
    return event.get("queryStringParameters") or {}


def _path_params(event: Dict[str, Any]) -> Dict[str, str]:
    """Extract path parameters (empty dict if none)."""
    return event.get("pathParameters") or {}


def _is_cors_preflight(method: str) -> bool:
    """True if the method is CORS preflight (OPTIONS)."""
    return method == "OPTIONS"


def _cors_preflight_response() -> Dict[str, Any]:
    """Return a 204 response for CORS preflight."""
    return {
        "statusCode": 204,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Max-Age": "600",
        },
        "body": "",
    }


def _ensure_route(parts: List[str]) -> Optional[str]:
    """Validate route parts and return the resource segment or None if invalid."""
    if len(parts) < 2 or parts[0] != "v1":
        return None
    return parts[1]


def _validate_resource(resource: str) -> bool:
    """True if the resource is one of the allowed types."""
    return resource in ALLOWED_TYPES


def _extract_item_id(parts: List[str], path_params: Dict[str, str]) -> Optional[str]:
    """Determine item id from either pathParameters or the 3rd path part."""
    item_id = path_params.get("id") if isinstance(path_params, dict) else None
    if not item_id and len(parts) >= 3:
        item_id = parts[2]
    return item_id


def _parse_pagination(qs: Dict[str, str]) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """Extract `start` and `size` from query string; return (start, size, error)."""
    start = qs.get("start")
    size_str = qs.get("size")
    if size_str is None:
        return start, None, None
    try:
        size = int(size_str)
        return start, size, None
    except Exception:
        return start, None, "size must be an integer"


def _handle_get_item(resource: str, item_id: str) -> Dict[str, Any]:
    """Handle GET for single item; return API response."""
    item = get_one(resource, item_id)
    if not item:
        singular = {"foodbanks": "Foodbank", "programs": "Program", "sponsors": "Sponsor"}
        return not_found(f"{singular.get(resource, 'Item')} not found")
    return response(200, item)


def _handle_get_collection(resource: str, start: Optional[str], size: Optional[int]) -> Dict[str, Any]:
    """Handle GET for collection listing; return API response."""
    try:
        items, next_start = list_range(resource, start, size)
    except ValueError as ve:
        return bad_request(str(ve))
    payload: Dict[str, Any] = {"items": items}
    if next_start:
        payload["next_start"] = next_start
    return response(200, payload)


def _handle_get(method: str, parts: List[str], qs: Dict[str, str], path_params: Dict[str, str]) -> Dict[str, Any]:
    """Route GET requests to either item or collection handlers."""
    if method != "GET":
        res = response(405, {"error": "MethodNotAllowed", "message": "Only GET is allowed"})
        res["headers"]["Allow"] = "GET, OPTIONS"
        return res

    resource = _ensure_route(parts)
    if not resource:
        return not_found("Unknown route")
    if not _validate_resource(resource):
        return not_found("Unknown resource")

    # Ensure backing table exists (friendly 503 if missing)
    try:
        _ensure_table_or_error(resource)
    except RuntimeError as e:
        s = str(e)
        if s.startswith("__MISSING_TABLES__:"):
            missing = s.split(":", 1)[1].split(",")
            return _friendly_missing_tables_response(missing)
        logger.exception("Preflight table check failed")
        return server_error("Unexpected error")

    # ID or listing?
    item_id = _extract_item_id(parts, path_params)
    if item_id:
        return _handle_get_item(resource, item_id)

    start, size, err = _parse_pagination(qs)
    if err:
        return bad_request(err)
    return _handle_get_collection(resource, start, size)


# ------------------------------------------------------------------------------
# Lambda entrypoint
# ------------------------------------------------------------------------------
def lambda_handler(event, context):
    """
    AWS Lambda handler for API Gateway (HTTP API).
    Supports:
      - OPTIONS (CORS preflight)
      - GET /v1/<resource>[/<id>] with optional `start` and `size`
    """
    try:
        method = _method_from_event(event)
        raw_path = _raw_path_from_event(event)
        path_params = _path_params(event)
        qs = _query_params(event)
    except Exception:
        return bad_request("Malformed event")

    if _is_cors_preflight(method):
        return _cors_preflight_response()

    parts = _path_parts(raw_path)
    try:
        return _handle_get(method, parts, qs, path_params)
    except pg8000.dbapi.ProgrammingError as e:
        missing = _is_missing_relation_error(e)
        if missing is not None:
            # If we couldn't extract a concrete table, fall back to generic.
            return _friendly_missing_tables_response(missing or ["<unknown>"])
        logger.exception("DB programming error")
        return server_error("Unexpected error")
    except Exception:
        logger.exception("Unhandled error")
        return server_error("Unexpected error")
