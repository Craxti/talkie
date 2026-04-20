"""Request history: JSON file (default) or SQLite, with atomic writes and redaction."""

from __future__ import annotations

import csv
import json
import logging
import os
import sqlite3
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

logger = logging.getLogger("talkie.history")

SortOrder = Literal["asc", "desc"]


class HistoryIOError(OSError):
    """Raised when history cannot be read or written."""


def _atomic_write_json(path: Path, data: List[Dict[str, Any]]) -> None:
    """Write JSON atomically to avoid corrupt history on crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        suffix=".tmp", prefix="talkie_history_", dir=str(path.parent)
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        tmp_path.replace(path)
    except OSError as exc:
        logger.warning("Failed to write history file %s: %s", path, exc)
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise HistoryIOError(f"Cannot write history to {path}") from exc


_SENSITIVE_HEADER_NAMES = frozenset(
    (
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-access-token",
        "proxy-authorization",
    )
)
_SENSITIVE_KEY_SUBSTRINGS = ("password", "secret", "token", "api_key", "apikey", "authorization")


def _redact_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    if not headers:
        return {}
    out: Dict[str, str] = {}
    for k, v in headers.items():
        if k.lower() in _SENSITIVE_HEADER_NAMES or any(
            s in k.lower() for s in ("secret", "token", "password", "api-key", "apikey")
        ):
            out[k] = "***"
        else:
            out[k] = v
    return out


def _redact_value(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _redact_value(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_value(i) for i in obj]
    if isinstance(obj, str) and len(obj) > 200:
        return obj[:200] + "…"
    return obj


def _redact_body_data(data: Any) -> Any:
    """Mask nested dict keys that look like secrets (for JSON bodies)."""
    if not isinstance(data, dict):
        return data
    redacted: Dict[str, Any] = {}
    for key, val in data.items():
        lk = str(key).lower()
        if any(s in lk for s in _SENSITIVE_KEY_SUBSTRINGS):
            redacted[key] = "***"
        elif isinstance(val, (dict, list)):
            redacted[key] = _redact_value(val)
        else:
            redacted[key] = val
    return redacted


@dataclass
class RequestData:
    """Request information stored in history."""

    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    data: Optional[Any] = None
    response_status: Optional[int] = None
    response_time: Optional[float] = None


class HistoryManager:
    """Stores HTTP request history in JSON or SQLite."""

    def __init__(self, history_file: Optional[str] = None) -> None:
        backend = os.environ.get("TALKIE_HISTORY_BACKEND", "json").lower().strip()
        self._sqlite = backend == "sqlite"
        env_path = os.environ.get("TALKIE_HISTORY_FILE")
        if history_file:
            self.history_file = Path(history_file)
        elif env_path:
            self.history_file = Path(env_path)
        else:
            base = Path.home() / ".talkie"
            base.mkdir(exist_ok=True)
            self.history_file = (
                base / "history.sqlite" if self._sqlite else base / "history.json"
            )

        self.history: List[Dict[str, Any]] = []
        self._conn: Optional[sqlite3.Connection] = None
        if self._sqlite:
            self._conn = sqlite3.connect(str(self.history_file))
            self._conn.row_factory = sqlite3.Row
            self._init_sqlite()
        else:
            self.load_history()

    def _init_sqlite(self) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers TEXT,
                data TEXT,
                response_status INTEGER,
                response_time REAL
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_requests_ts ON requests(timestamp)"
        )
        self._conn.commit()

    def load_history(self) -> None:
        """Load history from file (JSON backend only)."""
        if self._sqlite:
            return
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                if not isinstance(self.history, list):
                    self.history = []
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load history %s: %s", self.history_file, exc)
                self.history = []
        else:
            self.history = []

    def save_history(self) -> None:
        """Persist history (JSON backend)."""
        if self._sqlite:
            return
        try:
            _atomic_write_json(self.history_file, self.history)
        except HistoryIOError:
            raise

    def add_request(self, request_data: RequestData) -> None:
        """Append one request (redacted)."""
        entry_id = str(uuid.uuid4())
        headers = _redact_headers(request_data.headers)
        data = request_data.data
        if isinstance(data, dict):
            data = _redact_body_data(data)

        entry: Dict[str, Any] = {
            "id": entry_id,
            "timestamp": datetime.now().isoformat(),
            "method": request_data.method,
            "url": request_data.url,
            "headers": headers,
            "data": data,
            "response_status": request_data.response_status,
            "response_time": request_data.response_time,
        }

        if self._sqlite:
            assert self._conn is not None
            self._conn.execute(
                """
                INSERT INTO requests (id, timestamp, method, url, headers, data, response_status, response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    entry["timestamp"],
                    entry["method"],
                    entry["url"],
                    json.dumps(entry["headers"], ensure_ascii=False),
                    json.dumps(entry["data"], ensure_ascii=False)
                    if entry["data"] is not None
                    else None,
                    entry["response_status"],
                    entry["response_time"],
                ),
            )
            self._conn.commit()
            self._trim_sqlite_if_needed()
            return

        self.history.append(entry)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        try:
            self.save_history()
        except HistoryIOError:
            logger.error("History not saved after add_request")

    def _trim_sqlite_if_needed(self) -> None:
        assert self._conn is not None
        c = self._conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        if c <= 1000:
            return
        excess = c - 1000
        self._conn.execute(
            """
            DELETE FROM requests WHERE id IN (
                SELECT id FROM requests ORDER BY timestamp ASC LIMIT ?
            )
            """,
            (excess,),
        )
        self._conn.commit()

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Recent entries (newest last for JSON list; for CLI we return chronological)."""
        if self._sqlite:
            assert self._conn is not None
            q = "SELECT * FROM requests ORDER BY timestamp ASC"
            rows = self._conn.execute(q).fetchall()
            out = [_row_to_entry(r) for r in rows]
            if limit:
                return out[-limit:]
            return out

        if limit:
            return self.history[-limit :]
        return list(self.history)

    def get_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        if self._sqlite:
            assert self._conn is not None
            row = self._conn.execute(
                "SELECT * FROM requests WHERE id = ?", (entry_id,)
            ).fetchone()
            return _row_to_entry(row) if row else None
        for e in reversed(self.history):
            if e.get("id") == entry_id:
                return dict(e)
        return None

    def search_history(
        self,
        method: Optional[str] = None,
        url_pattern: Optional[str] = None,
        status_code: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        status_min: Optional[int] = None,
        status_max: Optional[int] = None,
        domain: Optional[str] = None,
        sort: SortOrder = "asc",
    ) -> List[Dict[str, Any]]:
        """Filter history; timestamps ISO8601 strings optional."""
        if self._sqlite:
            return self._search_sqlite(
                method,
                url_pattern,
                status_code,
                since,
                until,
                status_min,
                status_max,
                domain,
                sort,
            )

        results: List[Dict[str, Any]] = []
        for entry in self.history:
            if not _entry_matches(
                entry,
                method,
                url_pattern,
                status_code,
                since,
                until,
                status_min,
                status_max,
                domain,
            ):
                continue
            results.append(entry)

        reverse = sort == "desc"
        results.sort(key=lambda e: e.get("timestamp") or "", reverse=reverse)
        return results

    def _search_sqlite(
        self,
        method: Optional[str],
        url_pattern: Optional[str],
        status_code: Optional[int],
        since: Optional[str],
        until: Optional[str],
        status_min: Optional[int],
        status_max: Optional[int],
        domain: Optional[str],
        sort: SortOrder,
    ) -> List[Dict[str, Any]]:
        assert self._conn is not None
        clauses: List[str] = []
        params: List[Any] = []
        if method:
            clauses.append("method = ?")
            params.append(method.upper())
        if url_pattern:
            clauses.append("url LIKE ?")
            params.append(f"%{url_pattern}%")
        if status_code is not None:
            clauses.append("response_status = ?")
            params.append(status_code)
        if since:
            clauses.append("timestamp >= ?")
            params.append(since)
        if until:
            clauses.append("timestamp <= ?")
            params.append(until)
        if status_min is not None:
            clauses.append("response_status >= ?")
            params.append(status_min)
        if status_max is not None:
            clauses.append("response_status <= ?")
            params.append(status_max)
        if domain:
            clauses.append("url LIKE ?")
            params.append(f"%{domain}%")

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        order = "DESC" if sort == "desc" else "ASC"
        q = f"SELECT * FROM requests{where} ORDER BY timestamp {order}"
        rows = self._conn.execute(q, params).fetchall()
        return [_row_to_entry(r) for r in rows]

    def clear_history(self) -> None:
        if self._sqlite:
            assert self._conn is not None
            self._conn.execute("DELETE FROM requests")
            self._conn.commit()
            return
        self.history = []
        try:
            self.save_history()
        except HistoryIOError as exc:
            logger.error("clear_history save failed: %s", exc)

    def export_history(self, output_file: str, export_format: str = "json") -> None:
        data = self.get_history()
        if export_format == "json":
            _atomic_write_json(Path(output_file), data)
        elif export_format == "csv":
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", newline="", encoding="utf-8") as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

    def import_history(self, input_file: str) -> int:
        """Merge entries from JSON file. Returns count imported."""
        with open(input_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError("Import file must contain a JSON array")
        n = 0
        for item in raw:
            if not isinstance(item, dict):
                continue
            if self._sqlite:
                assert self._conn is not None
                eid = item.get("id") or str(uuid.uuid4())
                self._conn.execute(
                    """
                    INSERT OR REPLACE INTO requests
                    (id, timestamp, method, url, headers, data, response_status, response_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eid,
                        item.get("timestamp", datetime.now().isoformat()),
                        item.get("method", "GET"),
                        item.get("url", ""),
                        json.dumps(item.get("headers") or {}),
                        json.dumps(item.get("data"))
                        if item.get("data") is not None
                        else None,
                        item.get("response_status"),
                        item.get("response_time"),
                    ),
                )
                n += 1
            else:
                self.history.append(item)
                n += 1
        if self._sqlite:
            assert self._conn is not None
            self._conn.commit()
            self._trim_sqlite_if_needed()
        else:
            if len(self.history) > 1000:
                self.history = self.history[-1000:]
            self.save_history()
        return n

    def get_stats(self) -> Dict[str, Any]:
        hist = self.get_history()
        if not hist:
            return {}

        methods: Dict[str, int] = {}
        status_codes: Dict[int, int] = {}
        total_time = 0.0
        response_times: List[float] = []

        for entry in hist:
            method = entry.get("method", "UNKNOWN")
            methods[method] = methods.get(method, 0) + 1
            status = entry.get("response_status")
            if status is not None:
                status_codes[status] = status_codes.get(status, 0) + 1
            rt = entry.get("response_time")
            if rt is not None:
                response_times.append(float(rt))
                total_time += float(rt)

        avg = total_time / len(response_times) if response_times else 0.0
        return {
            "total_requests": len(hist),
            "methods": methods,
            "status_codes": status_codes,
            "average_response_time": avg,
            "fastest_response": min(response_times) if response_times else 0,
            "slowest_response": max(response_times) if response_times else 0,
        }

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


