"""
Caching layer — Redis-backed, cache-aside pattern.

TTL tiers
─────────
  LIVE_TTL      60 s   – live match scores
  UPCOMING_TTL  300 s  – upcoming fixtures (5 min)
  CURR_TTL      3 600 s – current-season data (1 h; changes each gameweek)
  PLAYER_TTL    604 800 s – player profiles / FPL stats (1 week)
  HIST_TTL      15 552 000 s – completed past-season data (180 days, sliding)

Sliding expiration
──────────────────
  Historical keys reset their TTL on every access so that frequently-requested
  data is never evicted while data untouched for 6 months is automatically
  removed — satisfying "evict if not requested in 6 months".

Optimal N
─────────
  Redis is configured with  maxmemory 256 mb + allkeys-lru  so the LRU
  eviction policy naturally keeps the N most-recently-used entries that fit
  in memory — no explicit cap needed.  For this dataset (≈10 seasons, ≈600
  players, ≈3 800 matches) the entire history fits comfortably in 256 MB.
"""

import json
from typing import Any, Optional
import redis
from pydantic import BaseModel
from app.config import settings

# ── TTL constants (seconds) ───────────────────────────────────────────────────
LIVE_TTL      = 60
UPCOMING_TTL  = 300
CURR_TTL      = 3_600
PLAYER_TTL    = 604_800
HIST_TTL      = 15_552_000           # 180 days

_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


# ── Low-level primitives ──────────────────────────────────────────────────────

def _serialize(value: Any) -> Any:
    """Convert Pydantic models / nested structures to JSON-safe dicts."""
    if isinstance(value, BaseModel):
        return json.loads(value.json())   # .json() handles date → ISO string
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def get_cached(key: str, sliding_ttl: Optional[int] = None) -> Optional[Any]:
    """
    Return the cached value for *key*, or None on a miss.

    When *sliding_ttl* is given the key's TTL is reset on every hit,
    implementing "evict if not accessed for N seconds".
    """
    try:
        r = get_redis()
        raw = r.get(key)
        if raw is None:
            return None
        if sliding_ttl:
            r.expire(key, sliding_ttl)    # reset the clock on access
        return json.loads(raw)
    except Exception:
        return None


def set_cached(key: str, value: Any, ttl: int) -> None:
    try:
        payload = json.dumps(_serialize(value), default=str)
        get_redis().setex(key, ttl, payload)
    except Exception:
        pass


def delete_cached(key: str) -> None:
    try:
        get_redis().delete(key)
    except Exception:
        pass


# ── Cache-aside helper ────────────────────────────────────────────────────────

def get_or_fetch(
    key: str,
    fetch_fn,
    ttl: int,
    sliding: bool = False,
) -> Optional[Any]:
    """
    Cache-aside: Redis → fetch_fn() → Redis.

    If *sliding* is True the TTL is reset on every cache hit (historical data).
    fetch_fn must return a JSON-serialisable value (dict, list, Pydantic model).
    Returns None only if both the cache and fetch_fn return nothing.
    """
    cached = get_cached(key, sliding_ttl=ttl if sliding else None)
    if cached is not None:
        return cached
    value = fetch_fn()
    if value is not None:
        set_cached(key, value, ttl=ttl)
    return value


# ── Season-tier helper ────────────────────────────────────────────────────────

def season_ttl(season_id: int, current_season_id: int) -> tuple[int, bool]:
    """
    Return (ttl, sliding) for a given season_id.

    Past seasons → HIST_TTL with sliding expiration.
    Current season → CURR_TTL with fixed expiration (data changes weekly).
    """
    if season_id < current_season_id:
        return HIST_TTL, True
    return CURR_TTL, False


def get_current_season_id(db) -> int:
    """
    Return the ID of the latest season, cached for 1 hour.
    Avoids a DB round-trip on every request.
    """
    meta_key = "meta:current_season_id"
    cached = get_cached(meta_key)
    if cached is not None:
        return int(cached)
    from app.models import Season
    season = db.query(Season).order_by(Season.id.desc()).first()
    sid = season.id if season else 0
    set_cached(meta_key, sid, ttl=CURR_TTL)
    return sid
