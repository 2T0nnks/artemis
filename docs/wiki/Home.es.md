# Artemis — Wiki

**Búsqueda precisa. Múltiples motores. Soporte para Tor.**

[🇧🇷 Português](Home) · [🇺🇸 English](Home.en) · 🇪🇸 Español

---

## Índice

- [Instalación](#instalación)
- [Motores disponibles](#motores-disponibles)
- [Constructor de dorks](#constructor-de-dorks)
- [Tor — bypass y dark web](#tor--bypass-y-dark-web)
- [Motores .onion](#motores-onion)
- [Capa anti-bloqueo](#capa-anti-bloqueo)
- [Exportar resultados](#exportar-resultados)
- [VirusTotal](#virustotal)
- [CLI](#cli)

---

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
python artemis.py web         # → http://127.0.0.1:5000
```

**Variables de entorno** (archivo `.env`, todas opcionales):

| Variable | Descripción |
|---|---|
| `VIRUSTOTAL_API_KEY` | Verificación de seguridad de URLs |
| `BRAVE_API_KEY` | Motor Brave Search vía API oficial |
| `TOR_PROXY` | Ej: `socks5://127.0.0.1:9050` |

---

## Motores disponibles

### Surface Web

| Slug | Motor | Notas |
|---|---|---|
| `ddghtml` | DuckDuckGo HTML | Scraper, sin API |
| `bing` | Bing | Scraper (en-US) |
| `google` | Bing Global | Scraper (en-GB) |
| `startpage` | Bing PT-BR | Scraper (pt-BR) |
| `ddg` | DuckDuckGo API | Vía biblioteca oficial |
| `searx` | SearXNG | 7 instancias públicas, orden aleatorio |
| `mojeek` | Mojeek | Índice independiente |
| `ecosia` | Ecosia | Motor ecológico |
| `brave_html` | Brave Search | Scraper HTML |
| `brave` | Brave API | Requiere `BRAVE_API_KEY` |

### Red .onion *(requiere Tor activo)*

| Slug | Motor | Descripción |
|---|---|---|
| `ahmia` | Ahmia | Índice más actualizado de la dark web |
| `torch` | Torch | Pionero, gran volumen de enlaces |
| `haystack` | Haystack | Enfocado en privacidad |

> Los motores .onion solo aparecen en la UI cuando Tor está activo. No funcionan sin el daemon de Tor corriendo localmente.

---

## Constructor de dorks

El Constructor de dorks genera dorks precisos automáticamente según la categoría elegida.

### Categorías

| Categoría | Formatos generados |
|---|---|
| Libro | `pdf epub mobi djvu` |
| Manga | `cbz cbr pdf zip` |
| Película | `mkv mp4 avi 1080p 720p 4k` |
| Música | `mp3 flac wav ogg aac` |
| Curso | `pdf mp4 zip inurl:torrent` |
| Software | `exe zip iso dmg inurl:download inurl:release` |
| Libre | campo libre, sin modificaciones |

### Panel avanzado

- **Excluir sitios** — ej: `amazon.com, goodreads.com` → añade `-site:` al dork
- **Operadores extra** — ej: `site:gov.br before:2024 intext:confidencial` → se concatena al final
- **Formatos** — chips activables individualmente por categoría
- **Preview coloreado** — cada tipo de operador tiene un color distinto en tiempo real:
  - 🟡 `intitle:` · 🟣 `inurl:` · 🔵 `site:` · 🟠 `intext:` · 🟤 `filetype:` · 🔴 `-site:` (exclusión) · 🟢 `"frase exacta"`

---

## Tor — bypass y dark web

Tor sirve para **dos propósitos distintos**:

### 1. Bypass anti-scraping
Enruta las peticiones de los motores normales (DDG, Bing etc.) por Tor → exit node con IP aleatoria → el sitio objetivo nunca ve tu IP real. Cada renovación de circuito cambia el exit node.

```
httpx → SOCKS5 → Tor → exit node (IP aleatoria) → sitio objetivo
```

### 2. Búsqueda en red .onion
Los motores `.onion` corren dentro de la red Tor. El tráfico nunca llega a la internet pública.

```
httpx → SOCKS5 → Tor → relay → relay → servidor .onion
```

### Activar vía CLI

```bash
python artemis.py tor install   # descarga el bundle oficial
python artemis.py tor start     # inicia en segundo plano
python artemis.py tor stop      # detiene el proceso
```

### Activar vía Web App

1. Haz clic en el badge **Tor** de la interfaz
2. Usa el panel **⚙** para control avanzado:
   - Renovar circuito cada N búsquedas
   - Iniciar/detener el daemon
   - Acceder a los motores .onion

---

## Motores .onion

Cuando Tor está activo, el bloque **🧅 Red .onion** aparece en el panel ⚙:

- **Pills individuales** — activa Ahmia, Torch y/o Haystack por separado
- **Modo Surface + Onion** — busca en los motores normales activos + motores .onion en paralelo
- **Modo Solo .onion** — desactiva todos los motores normales, usa solo los .onion seleccionados
- **Filtro post-búsqueda** — pill `🧅 Solo Onion` en la barra de filtros aísla resultados `.onion`

---

## Capa anti-bloqueo

Todas las peticiones pasan por la capa de protección en `http_client.py`:

- **Rotación de User-Agent** vía `fake-useragent` (Chrome, Firefox, Edge, Safari)
- **Headers aleatorios** — `Accept-Language`, `DNT`, `Referer` variados por petición
- **Reintento con backoff exponencial** en respuestas 429 y 503
- **Renovación de circuito Tor** cada N búsquedas (configurable)
- **Delay solo en reintentos** — sin espera en el primer intento

---

## Exportar resultados

Tras la búsqueda, haz clic en **⬇ Exportar**:

- **JSON** — array de objetos `{title, url, snippet, engine}`
- **CSV** — hoja de cálculo con las mismas columnas

La exportación se realiza completamente en el cliente (sin petición adicional al servidor).

---

## VirusTotal

Si `VIRUSTOTAL_API_KEY` está configurada, cada resultado muestra un badge de seguridad. Haz clic en **Verificar** para consultar el informe completo de la URL vía la API de VT.

---

## CLI

```bash
# Búsqueda simple
python artemis.py search "dork aquí"

# Motores específicos
python artemis.py search "inurl:login" --engines ddg,bing,searx

# Con verificación VirusTotal
python artemis.py search "filetype:pdf confidencial" --vt

# Límite de resultados
python artemis.py search "intext:password" --max 30

# Gestionar Tor
python artemis.py tor install
python artemis.py tor start
python artemis.py tor stop
python artemis.py tor status
```
