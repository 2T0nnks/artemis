```
    _         _                     _     
   / \   _ __| |_ ___ _ __ ___  (_)___
  / _ \ | '__| __/ _ \ '_ ` _ \ | / __|
 / ___ \| |  | ||  __/ | | | | || \__ \
/_/   \_\_|   \__\___|_| |_| |_|/ |___/
                               |__/     
```

<div align="center">

**Precision search. Multiple engines. Tor support.**

[![Python](https://img.shields.io/badge/Python-3.10+-7c3aed?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-7c3aed?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/license-MIT-a78bfa?style=flat-square)](LICENSE)

[🇧🇷 Português](../README.md) · 🇺🇸 English · [🇪🇸 Español](README.es.md) · [📖 Wiki](../../wiki)

</div>

---

![Artemis Web UI](artemis.jpeg)

---

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

## Configuration (optional)

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `VIRUSTOTAL_API_KEY` | URL safety scanning via VirusTotal |
| `BRAVE_API_KEY` | Brave Search via official API |
| `TOR_PROXY` | e.g. `socks5://127.0.0.1:9050` |

No keys needed — Artemis works out of the box with 10 free engines + unlimited custom engines via Engine Manager.

---

## Usage

### Web App

```bash
python artemis.py web
# → http://127.0.0.1:5000
```

### CLI

```bash
python artemis.py search "site:gov.br filetype:pdf"
python artemis.py search "inurl:login" --engines ddg,bing
python artemis.py search "intext:password" --vt --max 20
```

---

## Engines

### Surface Web
| Slug | Engine |
|---|---|
| `ddghtml` | DuckDuckGo HTML |
| `bing` | Bing |
| `google` | Bing Global (en-GB) |
| `startpage` | Bing (pt-BR) |
| `ddg` | DuckDuckGo API |
| `searx` | SearXNG (public instances, shuffled order) |
| `mojeek` | Mojeek |
| `ecosia` | Ecosia |
| `brave_html` | Brave Search (scraper) |
| `brave` | Brave API *(requires key)* |

### Tor Network .onion *(requires Tor active)*
| Slug | Engine | Description |
|---|---|---|
| `ahmia` | Ahmia | Most maintained dark web index |
| `torch` | Torch | Pioneer, large link volume |
| `haystack` | Haystack | Privacy-focused |

---

## Tor — bypass & dark web

```bash
python artemis.py tor install   # downloads official bundle into .tor/
python artemis.py tor start     # starts in background
python artemis.py tor stop      # stops the process
```

Or use the **⚙** panel next to the Tor badge in the web app for full control without CLI.

Tor serves **two purposes**:
- **Bypass** — IP rotation via exit nodes, avoids rate-limiting on normal engines
- **Dark web** — direct access to `.onion` engines (Ahmia, Torch, Haystack) via the Tor network

> Bundle downloaded directly from `archive.torproject.org`. Nothing is installed on your system.

---

## Features

- 🔍 **Multi-engine** — 10+ parallel engines with deduplication
- 🛡 **Anti-block** — UA rotation, randomized headers, retry with exponential backoff
- 🧅 **Tor dual-mode** — scraping bypass + dark web search (Ahmia, Torch, Haystack)
- 🔌 **Engine Manager** — add custom engines via UI panel, with health check and auto-selector detection
- 🌐 **Multilingual UI** — PT 🇧🇷 / EN 🇺🇸 / ES 🇪🇸
- 📋 **One-click copy URL** per result
- 🕒 **Search history** (localStorage, last 10)
- 🔽 **Export** results as JSON or CSV
- 🔎 **Filter by engine** after search (including exclusive 🧅 Onion filter)
- 🛡 **VirusTotal** inline check per result
- 🏹 **Dork builder** with extra operators (`site:`, `before:`, `after:`), color-coded preview
- 🎯 **Target sites** — extra operators field in advanced panel

---

## Engine Manager

Click the **🔌** button next to the Tor badge to open the custom engine panel.

- **Add engine** — provide URL, method, parameters, and CSS selectors
- **Auto-detect selectors** — Artemis fetches the page and infers working selectors automatically
- **Health check** — tests if the engine returns results (`ok` / `degraded` / `offline`)
- **Enable/Disable** — without removing the configuration
- **Persistence** — settings saved in `dorks_tool/engines.json`

---

<div align="center">
  <sub>By <strong>Tonnks</strong></sub>
</div>
