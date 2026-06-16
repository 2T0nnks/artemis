# Artemis — Wiki

**Busca precisa. Múltiplas engines. Suporte a Tor.**

🇧🇷 Português · [🇺🇸 English](Home.en) · [🇪🇸 Español](Home.es)

---

## Índice

- [Instalação](#instalação)
- [Engines disponíveis](#engines-disponíveis)
- [Dork Builder](#dork-builder)
- [Tor — bypass e dark web](#tor--bypass-e-dark-web)
- [Engines .onion](#engines-onion)
- [Anti-bloqueio](#anti-bloqueio)
- [Exportar resultados](#exportar-resultados)
- [VirusTotal](#virustotal)
- [Engine Manager](#engine-manager)
- [Interface multilíngue](#interface-multilíngue)
- [CLI](#cli)

---

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
python artemis.py web         # → http://127.0.0.1:5000
```

**Variáveis de ambiente** (arquivo `.env`, todas opcionais):

| Variável | Descrição |
|---|---|
| `VIRUSTOTAL_API_KEY` | Verificação de segurança de URLs |
| `BRAVE_API_KEY` | Engine Brave Search via API oficial |
| `TOR_PROXY` | Ex: `socks5://127.0.0.1:9050` |

---

## Engines disponíveis

### Surface Web

| Slug | Engine | Observação |
|---|---|---|
| `ddghtml` | DuckDuckGo HTML | Scraper sem API |
| `bing` | Bing | Scraper (en-US) |
| `google` | Bing Global | Scraper (en-GB) |
| `startpage` | Bing PT-BR | Scraper (pt-BR) |
| `ddg` | DuckDuckGo API | Via biblioteca oficial |
| `searx` | SearXNG | 7 instâncias públicas, ordem aleatória |
| `mojeek` | Mojeek | Índice próprio |
| `ecosia` | Ecosia | Engine sustentável |
| `brave_html` | Brave Search | Scraper HTML |
| `brave` | Brave API | Requer `BRAVE_API_KEY` |
| *custom* | *qualquer* | Adicionadas via Engine Manager |

### Rede .onion *(requer Tor ativo)*

| Slug | Engine | Descrição |
|---|---|---|
| `ahmia` | Ahmia | Índice mais atualizado da dark web |
| `torch` | Torch | Pioneiro, grande volume de links |
| `haystack` | Haystack | Foco em privacidade |

> Engines .onion só aparecem na UI quando o Tor estiver ativo. Não funcionam sem o daemon do Tor rodando localmente.

---

## Dork Builder

O Dork Builder gera dorks precisos automaticamente baseado na categoria escolhida.

### Categorias

| Categoria | Formatos gerados |
|---|---|
| Livro | `pdf epub mobi djvu` |
| Mangá | `cbz cbr pdf zip` |
| Filme | `mkv mp4 avi 1080p 720p 4k` |
| Música | `mp3 flac wav ogg aac` |
| Curso | `pdf mp4 zip inurl:torrent` |
| Software | `exe zip iso dmg inurl:download inurl:release` |
| Livre | campo livre, sem modificações |

### Painel avançado

- **Excluir sites** — ex: `amazon.com, goodreads.com` → adiciona `-site:` no dork
- **Operadores extras** — ex: `site:gov.br before:2024 intext:confidencial` → concatenado ao final
- **Formatos** — chips ativáveis individualmente por categoria
- **Preview colorido** — cada operador tem cor distinta em tempo real:
  - 🟡 `intitle:` · 🟣 `inurl:` · 🔵 `site:` · 🟠 `intext:` · 🟤 `filetype:` · 🔴 `-site:`(exclusão) · 🟢 `"frase exata"`

---

## Tor — bypass e dark web

O Tor serve para **duas coisas distintas**:

### 1. Bypass de anti-scraping
Roteia as requisições das engines normais (DDG, Bing etc.) pelo Tor → exit node com IP aleatório → o site alvo não vê seu IP real. A cada renovação de circuito, o exit node muda.

```
httpx → SOCKS5 → Tor → exit node (IP aleatório) → site alvo
```

### 2. Pesquisa na rede .onion
As engines `.onion` rodam dentro da rede Tor. O tráfego nunca sai para a internet pública.

```
httpx → SOCKS5 → Tor → relay → relay → servidor .onion
```

### Ativar via CLI

```bash
python artemis.py tor install   # baixa o bundle oficial
python artemis.py tor start     # inicia em background
python artemis.py tor stop      # para o processo
```

### Ativar via Web App

1. Clique no badge **Tor** na interface
2. Use o painel **⚙** para controle avançado:
   - Renovar circuito a cada N buscas
   - Iniciar/parar o daemon
   - Acessar engines .onion

---

## Engines .onion

Quando o Tor estiver ativo, o bloco **🧅 Rede .onion** aparece no painel ⚙:

- **Pills individuais** — ative Ahmia, Torch e/ou Haystack separadamente
- **Modo Surface + Onion** — busca nas engines normais ativas + engines .onion em paralelo
- **Modo Só .onion** — desativa todas as engines normais, usa apenas as .onion selecionadas
- **Filtro pós-busca** — pill `🧅 Só Onion` na barra de filtro isola apenas resultados `.onion`

---

## Anti-bloqueio

Todas as requisições passam pela camada de proteção em `http_client.py`:

- **Rotação de User-Agent** via `fake-useragent` (Chrome, Firefox, Edge, Safari)
- **Headers aleatórios** — `Accept-Language`, `DNT`, `Referer` variados por requisição
- **Retry com backoff exponencial** em respostas 429 e 503
- **Renovação de circuito Tor** a cada N buscas (configurável)
- **Delay apenas em retentativas** — sem espera na primeira tentativa

---

## Exportar resultados

Após a busca, clique em **⬇ Exportar**:

- **JSON** — array de objetos `{title, url, snippet, engine}`
- **CSV** — planilha com as mesmas colunas

A exportação é feita totalmente no cliente (sem nova requisição ao servidor).

---

## VirusTotal

Se `VIRUSTOTAL_API_KEY` estiver configurada, cada resultado exibe um badge de segurança. Clique em **Verificar** para consultar o relatório completo da URL via API VT.

---

## Engine Manager

Clique no botão **🔌** ao lado do badge Tor na web app.

### Adicionar engine

1. Abra a aba **Adicionar engine**
2. Preencha nome, slug único, URL de busca e método (GET/POST)
3. Informe o parâmetro da query (ex: `q`) — o valor `{query}` será substituído pelo termo buscado
4. Informe seletores CSS para o container de resultado e para o título/link
5. Clique em **Salvar engine** ou **Salvar e auto-detectar**

### Estrutura do `engines.json`

```json
{
  "slug": "minha-engine",
  "name": "Minha Engine",
  "url": "https://exemplo.com/search",
  "method": "GET",
  "params": {"q": "{query}"},
  "result_selector": "div.result",
  "title_selector": "h2 a",
  "snippet_selector": "p.desc",
  "enabled": true,
  "health": "ok"
}
```

### Health check

O botão 🦩 roda uma busca de teste (`python`) e marca a engine como:
- **ok** — retornou resultados
- **degraded** — respondeu mas sem resultados
- **offline** — falhou completamente

### Auto-detectar seletores

O Artemis busca a página com o termo `python`, analisa a estrutura HTML e tenta inferir os seletores corretos usando heurísticas semânticas e estruturais. Se conseguir, atualiza o `engines.json` automaticamente.

---

## Interface multilíngue

Clique nos botões 🇧🇷 **PT** · 🇺🇸 **EN** · 🇪🇸 **ES** no canto superior direito para alternar o idioma da interface. A preferência é salva no `localStorage`.

---

## CLI

```bash
# Busca simples
python artemis.py search "dork aqui"

# Engines específicas
python artemis.py search "inurl:login" --engines ddg,bing,searx

# Com verificação VirusTotal
python artemis.py search "filetype:pdf confidencial" --vt

# Limite de resultados
python artemis.py search "intext:password" --max 30

# Gerenciar Tor
python artemis.py tor install
python artemis.py tor start
python artemis.py tor stop
python artemis.py tor status
```
