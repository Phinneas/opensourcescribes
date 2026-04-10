"""
db.py — SurrealDB integration for the OpenSourceScribes pipeline.

Schema:
  repo        — every GitHub repo ever seen, with full metadata and status
  discovery   — log of each discovery run (source, count, timestamp)
  run         — log of each video pipeline run

Connection URL (config.json → surrealdb.url):
  surrealkv://./opensourcescribes.db   local file, no auth needed
  ws://localhost:8000                  local server, auth required
  wss://....surreal.cloud/rpc          Surreal Cloud / Railway, auth required
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from surrealdb import Surreal

_CONFIG_PATH = Path(__file__).parent / "config.json"


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return json.load(f)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class DB:
    """
    Synchronous wrapper around SurrealDB for the pipeline.

    Usage:
        with DB() as db:
            db.mark_published("https://github.com/owner/repo", {...})
    """

    def __init__(self, config: Optional[dict] = None):
        cfg = config or _load_config()
        self._cfg      = cfg.get("surrealdb", {})
        self._url      = self._cfg.get("url", "surrealkv://./opensourcescribes.db")
        self._ns       = self._cfg.get("namespace", "opensourcescribes")
        self._dbname   = self._cfg.get("database", "pipeline")
        self._username = self._cfg.get("username")
        self._password = self._cfg.get("password")
        self._conn: Optional[Surreal] = None

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #
    def __enter__(self) -> "DB":
        self.connect()
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------ #
    # Connection
    # ------------------------------------------------------------------ #
    def connect(self):
        self._conn = Surreal(self._url)
        self._conn.connect()
        is_remote = self._url.startswith(("ws://", "wss://", "http://", "https://"))
        if is_remote and self._username and self._password:
            self._conn.signin({"username": self._username, "password": self._password})
        self._conn.use(self._ns, self._dbname)
        self._ensure_schema()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------ #
    # Schema bootstrap (idempotent — multi-statement queries return None)
    # ------------------------------------------------------------------ #
    def _ensure_schema(self):
        self._conn.query("""
            DEFINE TABLE IF NOT EXISTS repo SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS url            ON repo TYPE string;
            DEFINE FIELD IF NOT EXISTS name           ON repo TYPE string;
            DEFINE FIELD IF NOT EXISTS description    ON repo TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS stars          ON repo TYPE option<int>;
            DEFINE FIELD IF NOT EXISTS forks          ON repo TYPE option<int>;
            DEFINE FIELD IF NOT EXISTS language       ON repo TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS topics         ON repo TYPE option<array>;
            DEFINE FIELD IF NOT EXISTS status         ON repo TYPE string DEFAULT 'pending';
            DEFINE FIELD IF NOT EXISTS source         ON repo TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS discovered_at  ON repo TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS published_at   ON repo TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS skipped_reason ON repo TYPE option<string>;
            DEFINE INDEX IF NOT EXISTS repo_url_idx   ON repo FIELDS url UNIQUE;
        """)
        self._conn.query("""
            DEFINE TABLE IF NOT EXISTS discovery SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS started_at ON discovery TYPE string;
            DEFINE FIELD IF NOT EXISTS mode       ON discovery TYPE string;
            DEFINE FIELD IF NOT EXISTS found      ON discovery TYPE int;
            DEFINE FIELD IF NOT EXISTS new_repos  ON discovery TYPE int;
            DEFINE FIELD IF NOT EXISTS duplicates ON discovery TYPE int;
        """)
        self._conn.query("""
            DEFINE TABLE IF NOT EXISTS run SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS started_at    ON run TYPE string;
            DEFINE FIELD IF NOT EXISTS completed_at  ON run TYPE option<string>;
            DEFINE FIELD IF NOT EXISTS repos_count   ON run TYPE int DEFAULT 0;
            DEFINE FIELD IF NOT EXISTS success_count ON run TYPE int DEFAULT 0;
            DEFINE FIELD IF NOT EXISTS error_count   ON run TYPE int DEFAULT 0;
            DEFINE FIELD IF NOT EXISTS output_path   ON run TYPE option<string>;
        """)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _rows(self, res) -> list:
        """query() returns a flat list of records, or None for DDL."""
        return res if isinstance(res, list) else []

    # ------------------------------------------------------------------ #
    # Repo operations
    # ------------------------------------------------------------------ #
    def is_published(self, github_url: str) -> bool:
        url = github_url.rstrip("/")
        rows = self._rows(self._conn.query(
            "SELECT id FROM repo WHERE url = $url AND status = 'published' LIMIT 1",
            {"url": url},
        ))
        return len(rows) > 0

    def is_seen(self, github_url: str) -> bool:
        url = github_url.rstrip("/")
        rows = self._rows(self._conn.query(
            "SELECT id FROM repo WHERE url = $url LIMIT 1",
            {"url": url},
        ))
        return len(rows) > 0

    def upsert_repo(
        self,
        github_url: str,
        name: str,
        *,
        description: Optional[str] = None,
        stars: Optional[int] = None,
        forks: Optional[int] = None,
        language: Optional[str] = None,
        topics: Optional[list] = None,
        status: str = "pending",
        source: Optional[str] = None,
    ) -> str:
        url = github_url.rstrip("/")
        now = _utcnow()

        existing = self._rows(self._conn.query(
            "SELECT id FROM repo WHERE url = $url LIMIT 1",
            {"url": url},
        ))

        if existing:
            rec_id = existing[0]["id"]
            self._conn.query(
                """
                UPDATE $id SET
                    name        = $name,
                    description = $desc,
                    stars       = $stars,
                    forks       = $forks,
                    language    = $lang,
                    topics      = $topics,
                    status      = $status,
                    source      = $source
                """,
                {
                    "id": rec_id, "name": name, "desc": description,
                    "stars": stars, "forks": forks, "lang": language,
                    "topics": topics or [], "status": status, "source": source,
                },
            )
            return str(rec_id)
        else:
            rows = self._rows(self._conn.query(
                """
                CREATE repo SET
                    url           = $url,
                    name          = $name,
                    description   = $desc,
                    stars         = $stars,
                    forks         = $forks,
                    language      = $lang,
                    topics        = $topics,
                    status        = $status,
                    source        = $source,
                    discovered_at = $now
                """,
                {
                    "url": url, "name": name, "desc": description,
                    "stars": stars, "forks": forks, "lang": language,
                    "topics": topics or [], "status": status,
                    "source": source, "now": now,
                },
            ))
            return str(rows[0]["id"]) if rows else ""

    def mark_published(self, github_url: str, metadata: Optional[dict] = None):
        url = github_url.rstrip("/")
        now = _utcnow()
        meta = metadata or {}

        existing = self._rows(self._conn.query(
            "SELECT id FROM repo WHERE url = $url LIMIT 1",
            {"url": url},
        ))

        if existing:
            self._conn.query(
                "UPDATE $id SET status = 'published', published_at = $now",
                {"id": existing[0]["id"], "now": now},
            )
        else:
            name = meta.get("name") or url.rstrip("/").split("/")[-1]
            self.upsert_repo(
                url, name,
                description=meta.get("description"),
                stars=meta.get("stars"),
                forks=meta.get("forks"),
                language=meta.get("language"),
                topics=meta.get("topics"),
                status="published",
            )
            self._conn.query(
                "UPDATE repo SET published_at = $now WHERE url = $url",
                {"url": url, "now": now},
            )

    def mark_skipped(self, github_url: str, reason: str = ""):
        url = github_url.rstrip("/")
        self._conn.query(
            "UPDATE repo SET status = 'skipped', skipped_reason = $reason WHERE url = $url",
            {"url": url, "reason": reason},
        )

    def get_published_urls(self) -> set:
        rows = self._rows(self._conn.query(
            "SELECT url FROM repo WHERE status = 'published'"
        ))
        return {r["url"].rstrip("/") for r in rows}

    def get_pending_repos(self, limit: int = 15) -> list:
        return self._rows(self._conn.query(
            "SELECT * FROM repo WHERE status = 'pending' ORDER BY stars DESC LIMIT $limit",
            {"limit": limit},
        ))

    def update_stats(self, github_url: str, stars: int, forks: int):
        """Refresh live star/fork counts after a GitHub API call."""
        url = github_url.rstrip("/")
        self._conn.query(
            "UPDATE repo SET stars = $stars, forks = $forks WHERE url = $url",
            {"url": url, "stars": stars, "forks": forks},
        )

    # ------------------------------------------------------------------ #
    # Discovery log
    # ------------------------------------------------------------------ #
    def log_discovery(self, mode: str, found: int, new_repos: int, duplicates: int) -> str:
        rows = self._rows(self._conn.query(
            """
            CREATE discovery SET
                started_at = $now,
                mode       = $mode,
                found      = $found,
                new_repos  = $new_repos,
                duplicates = $duplicates
            """,
            {"now": _utcnow(), "mode": mode, "found": found,
             "new_repos": new_repos, "duplicates": duplicates},
        ))
        return str(rows[0]["id"]) if rows else ""

    # ------------------------------------------------------------------ #
    # Pipeline run log
    # ------------------------------------------------------------------ #
    def start_run(self) -> str:
        rows = self._rows(self._conn.query(
            "CREATE run SET started_at = $now, repos_count = 0, success_count = 0, error_count = 0",
            {"now": _utcnow()},
        ))
        return str(rows[0]["id"]) if rows else ""

    def finish_run(
        self,
        run_id: str,
        repos_count: int,
        success_count: int,
        error_count: int,
        output_path: Optional[str] = None,
    ):
        self._conn.query(
            """
            UPDATE $id SET
                completed_at  = $now,
                repos_count   = $repos_count,
                success_count = $success_count,
                error_count   = $error_count,
                output_path   = $output_path
            """,
            {
                "id": run_id, "now": _utcnow(),
                "repos_count": repos_count, "success_count": success_count,
                "error_count": error_count, "output_path": output_path,
            },
        )

    # ------------------------------------------------------------------ #
    # One-time migration from flat files
    # ------------------------------------------------------------------ #
    def import_published_txt(self, txt_path: str) -> int:
        """Import published_repos.txt into SurrealDB. Returns inserted count."""
        path = Path(txt_path)
        if not path.exists():
            return 0
        count = 0
        now = _utcnow()
        with open(path) as f:
            for line in f:
                url = line.strip()
                if not url or not url.startswith("http"):
                    continue
                if not self.is_seen(url):
                    name = url.rstrip("/").split("/")[-1]
                    self._conn.query(
                        """
                        CREATE repo SET
                            url           = $url,
                            name          = $name,
                            status        = 'published',
                            source        = 'migration',
                            discovered_at = $now,
                            published_at  = $now
                        """,
                        {"url": url, "name": name, "now": now},
                    )
                    count += 1
        return count

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #
    def stats(self) -> dict:
        rows = self._rows(self._conn.query("""
            SELECT
                count()                         AS total,
                count(status = 'published')     AS published,
                count(status = 'pending')       AS pending,
                count(status = 'skipped')       AS skipped
            FROM repo GROUP ALL
        """))
        return rows[0] if rows else {}
