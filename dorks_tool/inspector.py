from urllib.parse import urlparse
from .http_client import get_client

TRUSTED_DOMAINS = {
    "archive.org", "wikipedia.org", "wikimedia.org", "github.com",
    "gitlab.com", "sourceforge.net", "gutenberg.org", "openlibrary.org",
    "libgen.is", "libgen.rs", "z-lib.org", "zlibrary.to",
    "mangadex.org", "readmanga.live", "fanfox.net",
    "nyaa.si", "1337x.to", "rarbg.to",
    "google.com", "drive.google.com", "docs.google.com",
    "dropbox.com", "mega.nz", "mediafire.com",
    "stackoverflow.com", "reddit.com",
}

SUSPICIOUS_TLDS = {".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".click", ".loan", ".win"}



def _format_size(content_length: str) -> str:
    try:
        n = int(content_length)
        if n < 1024:
            return f"{n} B"
        elif n < 1024 ** 2:
            return f"{n / 1024:.1f} KB"
        elif n < 1024 ** 3:
            return f"{n / 1024 ** 2:.1f} MB"
        else:
            return f"{n / 1024 ** 3:.1f} GB"
    except Exception:
        return None


def _safety_badge(parsed, https: bool, status: int) -> str:
    domain = parsed.netloc.lower().lstrip("www.")
    root = ".".join(domain.split(".")[-2:]) if domain.count(".") >= 1 else domain
    tld = "." + domain.rsplit(".", 1)[-1] if "." in domain else ""

    if not https:
        return "warning"
    if tld in SUSPICIOUS_TLDS:
        return "warning"
    if status >= 400:
        return "error"
    if root in TRUSTED_DOMAINS or domain in TRUSTED_DOMAINS:
        return "trusted"
    return "neutral"


def inspect_url(url: str) -> dict:
    try:
        parsed = urlparse(url)
        https = parsed.scheme == "https"
        domain = parsed.netloc.lstrip("www.")
        favicon = f"https://www.google.com/s2/favicons?sz=32&domain={parsed.netloc}"

        try:
            with get_client(timeout=6) as client:
                resp = client.head(url)
            status = resp.status_code
            content_type = resp.headers.get("content-type", "").split(";")[0].strip()
            content_length = resp.headers.get("content-length", "")
            final_url = str(resp.url)
            reachable = True
        except Exception:
            status = None
            content_type = None
            content_length = ""
            final_url = url
            reachable = False

        size = _format_size(content_length) if content_length else None

        file_type = None
        if content_type:
            ct_map = {
                "application/pdf": "PDF",
                "application/zip": "ZIP",
                "application/x-rar-compressed": "RAR",
                "application/x-rar": "RAR",
                "application/epub+zip": "EPUB",
                "application/octet-stream": "Arquivo binário",
                "text/html": "Página web",
                "video/mp4": "MP4",
                "video/x-matroska": "MKV",
                "audio/mpeg": "MP3",
                "audio/flac": "FLAC",
                "image/jpeg": "Imagem JPEG",
                "image/png": "Imagem PNG",
                "application/x-bittorrent": "Torrent",
            }
            file_type = ct_map.get(content_type, content_type or None)

        safety = _safety_badge(parsed, https, status or 0)

        redirected = final_url != url and final_url.rstrip("/") != url.rstrip("/")

        return {
            "reachable": reachable,
            "status": status,
            "https": https,
            "domain": domain,
            "favicon": favicon,
            "content_type": content_type,
            "file_type": file_type,
            "size": size,
            "safety": safety,
            "redirected": redirected,
            "final_url": final_url if redirected else None,
        }

    except Exception as e:
        return {"error": str(e), "reachable": False}