def _row_to_entry(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    if d.get("headers"):
        try:
            d["headers"] = json.loads(d["headers"])
        except json.JSONDecodeError:
            d["headers"] = {}
    if d.get("data"):
        try:
            d["data"] = json.loads(d["data"])
        except json.JSONDecodeError:
            pass
    return d


def _entry_matches(
    entry: Dict[str, Any],
    method: Optional[str],
    url_pattern: Optional[str],
    status_code: Optional[int],
    since: Optional[str],
    until: Optional[str],
    status_min: Optional[int],
    status_max: Optional[int],
    domain: Optional[str],
) -> bool:
    if method and entry.get("method") != method.upper():
        return False
    url = entry.get("url", "")
    if url_pattern and url_pattern not in url:
        return False
    if status_code is not None and entry.get("response_status") != status_code:
        return False
    ts = entry.get("timestamp") or ""
    if since and ts < since:
        return False
    if until and ts > until:
        return False
    st = entry.get("response_status")
    if status_min is not None and (st is None or st < status_min):
        return False
    if status_max is not None and (st is None or st > status_max):
        return False
    if domain:
        host = urlparse(url).netloc.lower()
        dom = domain.lower().lstrip("*.")
        if dom not in host and host != dom:
            return False
    return True


_HISTORY_MANAGER: Optional[HistoryManager] = None


def reset_history_manager() -> None:
    """Reset singleton (tests)."""
    global _HISTORY_MANAGER
    if _HISTORY_MANAGER is not None:
        _HISTORY_MANAGER.close()
    _HISTORY_MANAGER = None


def get_history_manager() -> HistoryManager:
    global _HISTORY_MANAGER
    if _HISTORY_MANAGER is None:
        _HISTORY_MANAGER = HistoryManager(None)
    return _HISTORY_MANAGER


def add_to_history(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    response_status: Optional[int] = None,
    response_time: Optional[float] = None,
) -> None:
    manager = get_history_manager()
    request_data = RequestData(
        method=method,
        url=url,
        headers=headers,
        data=data,
        response_status=response_status,
        response_time=response_time,
    )
    manager.add_request(request_data)


def get_recent_requests(limit: int = 10) -> List[Dict[str, Any]]:
    manager = get_history_manager()
    return manager.get_history(limit)


def search_requests(
    method: Optional[str] = None,
    url_pattern: Optional[str] = None,
    status_code: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    status_min: Optional[int] = None,
    status_max: Optional[int] = None,
    domain: Optional[str] = None,
    sort: SortOrder = "asc",
) -> List[Dict[str, Any]]:
    manager = get_history_manager()
    return manager.search_history(
        method=method,
        url_pattern=url_pattern,
        status_code=status_code,
        since=since,
        until=until,
        status_min=status_min,
        status_max=status_max,
        domain=domain,
        sort=sort,
    )
