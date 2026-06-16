import os
import base64
import httpx
from typing import Optional


VT_BASE = "https://www.virustotal.com/api/v3"


def is_available() -> bool:
    return bool(os.environ.get("VIRUSTOTAL_API_KEY", "").strip())


def _get_headers() -> dict:
    return {"x-apikey": os.environ.get("VIRUSTOTAL_API_KEY", "").strip()}


def _url_id(url: str) -> str:
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


def check_url(url: str) -> Optional[dict]:
    if not is_available():
        return None
    try:
        uid = _url_id(url)
        resp = httpx.get(
            f"{VT_BASE}/urls/{uid}",
            headers=_get_headers(),
            timeout=15,
        )
        if resp.status_code == 404:
            submit = httpx.post(
                f"{VT_BASE}/urls",
                headers=_get_headers(),
                data={"url": url},
                timeout=15,
            )
            if submit.status_code not in (200, 201):
                return {"error": "Não foi possível enviar ao VirusTotal."}
            analysis_id = submit.json().get("data", {}).get("id", "")
            analysis = httpx.get(
                f"{VT_BASE}/analyses/{analysis_id}",
                headers=_get_headers(),
                timeout=20,
            )
            data = analysis.json()
        else:
            data = resp.json()

        stats = (
            data.get("data", {})
            .get("attributes", {})
            .get("last_analysis_stats", {})
        )
        if not stats:
            stats = (
                data.get("data", {})
                .get("attributes", {})
                .get("stats", {})
            )

        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        harmless = stats.get("harmless", 0)
        undetected = stats.get("undetected", 0)
        total = malicious + suspicious + harmless + undetected

        if malicious > 0:
            verdict = "malicious"
        elif suspicious > 0:
            verdict = "suspicious"
        else:
            verdict = "clean"

        return {
            "verdict": verdict,
            "malicious": malicious,
            "suspicious": suspicious,
            "harmless": harmless,
            "undetected": undetected,
            "total": total,
            "url": f"https://www.virustotal.com/gui/url/{_url_id(url)}",
        }
    except Exception as e:
        return {"error": str(e)}
