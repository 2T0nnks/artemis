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

![Artemis Web UI](screenshot.png)

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

No keys needed — Artemis works out of the box with 9 free engines.

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

| Slug | Engine |
|---|---|
| `ddghtml` | DuckDuckGo HTML |
| `bing` | Bing |
| `google` | Bing Global (en-GB) |
| `startpage` | Bing (pt-BR) |
| `ddg` | DuckDuckGo API |
| `searx` | SearXNG (public instances) |
| `mojeek` | Mojeek |
| `ecosia` | Ecosia |
| `brave` | Brave API *(requires key)* |

---

## Tor — IP rotation

```bash
python artemis.py tor install   # downloads official bundle into .tor/
python artemis.py tor start     # starts in background
python artemis.py tor stop      # stops the process
```

Or use the **⚙** panel next to the Tor badge in the web app for full control without CLI.

> Bundle downloaded directly from `archive.torproject.org`. Nothing is installed on your system.

---

## Features

- 🔍 **Multi-engine** — 9 parallel engines with deduplication
- 🛡 **Anti-block** — UA rotation, randomized headers, retry with exponential backoff
- 🧅 **Tor integration** — real-time toggle, automatic circuit renewal
- 📋 **One-click copy URL** per result
- 🕒 **Search history** (localStorage, last 10)
- 🔽 **Export** results as JSON or CSV
- 🔎 **Filter by engine** after search
- 🛡 **VirusTotal** inline check per result
- 🏹 **Dork builder** by category (book, movie, music, software...)

---

<div align="center">
  <sub>By <strong>Tonnks</strong></sub>
</div>
