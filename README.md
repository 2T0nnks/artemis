```
    _         _                     _     
   / \   _ __| |_ ___ _ __ ___  (_)___
  / _ \ | '__| __/ _ \ '_ ` _ \ | / __|
 / ___ \| |  | ||  __/ | | | | || \__ \
/_/   \_\_|   \__\___|_| |_| |_|/ |___/
                               |__/     
```

<div align="center">

**Busca precisa. Múltiplas engines. Suporte a Tor.**

[![Python](https://img.shields.io/badge/Python-3.10+-7c3aed?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-7c3aed?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/license-MIT-a78bfa?style=flat-square)](LICENSE)

🇧🇷 Português · [🇺🇸 English](docs/README.en.md) · [🇪🇸 Español](docs/README.es.md) · [📖 Wiki](../../wiki)

</div>

---

![Artemis Web UI](docs/artemis.jpeg)

---

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

## Configuração (opcional)

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

| Variável | Descrição |
|---|---|
| `VIRUSTOTAL_API_KEY` | Verificação de segurança de URLs |
| `BRAVE_API_KEY` | Engine Brave Search via API oficial |
| `TOR_PROXY` | Ex: `socks5://127.0.0.1:9050` |

Sem nenhuma chave, o Artemis já funciona com 10 engines gratuitas.

---

## Uso

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
| `searx` | SearXNG (instâncias públicas, ordem aleatória) |
| `mojeek` | Mojeek |
| `ecosia` | Ecosia |
| `brave_html` | Brave Search (scraper) |
| `brave` | Brave API *(requer chave)* |

### Rede .onion *(requer Tor ativo)*
| Slug | Engine | Descrição |
|---|---|---|
| `ahmia` | Ahmia | Índice mais atualizado da dark web |
| `torch` | Torch | Pioneiro, grande volume de links |
| `haystack` | Haystack | Foco em privacidade |

---

## Tor — bypass e dark web

```bash
python artemis.py tor install   # baixa o bundle oficial em .tor/
python artemis.py tor start     # inicia em background
python artemis.py tor stop      # para o processo
```

Ou use o painel **⚙** ao lado do badge Tor na web app para controle completo sem CLI.

O Tor serve para **duas coisas**:
- **Bypass** — rotação de IP via exit nodes, evita bloqueios por rate-limit nas engines normais
- **Dark web** — acesso às engines `.onion` (Ahmia, Torch, Haystack) diretamente pela rede Tor

> O bundle é baixado direto de `archive.torproject.org`. Nada é instalado no sistema.

---

## Funcionalidades

- 🔍 **Multi-engine** — 10 engines em paralelo com deduplicação
- 🛡 **Anti-bloqueio** — rotação de UA, headers aleatórios, retry com backoff
- 🧅 **Tor dual-mode** — bypass de scraping + busca na rede .onion (Ahmia, Torch, Haystack)
- 📋 **Copiar URL** com um clique
- 🕒 **Histórico de buscas** (localStorage)
- 🔽 **Exportar** resultados em JSON ou CSV
- 🔎 **Filtro por engine** pós-busca (incluindo filtro exclusivo 🧅 Onion)
- 🛡 **VirusTotal** inline por resultado
- 🏹 **Dork builder** com operadores extras (`site:`, `before:`, `after:`), preview colorido por operador
- 🎯 **Sites-alvo** — campo de operadores extras no painel avançado

---

<div align="center">
  <sub>By <strong>Tonnks</strong></sub>
</div>
