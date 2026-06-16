import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

from ..search import run_search
from ..searchers import registry as _registry
from ..searchers.registry import ALL_SEARCHERS, ONION_SLUGS
from .. import virustotal
from ..inspector import inspect_url
from ..dork_builder import CATEGORIES, FORMATS_BY_CATEGORY, PLACEHOLDERS, build_dork
from ..http_client import get_status as antiblock_status, set_tor, detect_tor, tor_enabled
import dorks_tool.http_client as _hc
from .. import tor_setup
from .. import engine_manager
from ..searchers.registry import reload_custom_engines
from ..searchers.custom import CustomSearcher


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
            {"slug": s.slug, "name": s.name, "available": s.is_available(),
             "custom": isinstance(s, CustomSearcher)}
            for s in _registry.ALL_SEARCHERS
            if s.slug not in ONION_SLUGS
        ]
        onion_engines = [
            {"slug": s.slug, "name": s.name}
            for s in _registry.ALL_SEARCHERS
            if s.slug in ONION_SLUGS
        ]
        vt_enabled = virustotal.is_available()
        return render_template(
            "index.html",
            engines=engines,
            onion_engines=onion_engines,
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

    # ── Custom Engine CRUD ───────────────────────────────────────────────────

    @app.route("/api/engines/custom", methods=["GET"])
    def api_engines_list():
        configs = engine_manager.get_all_configs()
        return jsonify(configs)

    @app.route("/api/engines/custom", methods=["POST"])
    def api_engines_add():
        data = request.get_json(force=True)
        try:
            cfg = engine_manager.add_engine(data)
            reload_custom_engines()
            return jsonify({"ok": True, "engine": cfg}), 201
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.route("/api/engines/custom/<slug>", methods=["PUT"])
    def api_engines_update(slug):
        data = request.get_json(force=True)
        updated = engine_manager.update_engine(slug, data)
        if updated is None:
            return jsonify({"ok": False, "error": f"Engine '{slug}' not found."}), 404
        reload_custom_engines()
        return jsonify({"ok": True, "engine": updated})

    @app.route("/api/engines/custom/<slug>", methods=["DELETE"])
    def api_engines_delete(slug):
        removed = engine_manager.remove_engine(slug)
        if not removed:
            return jsonify({"ok": False, "error": f"Engine '{slug}' not found."}), 404
        reload_custom_engines()
        return jsonify({"ok": True})

    # ── Health check + Auto-fix ──────────────────────────────────────────────

    @app.route("/api/engines/healthcheck", methods=["POST"])
    def api_engines_healthcheck_all():
        data = request.get_json(force=True) or {}
        target_slug = data.get("slug")
        targets = [
            s for s in _registry.ALL_SEARCHERS
            if isinstance(s, CustomSearcher) and (target_slug is None or s.slug == target_slug)
        ]
        if not targets:
            return jsonify({"results": [], "message": "No custom engines found."})
        results = [engine_manager.run_health_check(s) for s in targets]
        reload_custom_engines()
        return jsonify({"results": results})

    @app.route("/api/engines/healthcheck/<slug>", methods=["POST"])
    def api_engines_autofix(slug):
        configs = engine_manager.get_all_configs()
        cfg = next((c for c in configs if c["slug"] == slug), None)
        if cfg is None:
            return jsonify({"ok": False, "error": f"Engine '{slug}' not found."}), 404
        updated = engine_manager.auto_fix_selectors(cfg)
        reload_custom_engines()
        return jsonify({"ok": True, "engine": updated})

    return app
