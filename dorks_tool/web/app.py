import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

from ..search import run_search
from ..searchers.registry import ALL_SEARCHERS
from .. import virustotal
from ..inspector import inspect_url
from ..dork_builder import CATEGORIES, FORMATS_BY_CATEGORY, PLACEHOLDERS, build_dork
from ..http_client import get_status as antiblock_status, set_tor, detect_tor, tor_enabled
import dorks_tool.http_client as _hc
from .. import tor_setup


_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def create_app():
    app = Flask(
        __name__,
        static_folder=_STATIC_DIR,
        static_url_path="/static",
    )

    @app.route("/")
    def index():
        engines = [
            {"slug": s.slug, "name": s.name, "available": s.is_available()}
            for s in ALL_SEARCHERS
        ]
        vt_enabled = virustotal.is_available()
        return render_template(
            "index.html",
            engines=engines,
            vt_enabled=vt_enabled,
            categories=CATEGORIES,
            formats_by_category=FORMATS_BY_CATEGORY,
            placeholders=PLACEHOLDERS,
        )

    @app.route("/api/search", methods=["POST"])
    def api_search():
        data = request.get_json(force=True)
        query = (data.get("query") or "").strip()
        engine_slugs = data.get("engines") or None

        if not query:
            return jsonify({"error": "Query vazia."}), 400

        results, engine_counts = run_search(query, engine_slugs=engine_slugs, max_per_engine=15)
        return jsonify({
            "results": [
                {"title": r.title, "url": r.url, "snippet": r.snippet, "engine": r.engine}
                for r in results
            ],
            "engine_counts": engine_counts,
        })

    @app.route("/api/build-dork", methods=["POST"])
    def api_build_dork():
        data = request.get_json(force=True)
        category = (data.get("category") or "free").strip()
        title = (data.get("title") or "").strip()
        formats = data.get("formats") or None
        excludes = data.get("excludes") or None
        extra_operators = (data.get("extra_operators") or "").strip() or None

        dork = build_dork(category, title, formats=formats, excludes=excludes, extra_operators=extra_operators)
        return jsonify({"dork": dork})

    @app.route("/api/inspect", methods=["POST"])
    def api_inspect():
        data = request.get_json(force=True)
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify({"error": "URL vazia."}), 400
        result = inspect_url(url)
        return jsonify(result)

    @app.route("/api/status")
    def api_status():
        status = antiblock_status()
        status["tor_available"] = detect_tor() is not None
        return jsonify(status)

    @app.route("/api/tor", methods=["POST"])
    def api_tor():
        data = request.get_json(force=True)
        enabled = bool(data.get("enabled", False))
        result = set_tor(enabled)
        return jsonify(result)

    @app.route("/api/tor/install", methods=["POST"])
    def api_tor_install():
        ok, msg = tor_setup.download_tor()
        if ok:
            start_ok, start_msg = tor_setup.start_bundled_tor()
            if start_ok:
                set_tor(True)
            return jsonify({"ok": ok, "message": msg, "started": start_ok, "start_message": start_msg})
        return jsonify({"ok": False, "message": msg, "started": False, "start_message": None})

    @app.route("/api/tor/start", methods=["POST"])
    def api_tor_start():
        ok, msg = tor_setup.start_bundled_tor()
        if ok:
            set_tor(True)
        return jsonify({"ok": ok, "message": msg})

    @app.route("/api/tor/stop", methods=["POST"])
    def api_tor_stop():
        set_tor(False)
        ok, msg = tor_setup.stop_bundled_tor()
        return jsonify({"ok": ok, "message": msg})

    @app.route("/api/tor/status", methods=["GET"])
    def api_tor_status():
        s = tor_setup.get_status()
        s["tor_enabled"] = tor_enabled()
        s["renew_every"] = _hc._TOR_RENEW_EVERY
        return jsonify(s)

    @app.route("/api/tor/config", methods=["POST"])
    def api_tor_config():
        data = request.get_json(force=True)
        if "renew_every" in data:
            val = int(data["renew_every"])
            if 1 <= val <= 200:
                _hc._TOR_RENEW_EVERY = val
        return jsonify({"ok": True, "renew_every": _hc._TOR_RENEW_EVERY})

    @app.route("/api/virustotal", methods=["POST"])
    def api_vt():
        if not virustotal.is_available():
            return jsonify({"error": "VirusTotal não configurado."}), 403
        data = request.get_json(force=True)
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify({"error": "URL vazia."}), 400
        result = virustotal.check_url(url)
        return jsonify(result)

    return app
