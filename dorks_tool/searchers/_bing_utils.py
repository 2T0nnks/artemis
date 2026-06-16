"""Shared Bing cite-URL extraction logic."""
import re
from urllib.parse import urlparse


def bing_url_from_cite(cite_text: str, fallback: str) -> str:
    """
    Bing cite tags look like:
      'https://www.example.com'
      'https://example.com › wiki › Article'
    We want the clean URL: keep the base origin + first path chunk when no full
    URL is available, otherwise return the full https:// part.
    """
    text = cite_text.strip()
    if not text:
        return fallback

    # If it starts with http, the full URL is on the left of any ' › '
    if text.startswith("http"):
        # Take only the part before breadcrumb separators
        url_part = re.split(r"\s*›\s*", text)[0].rstrip("/")
        if url_part.startswith("http"):
            return url_part

    # Reconstruct from breadcrumbs: "example.com › path › sub"
    parts = re.split(r"\s*›\s*", text)
    if parts:
        domain = parts[0].strip()
        path = "/".join(p.strip() for p in parts[1:] if p.strip())
        url = f"https://{domain}"
        if path:
            url += "/" + path
        if urlparse(url).netloc:
            return url

    return fallback
