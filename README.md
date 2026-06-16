# 🏹 Artemis — Google Dorks Search Tool

Ferramenta de busca de Google Dorks com múltiplas engines, proteção anti-bloqueio, suporte a Tor e interface dual: **CLI** e **Web App local**.

---

## Índice

- [Instalação](#instalação)
- [Configuração](#configuração-opcional)
- [Uso — CLI](#uso--cli)
- [Uso — Web App](#uso--web-app)
- [Engines de busca](#engines-de-busca)
- [Proteção anti-bloqueio](#proteção-anti-bloqueio)
- [Tor — rotação de IP](#tor--rotação-de-ip)
- [Exemplos de dorks](#exemplos-de-dorks)

---

## Instalação

```bash
pip install -r requirements.txt
```

> **Recomendado:** use um virtualenv.
> ```bash
> python -m venv .venv
> .venv\Scripts\activate   # Windows
> pip install -r requirements.txt
> ```

---

## Configuração (opcional)

Copie o arquivo de exemplo e preencha as chaves que desejar:

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

| Variável | Descrição | Obrigatório? |
|---|---|---|
| `VIRUSTOTAL_API_KEY` | Habilita verificação de segurança de URLs | Não |
| `BRAVE_API_KEY` | Habilita a engine Brave Search (API oficial) | Não |
| `TOR_PROXY` | Endereço SOCKS5 do Tor (ex: `socks5://127.0.0.1:9050`) | Não |

Sem nenhuma chave configurada a ferramenta já funciona com DuckDuckGo, Bing, Brave e mais.

---

## Uso — CLI

```bash
# Busca simples (todas as engines disponíveis)
python artemis.py search "site:gov.br filetype:pdf"

# Escolher engines específicas
python artemis.py search "inurl:login" --engines ddg,bing

# Incluir verificação VirusTotal (requer VIRUSTOTAL_API_KEY)
python artemis.py search "intext:password" --vt

# Ajustar número máximo de resultados por engine
python artemis.py search "intitle:index.of" --max 20
```

---

## Uso — Web App

```bash
python artemis.py web
```

Abre em `http://127.0.0.1:5000`

- Digite o dork e pressione **Enter**
- Ative/desative engines clicando nas **pills de engine**
- Clique no badge **Tor** para ativar/desativar roteamento via Tor em tempo real
- Botão **🛡 Verificar** aparece automaticamente se `VIRUSTOTAL_API_KEY` estiver configurada

```bash
# Porta personalizada
python artemis.py web --port 8080
```

---

## Engines de busca

| Slug | Engine | Método |
|---|---|---|
| `ddg` | DuckDuckGo | Biblioteca oficial (html backend) |
| `ddghtml` | DuckDuckGo HTML | POST direto |
| `bing` | Bing (en-US) | Scraping |
| `google` | Bing (en-GB) | Scraping, mercado britânico |
| `startpage` | Bing (pt-BR) | Scraping, mercado brasileiro |
| `yahoo` | Brave Search | Scraping sem API key |
| `brave` | Brave (API) | API oficial (requer `BRAVE_API_KEY`) |

---

## Proteção anti-bloqueio

O Artemis tem uma camada anti-detecção automática ativa em todas as buscas:

- **Rotação de User-Agent** — pool de 50+ UAs reais via `fake-useragent` (Chrome, Firefox, Safari, Edge)
- **Headers randomizados** — Accept-Language, DNT e outros variam por request
- **Delays aleatórios** — 0.5 a 2.5 segundos entre requests para parecer humano
- **Retry automático** — 2 tentativas com backoff exponencial em respostas 429/503

---

## Tor — rotação de IP

O Tor rotaciona o IP a cada circuit, tornando buscas muito mais difíceis de bloquear.

### Opção 1 — Tor Browser (mais fácil)

1. Baixe e instale: https://www.torproject.org/download/
2. Abra o Tor Browser e clique em **Connect**
3. No Artemis Web App, clique no badge **Tor** — ele ficará verde
4. Todas as buscas passarão pelo Tor automaticamente

### Opção 2 — Download automático pelo Artemis (sem instalar nada)

O Artemis pode baixar e gerenciar o **Tor Expert Bundle** diretamente na pasta `.tor/` do projeto, sem instalar nada no sistema.

```bash
# 1. Verificar status
python artemis.py tor status

# 2. Baixar e instalar o Tor (Official Expert Bundle)
python artemis.py tor install

# 3. Iniciar o Tor em background
python artemis.py tor start

# 4. Em outro terminal, iniciar a web app normalmente
python artemis.py web
# → Clique no badge Tor na interface para ativá-lo

# Parar o Tor quando terminar
python artemis.py tor stop
```

> **Segurança:** o Artemis baixa o bundle direto de `archive.torproject.org` (fonte oficial). Nenhum arquivo é instalado fora do diretório do projeto.

### Opção 3 — Configuração manual via .env

Se você já tem o Tor rodando em outra porta:

```env
# .env
TOR_PROXY=socks5://127.0.0.1:9050   # serviço tor
# ou
TOR_PROXY=socks5://127.0.0.1:9150   # Tor Browser
```

### Renovação de circuito automática

Se o pacote `stem` estiver instalado, o Artemis renova o circuito Tor a cada 10 requests automaticamente:

```bash
pip install stem
```

---

## Exemplos de dorks

```
site:empresa.com.br filetype:xls
inurl:admin intitle:"login"
"index of" "parent directory" mp3
intitle:"phpMyAdmin" "Welcome to phpMyAdmin"
ext:env "DB_PASSWORD"
harry potter filetype:pdf
intext:"confidential" site:gov.br
```
