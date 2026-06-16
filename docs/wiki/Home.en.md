# Artemis — Wiki

**Precision search. Multiple engines. Tor support.**

[🇧🇷 Português](Home) · 🇺🇸 English · [🇪🇸 Español](Home.es)

---

## Table of Contents

- [Installation](#installation)
- [Available Engines](#available-engines)
- [Dork Builder](#dork-builder)
- [Tor — bypass & dark web](#tor--bypass--dark-web)
- [.onion Engines](#onion-engines)
- [Anti-block Layer](#anti-block-layer)
- [Exporting Results](#exporting-results)
- [VirusTotal](#virustotal)
- [CLI](#cli)

---

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
python artemis.py web         # → http://127.0.0.1:5000
```

**Environment variables** (`.env` file, all optional):

| Variable | Description |
|---|---|
| `VIRUSTOTAL_API_KEY` | URL safety scanning via VirusTotal |
| `BRAVE_API_KEY` | Brave Search via official API |
| `TOR_PROXY` | e.g. `socks5://127.0.0.1:9050` |

---

## Available Engines

### Surface Web

| Slug | Engine | Notes |
|---|---|---|
| `ddghtml` | DuckDuckGo HTML | Scraper, no API needed |
| `bing` | Bing | Scraper (en-US) |
| `google` | Bing Global | Scraper (en-GB) |
| `startpage` | Bing PT-BR | Scraper (pt-BR) |
| `ddg` | DuckDuckGo API | Via official library |
| `searx` | SearXNG | 7 public instances, shuffled order |
| `mojeek` | Mojeek | Independent index |
| `ecosia` | Ecosia | Eco-friendly engine |
| `brave_html` | Brave Search | HTML scraper |
| `brave` | Brave API | Requires `BRAVE_API_KEY` |

### .onion Network *(requires Tor active)*

| Slug | Engine | Description |
|---|---|---|
| `ahmia` | Ahmia | Most maintained dark web index |
| `torch` | Torch | Pioneer, large link volume |
| `haystack` | Haystack | Privacy-focused |

> .onion engines only appear in the UI when Tor is active. They cannot function without the Tor daemon running locally.

---

## Dork Builder

The Dork Builder automatically generates precise dorks based on the chosen category.

### Categories

| Category | Generated formats |
|---|---|
| Book | `pdf epub mobi djvu` |
| Manga | `cbz cbr pdf zip` |
| Movie | `mkv mp4 avi 1080p 720p 4k` |
| Music | `mp3 flac wav ogg aac` |
| Course | `pdf mp4 zip inurl:torrent` |
| Software | `exe zip iso dmg inurl:download inurl:release` |
| Free | free-form field, no modifications |

### Advanced Panel

- **Exclude sites** — e.g. `amazon.com, goodreads.com` → adds `-site:` to the dork
- **Extra operators** — e.g. `site:gov.br before:2024 intext:confidential` → appended to the dork
- **Formats** — individually toggleable chips per category
- **Colored preview** — each operator type gets a distinct color in real time:
  - 🟡 `intitle:` · 🟣 `inurl:` · 🔵 `site:` · 🟠 `intext:` · 🟤 `filetype:` · 🔴 `-site:` (exclusion) · 🟢 `"exact phrase"`

---

## Tor — bypass & dark web

Tor serves **two distinct purposes**:

### 1. Anti-scraping bypass
Routes normal engine requests (DDG, Bing etc.) through Tor → exit node with random IP → the target site never sees your real IP. Each circuit renewal changes the exit node.

```
httpx → SOCKS5 → Tor → exit node (random IP) → target site
```

### 2. .onion network search
`.onion` engines run inside the Tor network. Traffic never reaches the public internet.

```
httpx → SOCKS5 → Tor → relay → relay → .onion server
```

### Activate via CLI

```bash
python artemis.py tor install   # downloads official bundle
python artemis.py tor start     # starts in background
python artemis.py tor stop      # stops the process
```

### Activate via Web App

1. Click the **Tor** badge in the interface
2. Use the **⚙** panel for advanced control:
   - Renew circuit every N searches
   - Start/stop the daemon
   - Access .onion engines

---

## .onion Engines

When Tor is active, the **🧅 .onion Network** block appears in the ⚙ panel:

- **Individual pills** — activate Ahmia, Torch, and/or Haystack separately
- **Surface + Onion mode** — searches active normal engines + .onion engines in parallel
- **Only .onion mode** — disables all normal engines, uses only the selected .onion ones
- **Post-search filter** — `🧅 Only Onion` pill in the filter bar isolates `.onion` results

---

## Anti-block Layer

All requests pass through the protection layer in `http_client.py`:

- **User-Agent rotation** via `fake-useragent` (Chrome, Firefox, Edge, Safari)
- **Randomized headers** — `Accept-Language`, `DNT`, `Referer` varied per request
- **Exponential backoff retry** on 429 and 503 responses
- **Tor circuit renewal** every N searches (configurable)
- **Delay only on retries** — no wait on the first attempt

---

## Exporting Results

After a search, click **⬇ Export**:

- **JSON** — array of `{title, url, snippet, engine}` objects
- **CSV** — spreadsheet with the same columns

Export is handled entirely client-side (no additional server request).

---

## VirusTotal

If `VIRUSTOTAL_API_KEY` is configured, each result displays a safety badge. Click **Check** to query the full URL report via the VT API.

---

## CLI

```bash
# Simple search
python artemis.py search "dork here"

# Specific engines
python artemis.py search "inurl:login" --engines ddg,bing,searx

# With VirusTotal check
python artemis.py search "filetype:pdf confidential" --vt

# Result limit
python artemis.py search "intext:password" --max 30

# Manage Tor
python artemis.py tor install
python artemis.py tor start
python artemis.py tor stop
python artemis.py tor status
```
