"""
Tor setup utilities for Artemis.

Handles:
- Detecting if Tor is already running (ports 9050 / 9150)
- Downloading the Tor Expert Bundle (Windows) to a local .tor/ directory
- Starting the bundled tor process in background
- Stopping the bundled tor process
"""

import os
import sys
import socket
import shutil
import subprocess
import tarfile
import zipfile
import tempfile
import platform
from pathlib import Path
from typing import Optional, Tuple
from .config import TOR_PORTS

# Directory where the bundled Tor will be stored
TOR_DIR = Path(__file__).parent.parent / ".tor"

# Tor Expert Bundle download URLs (official dist.torproject.org)
_TOR_BUNDLES = {
    "win32": "https://archive.torproject.org/tor-package-archive/torbrowser/13.5.1/tor-expert-bundle-windows-x86_64-13.5.1.tar.gz",
    "win64": "https://archive.torproject.org/tor-package-archive/torbrowser/13.5.1/tor-expert-bundle-windows-x86_64-13.5.1.tar.gz",
    "linux": "https://archive.torproject.org/tor-package-archive/torbrowser/13.5.1/tor-expert-bundle-linux-x86_64-13.5.1.tar.gz",
    "darwin": "https://archive.torproject.org/tor-package-archive/torbrowser/13.5.1/tor-expert-bundle-macos-x86_64-13.5.1.tar.gz",
}

_tor_process: Optional[subprocess.Popen] = None


def _platform_key() -> str:
    s = sys.platform.lower()
    if s.startswith("win"):
        return "win64"
    if s.startswith("darwin"):
        return "darwin"
    return "linux"


def bundled_tor_exe() -> Optional[Path]:
    """Return path to the bundled tor executable, or None if not installed."""
    if sys.platform.startswith("win"):
        candidates = [
            TOR_DIR / "tor" / "tor.exe",
            TOR_DIR / "tor.exe",
        ]
    else:
        candidates = [
            TOR_DIR / "tor" / "tor",
            TOR_DIR / "tor",
        ]
    for c in candidates:
        if c.exists():
            return c
    return None


def is_running(port: Optional[int] = None) -> Tuple[bool, Optional[int]]:
    """Return (running, port) — checks both known Tor ports."""
    ports = [port] if port else TOR_PORTS
    for p in ports:
        try:
            with socket.create_connection(("127.0.0.1", p), timeout=1):
                return True, p
        except OSError:
            pass
    return False, None


def download_tor(progress_callback=None) -> Tuple[bool, str]:
    """
    Download and extract the Tor Expert Bundle into TOR_DIR.
    progress_callback(message: str) is called with status updates.
    Returns (success, message).
    """
    key = _platform_key()
    url = _TOR_BUNDLES.get(key)
    if not url:
        return False, f"Plataforma não suportada para download automático: {sys.platform}"

    def _cb(msg):
        if progress_callback:
            progress_callback(msg)

    try:
        import urllib.request

        TOR_DIR.mkdir(parents=True, exist_ok=True)
        filename = url.split("/")[-1]
        dest = TOR_DIR / filename

        _cb(f"Baixando {filename}...")

        def _reporthook(count, block_size, total_size):
            if total_size > 0 and progress_callback:
                pct = min(100, int(count * block_size * 100 / total_size))
                progress_callback(f"Baixando... {pct}%")

        urllib.request.urlretrieve(url, dest, reporthook=_reporthook)
        _cb("Download concluído. Extraindo...")

        if filename.endswith(".tar.gz"):
            with tarfile.open(dest, "r:gz") as tar:
                try:
                    tar.extractall(TOR_DIR, filter="data")
                except TypeError:
                    tar.extractall(TOR_DIR)
        elif filename.endswith(".zip"):
            with zipfile.ZipFile(dest, "r") as zf:
                zf.extractall(TOR_DIR)

        dest.unlink(missing_ok=True)

        exe = bundled_tor_exe()
        if exe is None:
            return False, "Extração concluída mas executável tor não encontrado. Verifique o diretório .tor/"

        # Make executable on Unix
        if not sys.platform.startswith("win"):
            exe.chmod(0o755)

        _cb(f"Tor instalado em: {exe}")
        return True, str(exe)

    except Exception as e:
        return False, f"Erro ao baixar: {e}"


def start_bundled_tor(progress_callback=None) -> Tuple[bool, str]:
    """
    Start the bundled tor process.
    Returns (success, message).
    """
    global _tor_process

    def _cb(msg):
        if progress_callback:
            progress_callback(msg)

    # Already running externally?
    running, port = is_running()
    if running:
        return True, f"Tor já está rodando na porta {port}."

    exe = bundled_tor_exe()
    if exe is None:
        return False, "Tor não instalado. Use `python artemis.py tor install` primeiro."

    try:
        _cb("Iniciando tor...")
        _tor_process = subprocess.Popen(
            [str(exe)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(exe.parent),
        )

        # Wait up to 10s for Tor to bind its SOCKS port
        import time
        for _ in range(20):
            time.sleep(0.5)
            running, port = is_running()
            if running:
                _cb(f"Tor ativo na porta {port}.")
                return True, f"Tor iniciado na porta {port}."

        # If process died early
        if _tor_process.poll() is not None:
            return False, "Processo tor encerrou inesperadamente."

        return False, "Tor iniciou mas não respondeu a tempo. Verifique se a porta 9050 está disponível."

    except Exception as e:
        return False, f"Erro ao iniciar tor: {e}"


def stop_bundled_tor() -> Tuple[bool, str]:
    """Stop the bundled tor process if we started it."""
    global _tor_process
    if _tor_process is None:
        return False, "Nenhum processo Tor gerenciado pelo Artemis está rodando."
    try:
        _tor_process.terminate()
        _tor_process.wait(timeout=5)
        _tor_process = None
        return True, "Tor encerrado."
    except Exception as e:
        return False, f"Erro ao encerrar: {e}"


def get_status() -> dict:
    running, port = is_running()
    exe = bundled_tor_exe()
    return {
        "running": running,
        "port": port,
        "bundled_installed": exe is not None,
        "bundled_exe": str(exe) if exe else None,
        "managed": _tor_process is not None,
    }
