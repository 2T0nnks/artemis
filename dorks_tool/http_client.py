"""
Central HTTP client factory for Artemis scrapers.

Features:
- Automatic User-Agent rotation (via fake-useragent with static fallback pool)
- Randomised realistic headers per request
- Random delay between requests (0.5–2.5 s) to avoid rate-limiting
- Automatic retry with exponential backoff on 429 / 503
- Optional Tor routing via TOR_PROXY env var (socks5://127.0.0.1:9050)
- Optional Tor circuit renewal via `stem` library (if installed)
"""

import os
import time
import random
import logging
import threading
from contextlib import contextmanager
from typing import Optional

import httpx
from .config import TOR_PORTS, TOR_RENEW_EVERY_DEFAULT, REQUEST_MIN_DELAY, REQUEST_MAX_DELAY, REQUEST_MAX_RETRIES, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# ── Static UA fallback pool (used when fake-useragent is unavailable) ──────
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
]

# ── fake-useragent integration (graceful degradation) ──────────────────────
_fua = None
try:
    from fake_useragent import UserAgent
    _fua = UserAgent(browsers=["chrome", "firefox", "edge", "safari"], os=["windows", "macos", "linux"])
except Exception:
    pass


def random_ua() -> str:
    if _fua:
        try:
            return _fua.random
        except Exception:
            pass
    return random.choice(_UA_POOL)


# ── Accept-Language variants ────────────────────────────────────────────────
_ACCEPT_LANGS = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.5",
    "en-US,en;q=0.8,pt;q=0.5",
]

# ── Tor state ───────────────────────────────────────────────────────────────
_tor_proxy: Optional[str] = os.getenv("TOR_PROXY", "").strip() or None
_request_count: int = 0
_TOR_RENEW_EVERY: int = TOR_RENEW_EVERY_DEFAULT
_state_lock = threading.Lock()

# Known Tor SOCKS ports to probe
_TOR_PORTS = TOR_PORTS


def detect_tor() -> Optional[str]:
    """Probe known Tor SOCKS ports and return the first responsive one, or None."""
    import socket  # noqa: PLC0415
    for port in _TOR_PORTS:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return f"socks5://127.0.0.1:{port}"
        except OSError:
            pass
    return None


def set_tor(enabled: bool) -> dict:
    """
    Enable or disable Tor routing at runtime.
    Returns a status dict: {"ok": bool, "tor_proxy": str|None, "error": str|None}
    """
    global _tor_proxy
    if enabled:
        proxy = detect_tor()
        if proxy:
            with _state_lock:
                _tor_proxy = proxy
            logger.info("Tor enabled: %s", proxy)
            return {"ok": True, "tor_proxy": proxy, "error": None}
        else:
            return {"ok": False, "tor_proxy": None,
                    "error": "Tor não encontrado. Inicie o Tor Browser ou o serviço tor."}
    else:
        with _state_lock:
            _tor_proxy = None
        logger.info("Tor disabled.")
        return {"ok": True, "tor_proxy": None, "error": None}


def _renew_tor_circuit() -> None:
    """Attempt to renew the Tor circuit via stem (no-op if stem unavailable)."""
    try:
        from stem import Signal
        from stem.control import Controller
        with Controller.from_port(port=9051) as ctrl:
            ctrl.authenticate()
            ctrl.signal(Signal.NEWNYM)
            logger.debug("Tor circuit renewed.")
    except Exception:
        pass  # stem not installed or Tor control port not available


def tor_enabled() -> bool:
    return bool(_tor_proxy)


# ── Client factory ──────────────────────────────────────────────────────────

def _build_transport() -> Optional[httpx.BaseTransport]:
    with _state_lock:
        proxy = _tor_proxy
    if not proxy:
        return None
    try:
        return httpx.SOCKSTransport(proxy=proxy)  # type: ignore[attr-defined]
    except AttributeError:
        return None


def _build_mounts() -> Optional[dict]:
    """Fallback for httpx versions that use mounts instead of transport."""
    with _state_lock:
        proxy = _tor_proxy
    if not proxy:
        return None
    try:
        httpx.SOCKSTransport  # noqa: B018
        return None  # transport approach works
    except AttributeError:
        return {"http://": httpx.HTTPTransport(proxy=proxy),
                "https://": httpx.HTTPTransport(proxy=proxy)}


def make_headers(extra: Optional[dict] = None) -> dict:
    """Return a randomised realistic header dict."""
    headers = {
        "User-Agent": random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice(_ACCEPT_LANGS),
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    if extra:
        headers.update(extra)
    return headers


@contextmanager
def get_client(extra_headers: Optional[dict] = None, timeout: int = 15):
    """
    Context manager that yields a configured httpx.Client.

    Usage::

        with get_client() as client:
            resp = client.get(url, params=params)
    """
    global _request_count

    headers = make_headers(extra_headers)
    transport = _build_transport()
    mounts = _build_mounts()

    kwargs: dict = {
        "headers": headers,
        "follow_redirects": True,
        "timeout": timeout,
    }
    if transport:
        kwargs["transport"] = transport
    elif mounts:
        kwargs["mounts"] = mounts

    with httpx.Client(**kwargs) as client:
        yield client


def request_with_retry(
    method: str,
    url: str,
    *,
    params: Optional[dict] = None,
    data: Optional[dict] = None,
    extra_headers: Optional[dict] = None,
    timeout: int = REQUEST_TIMEOUT,
    max_retries: int = REQUEST_MAX_RETRIES,
    min_delay: float = REQUEST_MIN_DELAY,
    max_delay: float = REQUEST_MAX_DELAY,
) -> Optional[httpx.Response]:
    """
    Make an HTTP request with:
    - Random pre-request delay
    - Automatic retry on 429 / 503 with exponential backoff
    - Tor circuit renewal when applicable
    """
    global _request_count

    for attempt in range(max_retries + 1):
        # Delay only on retries — no unnecessary wait on first attempt
        if attempt > 0:
            delay = random.uniform(min_delay, max_delay) * (2 ** attempt)
            time.sleep(delay)

        try:
            with get_client(extra_headers=extra_headers, timeout=timeout) as client:
                if method.upper() == "POST":
                    resp = client.post(url, data=data, params=params)
                else:
                    resp = client.get(url, params=params)

            with _state_lock:
                _request_count += 1
                count_snap = _request_count
                proxy_snap = _tor_proxy

            # Renew Tor circuit periodically
            if proxy_snap and count_snap % _TOR_RENEW_EVERY == 0:
                _renew_tor_circuit()

            if resp.status_code in (429, 503) and attempt < max_retries:
                logger.debug("Rate limited (%s), retry %d…", resp.status_code, attempt + 1)
                continue

            return resp

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.debug("Request error attempt %d: %s", attempt, exc)
            if attempt == max_retries:
                return None

    return None


def get_status() -> dict:
    """Return current anti-block status (useful for debug endpoint)."""
    with _state_lock:
        proxy = _tor_proxy
        count = _request_count
    masked = "socks5://127.0.0.1:****" if proxy else None
    return {
        "tor_enabled": tor_enabled(),
        "tor_proxy": masked,
        "ua_pool_size": len(_UA_POOL),
        "fake_useragent": _fua is not None,
        "request_count": count,
    }
