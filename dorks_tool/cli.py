import os
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from dotenv import load_dotenv

load_dotenv()

from .search import run_search
from .searchers.registry import ALL_SEARCHERS, ONION_SLUGS
from .http_client import tor_enabled
from . import virustotal
from . import tor_setup

console = Console()
app = typer.Typer(add_completion=False, help="Artemis — Google Dorks Search Tool")

BANNER = r"""
    _         _                     _     
   / \   _ __| |_ ___ _ __ ___  (_)___
  / _ \ | '__| __/ _ \ '_ ` _ \ | / __|
 / ___ \| |  | ||  __/ | | | | || \__ \\
/_/   \_\_|   \__\___|_| |_| |_|/ |___/
                               |__/     
"""


def _print_banner():
    text = Text(BANNER, style="bold #7c3aed")
    console.print(text)
    console.print(
        "  [dim]Precision search. Powered by multiple engines.[/dim]\n"
    )


def _engines_help() -> str:
    slugs = [s.slug for s in ALL_SEARCHERS]
    return "Engines: " + ", ".join(slugs) + ". Separe por vírgula. Padrão: todas disponíveis."


@app.command()
def search(
    query: str = typer.Argument(..., help="Dork ou termo de busca"),
    engines: Optional[str] = typer.Option(
        None, "--engines", "-e", help=_engines_help()
    ),
    vt: bool = typer.Option(False, "--vt", help="Verificar URLs no VirusTotal (requer VIRUSTOTAL_API_KEY no .env)"),
    max_results: int = typer.Option(15, "--max", "-n", help="Máximo de resultados por engine"),
):
    """Pesquisa um dork em múltiplas search engines."""
    _print_banner()

    engine_slugs = [e.strip() for e in engines.split(",")] if engines else None

    if engine_slugs:
        onion_requested = [s for s in engine_slugs if s in ONION_SLUGS]
        if onion_requested and not tor_enabled():
            console.print(
                f"[yellow]⚠  Engines .onion ({', '.join(onion_requested)}) requerem Tor ativo.[/yellow] "
                "Inicie com [bold]python artemis.py tor start[/bold] primeiro.\n"
            )

    if vt and not virustotal.is_available():
        console.print("[yellow]⚠  VirusTotal desativado:[/yellow] configure [bold]VIRUSTOTAL_API_KEY[/bold] no arquivo .env\n")
        vt = False

    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold #7c3aed"),
        TextColumn("[bold white]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("Caçando resultados...", total=None)
        results, _ = run_search(query, engine_slugs=engine_slugs, max_per_engine=max_results)

    if not results:
        console.print(Panel(
            "[dim]Nenhum resultado encontrado. Tente outro dork ou verifique sua conexão.[/dim]",
            border_style="#7c3aed",
            title="[bold]Artemis[/bold]",
        ))
        raise typer.Exit()

    console.print(f"[dim]  {len(results)} resultado(s) encontrado(s)[/dim]\n")

    table = Table(
        box=box.ROUNDED,
        border_style="#7c3aed",
        header_style="bold #7c3aed",
        show_lines=True,
        expand=True,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Título", style="bold white", min_width=20)
    table.add_column("URL", style="cyan", min_width=30)
    table.add_column("Engine", style="#a78bfa", width=12, justify="center")

    for i, r in enumerate(results, 1):
        table.add_row(str(i), r.title or "[dim]sem título[/dim]", r.url, r.engine)

    console.print(table)

    if vt:
        console.print("\n[bold #7c3aed]Verificando URLs no VirusTotal...[/bold #7c3aed]\n")
        vt_table = Table(
            box=box.ROUNDED,
            border_style="#7c3aed",
            header_style="bold #7c3aed",
            show_lines=True,
            expand=True,
        )
        vt_table.add_column("#", style="dim", width=4, justify="right")
        vt_table.add_column("URL", style="cyan", min_width=30)
        vt_table.add_column("Veredito", justify="center", width=14)
        vt_table.add_column("Malicioso", justify="center", width=10)
        vt_table.add_column("Suspeito", justify="center", width=10)
        vt_table.add_column("Total", justify="center", width=8)

        with Progress(
            SpinnerColumn(spinner_name="dots", style="bold #7c3aed"),
            TextColumn("[bold white]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Verificando...", total=len(results))
            vt_results = []
            for r in results:
                res = virustotal.check_url(r.url)
                vt_results.append((r, res))
                progress.advance(task)

        for i, (r, vt_res) in enumerate(vt_results, 1):
            if not vt_res:
                continue
            if "error" in vt_res:
                verdict_str = "[dim]erro[/dim]"
                mal = sus = tot = "-"
            else:
                v = vt_res["verdict"]
                if v == "malicious":
                    verdict_str = "[bold red]⛔ Malicioso[/bold red]"
                elif v == "suspicious":
                    verdict_str = "[bold yellow]⚠ Suspeito[/bold yellow]"
                else:
                    verdict_str = "[bold green]✔ Limpo[/bold green]"
                mal = str(vt_res["malicious"])
                sus = str(vt_res["suspicious"])
                tot = str(vt_res["total"])

            vt_table.add_row(str(i), r.url, verdict_str, mal, sus, tot)

        console.print(vt_table)


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", help="Host do servidor"),
    port: int = typer.Option(5000, help="Porta do servidor"),
):
    """Inicia a interface web no browser."""
    _print_banner()
    console.print(f"[bold #7c3aed]Iniciando interface web em[/bold #7c3aed] [cyan]http://{host}:{port}[/cyan]\n")
    from .web.app import create_app
    flask_app = create_app()
    flask_app.run(host=host, port=port, debug=False)


# ── Tor command group ────────────────────────────────────────────────────────
tor_app = typer.Typer(help="Gerenciar o Tor para rotação de IP nas buscas.")
app.add_typer(tor_app, name="tor")


@tor_app.command("status")
def tor_status():
    """Verifica se o Tor está instalado e rodando."""
    _print_banner()
    s = tor_setup.get_status()
    if s["running"]:
        console.print(f"[bold green]✔ Tor rodando[/bold green] na porta [cyan]{s['port']}[/cyan]")
    else:
        console.print("[yellow]✘ Tor não detectado[/yellow] nas portas 9050 / 9150")

    if s["bundled_installed"]:
        console.print(f"[dim]  Bundle local: {s['bundled_exe']}[/dim]")
    else:
        console.print("[dim]  Bundle local: não instalado[/dim]")

    if not s["running"]:
        console.print("\n[dim]Dica:[/dim] use [bold]python artemis.py tor install[/bold] para baixar o Tor automaticamente.")


@tor_app.command("install")
def tor_install():
    """Baixa e instala o Tor Expert Bundle localmente (não modifica o sistema)."""
    _print_banner()

    running, port = tor_setup.is_running()
    if running:
        console.print(f"[green]✔ Tor já está rodando na porta {port} — nada a instalar.[/green]")
        raise typer.Exit()

    if tor_setup.bundled_tor_exe():
        console.print("[green]✔ Tor já está instalado localmente em .tor/[/green]")
        console.print("[dim]Use [bold]python artemis.py tor start[/bold] para iniciá-lo.[/dim]")
        raise typer.Exit()

    console.print("[bold #7c3aed]Instalando Tor Expert Bundle...[/bold #7c3aed]")
    console.print("[dim]Fonte oficial: dist.torproject.org (sem modificações no sistema)[/dim]\n")

    messages = []

    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold #7c3aed"),
        TextColumn("[bold white]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Baixando...", total=None)

        def _cb(msg):
            messages.append(msg)
            progress.update(task, description=msg)

        ok, result = tor_setup.download_tor(progress_callback=_cb)

    if ok:
        console.print(f"[bold green]✔ Instalado com sucesso![/bold green]")
        console.print(f"[dim]  {result}[/dim]")
        console.print("\n[dim]Próximo passo:[/dim] [bold]python artemis.py tor start[/bold]")
    else:
        console.print(f"[bold red]✘ Falha na instalação:[/bold red] {result}")
        console.print("\n[dim]Alternativa:[/dim] Baixe o Tor Browser em [cyan]https://www.torproject.org/download/[/cyan]")


@tor_app.command("start")
def tor_start():
    """Inicia o Tor (bundle local ou detecta Tor Browser rodando)."""
    _print_banner()

    running, port = tor_setup.is_running()
    if running:
        console.print(f"[green]✔ Tor já está rodando na porta {port}.[/green]")
        raise typer.Exit()

    console.print("[bold #7c3aed]Iniciando Tor...[/bold #7c3aed]")

    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold #7c3aed"),
        TextColumn("[bold white]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Aguardando Tor...", total=None)

        def _cb(msg):
            progress.update(task, description=msg)

        ok, result = tor_setup.start_bundled_tor(progress_callback=_cb)

    if ok:
        console.print(f"[bold green]✔ {result}[/bold green]")
        console.print("\n[dim]O Tor ficará ativo enquanto esta sessão do terminal estiver aberta.[/dim]")
        console.print("[dim]Para usar na web app, inicie [bold]python artemis.py web[/bold] em outro terminal.[/dim]")
    else:
        console.print(f"[bold red]✘ {result}[/bold red]")
        if "não instalado" in result:
            console.print("\n[dim]Execute primeiro:[/dim] [bold]python artemis.py tor install[/bold]")


@tor_app.command("stop")
def tor_stop():
    """Para o processo Tor gerenciado pelo Artemis."""
    ok, result = tor_setup.stop_bundled_tor()
    if ok:
        console.print(f"[green]✔ {result}[/green]")
    else:
        console.print(f"[yellow]{result}[/yellow]")
