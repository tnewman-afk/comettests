#!/usr/bin/env python3
"""JavaStream Manager - GUI controller for the JavaStream server on Linux."""

from __future__ import annotations

import ipaddress
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import messagebox, ttk

APP_TITLE = "JavaStream Manager"
SERVICE_NAME = "javastream.service"
DEFAULT_PORT = 8000
POLL_INTERVAL_MS = 2000


def generate_admin_password(length: int = 18) -> str:
    return secrets.token_urlsafe(length)


def resolve_app_root() -> Path:
    env_root = os.environ.get("JAVASTREAM_APP_ROOT")
    if env_root:
        env_path = Path(env_root).expanduser()
        if (env_path / "comet").exists():
            return env_path

    base = Path(__file__).resolve().parents[1]
    if (base / "comet").exists():
        return base
    if (base / "app" / "comet").exists():
        return base / "app"
    return base


APP_ROOT = resolve_app_root()
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "javastream"
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "javastream"
STATE_FILE = CONFIG_DIR / "manager_state.json"
PID_FILE = DATA_DIR / "javastream.pid"
LOG_FILE = DATA_DIR / "javastream.log"
SYSTEMD_USER_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "systemd/user"
SERVICE_FILE = SYSTEMD_USER_DIR / SERVICE_NAME
CONFIG_FILE = CONFIG_DIR / "javastream_config.json"

SCRAPER_DEFINITIONS = [
    {
        "key": "jackett",
        "name": "Jackett",
        "enable_env": "SCRAPE_JACKETT",
        "fields": [
            {
                "env": "JACKETT_URL",
                "label": "Jackett URL",
                "default": "http://127.0.0.1:9117",
                "type": "string",
                "hint": "Example: http://127.0.0.1:9117",
            },
            {
                "env": "JACKETT_API_KEY",
                "label": "Jackett API Key",
                "default": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "type": "string",
                "placeholder": True,
                "hint": "Paste API key from Jackett",
            },
            {
                "env": "JACKETT_INDEXERS",
                "label": "Jackett Indexers",
                "default": "[]",
                "type": "list",
                "hint": "Example: [\"oxtorrent\",\"torrent9\"] or oxtorrent,torrent9",
            },
        ],
    },
    {
        "key": "prowlarr",
        "name": "Prowlarr",
        "enable_env": "SCRAPE_PROWLARR",
        "fields": [
            {
                "env": "PROWLARR_URL",
                "label": "Prowlarr URL",
                "default": "http://127.0.0.1:9696",
                "type": "string",
                "hint": "Example: http://127.0.0.1:9696",
            },
            {
                "env": "PROWLARR_API_KEY",
                "label": "Prowlarr API Key",
                "default": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "type": "string",
                "placeholder": True,
                "hint": "Paste API key from Prowlarr",
            },
            {
                "env": "PROWLARR_INDEXERS",
                "label": "Prowlarr Indexers",
                "default": "[]",
                "type": "list",
                "hint": "Example: [\"rarbg\",\"iptorrents\"] or rarbg,iptorrents",
            },
        ],
    },
    {
        "key": "comet",
        "name": "Comet",
        "enable_env": "SCRAPE_COMET",
        "fields": [
            {
                "env": "COMET_URL",
                "label": "Comet URL",
                "default": "https://comet.elfhosted.com",
                "type": "string",
            }
        ],
    },
    {
        "key": "nyaa",
        "name": "Nyaa",
        "enable_env": "SCRAPE_NYAA",
        "fields": [
            {
                "env": "NYAA_ANIME_ONLY",
                "label": "Anime only",
                "default": True,
                "type": "bool",
            },
            {
                "env": "NYAA_MAX_CONCURRENT_PAGES",
                "label": "Max concurrent pages",
                "default": 5,
                "type": "int",
            },
        ],
    },
    {
        "key": "zilean",
        "name": "Zilean",
        "enable_env": "SCRAPE_ZILEAN",
        "enable_default": True,
        "fields": [
            {
                "env": "ZILEAN_URL",
                "label": "Zilean URL",
                "default": "https://zilean.elfhosted.com",
                "type": "string",
            }
        ],
    },
    {
        "key": "stremthru",
        "name": "StremThru",
        "enable_env": "SCRAPE_STREMTHRU",
        "fields": [
            {
                "env": "STREMTHRU_SCRAPE_URL",
                "label": "StremThru scrape URL",
                "default": "https://stremthru.13377001.xyz",
                "type": "string",
            }
        ],
    },
    {
        "key": "bitmagnet",
        "name": "Bitmagnet",
        "enable_env": "SCRAPE_BITMAGNET",
        "fields": [
            {
                "env": "BITMAGNET_URL",
                "label": "Bitmagnet URL",
                "default": "https://bitmagnetfortheweebs.midnightignite.me",
                "type": "string",
            },
            {
                "env": "BITMAGNET_MAX_CONCURRENT_PAGES",
                "label": "Max concurrent pages",
                "default": 5,
                "type": "int",
            },
            {
                "env": "BITMAGNET_MAX_OFFSET",
                "label": "Max offset",
                "default": 15000,
                "type": "int",
            },
        ],
    },
    {
        "key": "torrentio",
        "name": "Torrentio",
        "enable_env": "SCRAPE_TORRENTIO",
        "enable_default": True,
        "fields": [
            {
                "env": "TORRENTIO_URL",
                "label": "Torrentio URL",
                "default": "https://torrentio.strem.fun",
                "type": "string",
            }
        ],
    },
    {
        "key": "mediafusion",
        "name": "MediaFusion",
        "enable_env": "SCRAPE_MEDIAFUSION",
        "fields": [
            {
                "env": "MEDIAFUSION_URL",
                "label": "MediaFusion URL",
                "default": "https://mediafusion.elfhosted.com",
                "type": "string",
            },
            {
                "env": "MEDIAFUSION_API_PASSWORD",
                "label": "MediaFusion API password",
                "default": "",
                "type": "string",
                "hint": "Example: password1 (optional)",
            },
            {
                "env": "MEDIAFUSION_LIVE_SEARCH",
                "label": "Enable live search",
                "default": True,
                "type": "bool",
            },
        ],
    },
    {
        "key": "aiostreams",
        "name": "AIOStreams",
        "enable_env": "SCRAPE_AIOSTREAMS",
        "fields": [
            {
                "env": "AIOSTREAMS_URL",
                "label": "AIOStreams URL",
                "default": "https://aio.example.com",
                "type": "string",
            },
            {
                "env": "AIOSTREAMS_USER_UUID_AND_PASSWORD",
                "label": "User UUID and password",
                "default": "user_uuid:password",
                "type": "string",
                "placeholder": True,
                "hint": "Format: user_uuid:password",
            },
        ],
    },
    {
        "key": "jackettio",
        "name": "Jackettio",
        "enable_env": "SCRAPE_JACKETTIO",
        "fields": [
            {
                "env": "JACKETTIO_URL",
                "label": "Jackettio URL",
                "default": "https://jackettio.example.com",
                "type": "string",
                "hint": "Manifest base URL without /manifest.json",
            }
        ],
    },
    {
        "key": "debridio",
        "name": "Debridio",
        "enable_env": "SCRAPE_DEBRIDIO",
        "fields": [
            {
                "env": "DEBRIDIO_API_KEY",
                "label": "Debridio API key",
                "default": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "type": "string",
                "placeholder": True,
            },
            {
                "env": "DEBRIDIO_PROVIDER",
                "label": "Debridio provider",
                "default": "realdebrid",
                "type": "string",
                "hint": "Example: realdebrid, alldebrid, premiumize",
            },
            {
                "env": "DEBRIDIO_PROVIDER_KEY",
                "label": "Debridio provider key",
                "default": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "type": "string",
                "placeholder": True,
            },
        ],
    },
    {
        "key": "torbox",
        "name": "TorBox",
        "enable_env": "SCRAPE_TORBOX",
        "fields": [
            {
                "env": "TORBOX_API_KEY",
                "label": "TorBox API key",
                "default": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "type": "string",
                "placeholder": True,
            }
        ],
    },
    {
        "key": "yggtorrent",
        "name": "YggTorrent",
        "enable_env": "SCRAPE_YGGTORRENT",
        "fields": [
            {
                "env": "YGGTORRENT_USERNAME",
                "label": "YGGTorrent username",
                "default": "username",
                "type": "string",
                "placeholder": True,
            },
            {
                "env": "YGGTORRENT_PASSWORD",
                "label": "YGGTorrent password",
                "default": "password",
                "type": "string",
                "placeholder": True,
            },
            {
                "env": "YGGTORRENT_PASSKEY",
                "label": "YGGTorrent passkey",
                "default": "passkey",
                "type": "string",
                "placeholder": True,
            },
            {
                "env": "YGGTORRENT_MAX_CONCURRENT_PAGES",
                "label": "Max concurrent pages",
                "default": 5,
                "type": "int",
            },
        ],
    },
]


class ManagerState:
    def __init__(self, first_launch_done: bool = False):
        self.first_launch_done = first_launch_done

    @classmethod
    def load(cls) -> "ManagerState":
        if not STATE_FILE.exists():
            return cls()
        try:
            data = json.loads(STATE_FILE.read_text())
            return cls(first_launch_done=bool(data.get("first_launch_done")))
        except (OSError, json.JSONDecodeError):
            return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"first_launch_done": self.first_launch_done}))


STATE = ManagerState.load()


WILDCARD_HOSTS = {"0.0.0.0", "::", "[::]"}


def auto_detect_lan_ip() -> str:
    for target in (("8.8.8.8", 80), ("1.1.1.1", 80)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(target)
                candidate = sock.getsockname()[0]
            ip = ipaddress.ip_address(candidate)
            if isinstance(ip, ipaddress.IPv4Address) and not ip.is_loopback:
                return str(ip)
        except OSError:
            continue
        except ValueError:
            continue

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            candidate = info[4][0]
            try:
                ip = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            if (
                isinstance(ip, ipaddress.IPv4Address)
                and (ip.is_private or ip.is_global)
                and not ip.is_loopback
            ):
                return str(ip)
    except OSError:
        pass

    return ""


def validate_server_host(host: str) -> bool:
    value = str(host).strip()
    if not value:
        return False
    if value == "localhost":
        return True
    if value in WILDCARD_HOSTS:
        return True
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return isinstance(ip, ipaddress.IPv4Address)


def load_server_settings(config: dict) -> tuple[str, int]:
    server = config.get("server")
    host = ""
    port = DEFAULT_PORT
    if isinstance(server, dict):
        host = str(server.get("host", "")).strip()
        port = server.get("port", DEFAULT_PORT)

    if not validate_server_host(host):
        detected = auto_detect_lan_ip()
        host = detected if detected else "127.0.0.1"

    try:
        port = int(port)
    except (TypeError, ValueError):
        port = DEFAULT_PORT
    if not (1 <= port <= 65535):
        port = DEFAULT_PORT

    return host, port


def connect_host_for_urls(host: str) -> str:
    value = str(host).strip()
    if value in WILDCARD_HOSTS or not value:
        detected = auto_detect_lan_ip()
        return detected if detected else "127.0.0.1"
    return value


def status_probe_hosts(host: str) -> list[str]:
    value = str(host).strip()
    probes: list[str] = []
    if value and value not in WILDCARD_HOSTS:
        probes.append(value)
    probes.append("127.0.0.1")
    return list(dict.fromkeys(probes))


def build_default_config() -> dict:
    detected_ip = auto_detect_lan_ip()
    config = {
        "admin_password": generate_admin_password(),
        "server": {"host": detected_ip if detected_ip else "127.0.0.1", "port": DEFAULT_PORT},
        "scrapers": {},
    }
    for scraper in SCRAPER_DEFINITIONS:
        fields = {}
        for field in scraper["fields"]:
            fields[field["env"]] = field.get("default", "")
        config["scrapers"][scraper["key"]] = {
            "enabled": bool(scraper.get("enable_default", False)),
            "fields": fields,
        }
    return config


def load_config() -> dict:
    config = build_default_config()
    if not CONFIG_FILE.exists():
        save_config(config)
        return config
    try:
        data = json.loads(CONFIG_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return config

    if isinstance(data, dict):
        admin_password = data.get("admin_password")
        if isinstance(admin_password, str):
            config["admin_password"] = admin_password

        server = data.get("server")
        if isinstance(server, dict):
            host = server.get("host")
            port = server.get("port")
            if isinstance(host, str):
                config["server"]["host"] = host
            if port is not None:
                config["server"]["port"] = port

        scrapers = data.get("scrapers")
        if isinstance(scrapers, dict):
            for scraper_key, scraper_config in config["scrapers"].items():
                incoming = scrapers.get(scraper_key, {})
                if not isinstance(incoming, dict):
                    continue
                enabled = incoming.get("enabled")
                if isinstance(enabled, bool):
                    scraper_config["enabled"] = enabled
                fields = incoming.get("fields")
                if isinstance(fields, dict):
                    for field_key in scraper_config["fields"]:
                        if field_key in fields:
                            scraper_config["fields"][field_key] = fields[field_key]

    if not str(config.get("admin_password", "")).strip():
        config["admin_password"] = generate_admin_password()
        save_config(config)

    return config


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def normalize_list_env(raw_value: str) -> str:
    value = str(raw_value).strip()
    if not value:
        return ""
    if value.startswith("["):
        parsed = json.loads(value)
        if not isinstance(parsed, list):
            raise ValueError("Expected a JSON array")
        return json.dumps(parsed, separators=(",", ":"))
    items = [item.strip() for item in value.split(",") if item.strip()]
    return json.dumps(items, separators=(",", ":"))


def format_env_value(value: str) -> str:
    text = str(value)
    if any(ch.isspace() for ch in text) or '"' in text:
        text = text.replace('"', '\\"')
        return f'"{text}"'
    return text


def build_config_env(config: dict) -> dict:
    env = {}
    admin_password = str(config.get("admin_password", "")).strip()
    if admin_password:
        env["ADMIN_DASHBOARD_PASSWORD"] = admin_password

    scrapers = config.get("scrapers", {})
    for scraper in SCRAPER_DEFINITIONS:
        scraper_key = scraper["key"]
        scraper_state = scrapers.get(scraper_key, {})
        enabled = bool(scraper_state.get("enabled", False))
        env[scraper["enable_env"]] = "true" if enabled else "false"

        fields = scraper_state.get("fields", {})
        for field in scraper["fields"]:
            env_name = field["env"]
            value = fields.get(env_name, field.get("default", ""))
            field_type = field.get("type", "string")

            if field_type == "bool":
                env[env_name] = "true" if bool(value) else "false"
                continue

            if field_type == "int":
                if value is None or value == "":
                    continue
                try:
                    env[env_name] = str(int(value))
                except (TypeError, ValueError):
                    continue
                continue

            if field_type == "list":
                try:
                    normalized = normalize_list_env(value)
                except (TypeError, ValueError):
                    continue
                if normalized:
                    env[env_name] = normalized
                continue

            text_value = str(value).strip()
            if field.get("placeholder") and text_value == str(field.get("default", "")).strip():
                continue
            if text_value:
                env[env_name] = text_value

    return env


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def python_executable() -> str:
    return os.environ.get("JAVASTREAM_PYTHON", sys.executable)


def service_env() -> dict:
    config = load_config()
    server_host, server_port = load_server_settings(config)
    connect_host = connect_host_for_urls(server_host)
    env = {
        "PYTHONPATH": str(APP_ROOT),
        "DATABASE_PATH": str(DATA_DIR / "javastream.db"),
        "FASTAPI_HOST": "0.0.0.0",
        "FASTAPI_PORT": str(server_port),
        "PUBLIC_BASE_URL": f"http://{connect_host}:{server_port}",
    }
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        env["XDG_CONFIG_HOME"] = xdg_config_home
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        env["XDG_DATA_HOME"] = xdg_data_home
    env.update(build_config_env(config))
    return env


def systemd_available() -> bool:
    if not shutil.which("systemctl"):
        return False
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "default.target"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode in (0, 3)
    except OSError:
        return False


def run_systemctl(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["systemctl", "--user", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def install_service() -> None:
    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    env = service_env()
    env_lines = "\n".join(
        f"Environment={key}={format_env_value(value)}"
        for key, value in sorted(env.items())
    )
    service_contents = """[Unit]
Description=JavaStream Server
After=network.target

[Service]
Type=simple
WorkingDirectory={app_root}
{env_lines}
ExecStart={exec_start}
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
""".format(
        app_root=APP_ROOT,
        env_lines=env_lines,
        exec_start=f"{python_executable()} -m comet.main",
    )
    SERVICE_FILE.write_text(service_contents)


def remove_service() -> None:
    if SERVICE_FILE.exists():
        SERVICE_FILE.unlink()


def is_service_installed() -> bool:
    return SERVICE_FILE.exists()


def is_service_active() -> bool:
    if not systemd_available() or not is_service_installed():
        return False
    result = run_systemctl("is-active", SERVICE_NAME)
    return result.returncode == 0


def is_service_enabled() -> bool:
    if not systemd_available() or not is_service_installed():
        return False
    result = run_systemctl("is-enabled", SERVICE_NAME)
    return result.returncode == 0


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def read_pid() -> Optional[int]:
    try:
        pid = int(PID_FILE.read_text().strip())
        return pid
    except (OSError, ValueError):
        return None


def start_fallback() -> None:
    ensure_data_dirs()
    host, port = load_server_settings(load_config())
    if any(is_port_open(probe_host, port) for probe_host in status_probe_hosts(host)):
        return
    env = os.environ.copy()
    env.update(service_env())
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [python_executable(), "-m", "comet.main"],
            cwd=str(APP_ROOT),
            env=env,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )
    PID_FILE.write_text(str(process.pid))


def stop_fallback() -> None:
    pid = read_pid()
    if not pid:
        return
    if not process_running(pid):
        PID_FILE.unlink(missing_ok=True)
        return
    os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        if not process_running(pid):
            PID_FILE.unlink(missing_ok=True)
            return
        time.sleep(0.2)
    os.kill(pid, signal.SIGKILL)
    PID_FILE.unlink(missing_ok=True)


def start_service() -> None:
    ensure_data_dirs()
    if systemd_available():
        install_service()
        run_systemctl("daemon-reload")
        run_systemctl("start", SERVICE_NAME)
    else:
        start_fallback()


def stop_service() -> None:
    if systemd_available() and is_service_installed():
        run_systemctl("stop", SERVICE_NAME)
    else:
        stop_fallback()


def restart_service() -> None:
    if systemd_available() and is_service_installed():
        run_systemctl("restart", SERVICE_NAME)
    else:
        stop_fallback()
        start_fallback()


def service_status() -> tuple[bool, str]:
    if systemd_available() and is_service_installed():
        return is_service_active(), "systemd user service"
    host, port = load_server_settings(load_config())
    return any(is_port_open(probe_host, port) for probe_host in status_probe_hosts(host)), "local process"


def wait_for_server(timeout: float = 15.0) -> bool:
    host, port = load_server_settings(load_config())
    end_time = time.time() + timeout
    while time.time() < end_time:
        if any(is_port_open(probe_host, port) for probe_host in status_probe_hosts(host)):
            return True
        time.sleep(0.25)
    return False


def open_dashboard() -> None:
    host, port = load_server_settings(load_config())
    webbrowser.open_new_tab(f"http://{connect_host_for_urls(host)}:{port}/configure")


def open_admin() -> None:
    host, port = load_server_settings(load_config())
    webbrowser.open_new_tab(f"http://{connect_host_for_urls(host)}:{port}/admin")


def set_autostart(enabled: bool) -> None:
    if not systemd_available():
        return
    if not is_service_installed():
        install_service()
        run_systemctl("daemon-reload")
    if enabled:
        run_systemctl("enable", SERVICE_NAME)
    else:
        run_systemctl("disable", SERVICE_NAME)


def ensure_first_launch() -> None:
    if STATE.first_launch_done:
        return
    start_service()
    if wait_for_server():
        open_dashboard()
        STATE.first_launch_done = True
        STATE.save()


def build_ui() -> tk.Tk:
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("560x360")
    root.minsize(560, 360)

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TFrame", background="#0f1719")
    style.configure("TLabel", background="#0f1719", foreground="#e7f0ee")
    style.configure("TLabelframe", background="#0f1719", foreground="#e7f0ee")
    style.configure("TLabelframe.Label", background="#0f1719", foreground="#e7f0ee")
    style.configure("TButton", background="#1fd7a2", foreground="#0b1112")

    config = load_config()
    server_host, server_port = load_server_settings(config)
    server_host_var = tk.StringVar(value=server_host)
    server_port_var = tk.StringVar(value=str(server_port))

    notebook = ttk.Notebook(root)
    status_frame = ttk.Frame(notebook, padding=18)
    settings_frame = ttk.Frame(notebook, padding=18)
    scrapers_frame = ttk.Frame(notebook)
    notebook.add(status_frame, text="Status")
    notebook.add(settings_frame, text="Settings")
    notebook.add(scrapers_frame, text="Scrapers")
    notebook.pack(fill="both", expand=True)

    title_label = ttk.Label(status_frame, text="JavaStream Manager", font=("TkDefaultFont", 16, "bold"))
    title_label.pack(anchor="w")

    status_row = ttk.Frame(status_frame)
    status_row.pack(fill="x", pady=(14, 6))

    status_canvas = tk.Canvas(status_row, width=12, height=12, highlightthickness=0, bg="#0f1719")
    status_dot = status_canvas.create_oval(2, 2, 10, 10, fill="#ff5c5c", outline="")
    status_canvas.pack(side="left")

    status_label = ttk.Label(status_row, text="Checking status...", font=("TkDefaultFont", 11, "bold"))
    status_label.pack(side="left", padx=8)

    mode_label = ttk.Label(status_frame, text="Mode: --")
    mode_label.pack(anchor="w", pady=(0, 12))

    button_row = ttk.Frame(status_frame)
    button_row.pack(fill="x", pady=(6, 12))

    start_button = ttk.Button(button_row, text="Start", width=12)
    start_button.pack(side="left", padx=(0, 8))

    stop_button = ttk.Button(button_row, text="Stop", width=12)
    stop_button.pack(side="left", padx=(0, 8))

    restart_button = ttk.Button(button_row, text="Restart", width=12)
    restart_button.pack(side="left")

    link_row = ttk.Frame(status_frame)
    link_row.pack(fill="x", pady=(10, 6))

    open_button = ttk.Button(link_row, text="Open Dashboard")
    open_button.pack(side="left", padx=(0, 8))

    open_admin_button = ttk.Button(link_row, text="Open Admin Dashboard")
    open_admin_button.pack(side="left")

    info_label = ttk.Label(
        status_frame,
        text="Server: --",
        foreground="#9fb1ad",
    )
    info_label.pack(anchor="w", pady=(8, 0))

    settings_title = ttk.Label(settings_frame, text="Startup Settings", font=("TkDefaultFont", 14, "bold"))
    settings_title.pack(anchor="w", pady=(0, 10))

    systemd_note = ttk.Label(
        settings_frame,
        text="These options use systemd user services when available.",
        foreground="#9fb1ad",
    )
    systemd_note.pack(anchor="w")

    service_var = tk.BooleanVar(value=is_service_installed())
    autostart_var = tk.BooleanVar(value=is_service_enabled())
    admin_password_var = tk.StringVar(value=config.get("admin_password", ""))

    network_frame = ttk.LabelFrame(settings_frame, text="Network", padding=12)
    network_frame.pack(fill="x", pady=(12, 0))
    network_frame.columnconfigure(1, weight=1)

    host_label = ttk.Label(network_frame, text="LAN IP address")
    host_label.grid(row=0, column=0, sticky="w", padx=(0, 12))

    host_entry = ttk.Entry(network_frame, textvariable=server_host_var)
    host_entry.grid(row=0, column=1, sticky="ew")

    def handle_autodetect_host() -> None:
        detected = auto_detect_lan_ip()
        if not detected:
            messagebox.showwarning(
                APP_TITLE,
                "Could not auto-detect a LAN IPv4 address.\n\nEnter your static IP manually (example: 192.168.1.10).",
            )
            return
        server_host_var.set(detected)

    autodetect_button = ttk.Button(network_frame, text="Auto-detect", command=handle_autodetect_host)
    autodetect_button.grid(row=0, column=2, padx=(8, 0))

    port_label = ttk.Label(network_frame, text="Port")
    port_label.grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(10, 0))

    port_entry = ttk.Entry(network_frame, textvariable=server_port_var, width=10)
    port_entry.grid(row=1, column=1, sticky="w", pady=(10, 0))

    network_hint = ttk.Label(
        network_frame,
        text="Set this to the machine's static LAN IP so other devices can reach JavaStream.",
        foreground="#9fb1ad",
    )
    network_hint.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

    service_check = ttk.Checkbutton(
        settings_frame,
        text="Run JavaStream as a background service",
        variable=service_var,
    )
    service_check.pack(anchor="w", pady=(12, 6))

    autostart_check = ttk.Checkbutton(
        settings_frame,
        text="Start JavaStream on login",
        variable=autostart_var,
    )
    autostart_check.pack(anchor="w")

    admin_frame = ttk.LabelFrame(settings_frame, text="Admin Dashboard", padding=12)
    admin_frame.pack(fill="x", pady=(16, 0))

    admin_label = ttk.Label(admin_frame, text="Admin password")
    admin_label.grid(row=0, column=0, sticky="w", padx=(0, 12))

    admin_entry = ttk.Entry(admin_frame, textvariable=admin_password_var)
    admin_entry.grid(row=0, column=1, sticky="ew")
    admin_frame.columnconfigure(1, weight=1)

    admin_hint = ttk.Label(
        admin_frame,
        text="Leave blank to auto-generate a password on next restart.",
        foreground="#9fb1ad",
    )
    admin_hint.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

    settings_action_frame = ttk.Frame(settings_frame)
    settings_action_frame.pack(fill="x", pady=(12, 0))
    settings_save_button = ttk.Button(settings_action_frame, text="Save Settings")
    settings_save_button.pack(side="right")

    scrapers_canvas = tk.Canvas(scrapers_frame, highlightthickness=0, bg="#0f1719")
    scrapers_scrollbar = ttk.Scrollbar(scrapers_frame, orient="vertical", command=scrapers_canvas.yview)
    scrapers_canvas.configure(yscrollcommand=scrapers_scrollbar.set)
    scrapers_scrollbar.pack(side="right", fill="y")
    scrapers_canvas.pack(side="top", fill="both", expand=True)

    scrapers_inner = ttk.Frame(scrapers_canvas, padding=18)
    scrapers_window = scrapers_canvas.create_window((0, 0), window=scrapers_inner, anchor="nw")

    def update_scrollregion(_: tk.Event) -> None:
        scrapers_canvas.configure(scrollregion=scrapers_canvas.bbox("all"))
        scrapers_canvas.itemconfigure(scrapers_window, width=scrapers_canvas.winfo_width())

    scrapers_inner.bind("<Configure>", update_scrollregion)
    scrapers_canvas.bind("<Configure>", update_scrollregion)

    def _on_mousewheel(event: tk.Event) -> None:
        scrapers_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(event: tk.Event) -> None:
        direction = -1 if event.num == 4 else 1
        scrapers_canvas.yview_scroll(direction, "units")

    scrapers_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    scrapers_canvas.bind_all("<Button-4>", _on_mousewheel_linux)
    scrapers_canvas.bind_all("<Button-5>", _on_mousewheel_linux)

    scrapers_title = ttk.Label(scrapers_inner, text="Scraper Configuration", font=("TkDefaultFont", 14, "bold"))
    scrapers_title.pack(anchor="w", pady=(0, 10))

    scraper_vars = {}

    for scraper in SCRAPER_DEFINITIONS:
        scraper_key = scraper["key"]
        scraper_config = config["scrapers"].get(scraper_key, {})
        frame = ttk.LabelFrame(scrapers_inner, text=scraper["name"], padding=12)
        frame.pack(fill="x", pady=(0, 12))
        frame.columnconfigure(1, weight=1)

        enabled_var = tk.BooleanVar(value=bool(scraper_config.get("enabled", False)))
        enable_check = ttk.Checkbutton(frame, text="Enable", variable=enabled_var)
        enable_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        field_vars = {}
        row_index = 1
        for field in scraper["fields"]:
            env_key = field["env"]
            field_type = field.get("type", "string")
            default_value = field.get("default", "")
            current_value = scraper_config.get("fields", {}).get(env_key, default_value)

            if field_type == "bool":
                var = tk.BooleanVar(value=bool(current_value))
                check = ttk.Checkbutton(frame, text=field["label"], variable=var)
                check.grid(row=row_index, column=0, columnspan=2, sticky="w", pady=(0, 6))
                field_vars[env_key] = var
                row_index += 1
                continue

            label = ttk.Label(frame, text=field["label"])
            label.grid(row=row_index, column=0, sticky="w", padx=(0, 12))

            var = tk.StringVar(value=str(current_value))
            entry = ttk.Entry(frame, textvariable=var)
            entry.grid(row=row_index, column=1, sticky="ew", pady=2)
            field_vars[env_key] = var
            row_index += 1

            hint = field.get("hint")
            if hint:
                hint_label = ttk.Label(frame, text=hint, foreground="#9fb1ad")
                hint_label.grid(row=row_index, column=0, columnspan=2, sticky="w", pady=(0, 6))
                row_index += 1

        scraper_vars[scraper_key] = {"enabled": enabled_var, "fields": field_vars}

    scrapers_action_frame = ttk.Frame(scrapers_frame, padding=12)
    scrapers_action_frame.pack(fill="x")

    scrapers_save_button = ttk.Button(scrapers_action_frame, text="Save Scraper Settings")
    scrapers_save_button.pack(side="right")

    def update_info_label() -> None:
        host, port = load_server_settings(load_config())
        info_label.config(
            text=f"Server: http://{connect_host_for_urls(host)}:{port} (configure at /configure)"
        )

    def collect_config_from_ui() -> Optional[dict]:
        new_config = build_default_config()
        new_config["admin_password"] = admin_password_var.get().strip()

        host_text = server_host_var.get().strip()
        if not validate_server_host(host_text):
            messagebox.showerror(
                APP_TITLE,
                "Invalid LAN IP address.\n\nEnter a non-loopback IPv4 address (example: 192.168.1.10), or use 0.0.0.0.",
            )
            return None
        port_text = server_port_var.get().strip()
        try:
            port_value = int(port_text)
        except ValueError:
            messagebox.showerror(APP_TITLE, "Invalid port number.")
            return None
        if not (1 <= port_value <= 65535):
            messagebox.showerror(APP_TITLE, "Port must be between 1 and 65535.")
            return None
        new_config["server"] = {"host": host_text, "port": port_value}

        for scraper in SCRAPER_DEFINITIONS:
            scraper_key = scraper["key"]
            scraper_entry = new_config["scrapers"][scraper_key]
            scraper_state = scraper_vars.get(scraper_key, {})
            enabled_var = scraper_state.get("enabled")
            scraper_entry["enabled"] = bool(enabled_var.get()) if enabled_var else False

            for field in scraper["fields"]:
                env_key = field["env"]
                field_type = field.get("type", "string")
                var = scraper_state.get("fields", {}).get(env_key)
                if var is None:
                    continue

                if field_type == "bool":
                    scraper_entry["fields"][env_key] = bool(var.get())
                    continue

                raw_value = str(var.get()).strip()
                if field_type == "int":
                    if raw_value == "":
                        scraper_entry["fields"][env_key] = ""
                        continue
                    try:
                        scraper_entry["fields"][env_key] = int(raw_value)
                    except ValueError:
                        messagebox.showerror(
                            APP_TITLE,
                            f"Invalid number for {field['label']}.",
                        )
                        return None
                    continue

                if field_type == "list":
                    if raw_value == "":
                        scraper_entry["fields"][env_key] = ""
                        continue
                    try:
                        normalized = normalize_list_env(raw_value)
                    except ValueError:
                        messagebox.showerror(
                            APP_TITLE,
                            f"Invalid list for {field['label']}. Use JSON or comma-separated values.",
                        )
                        return None
                    scraper_entry["fields"][env_key] = normalized
                    continue

                scraper_entry["fields"][env_key] = raw_value

        return new_config

    def apply_config_from_ui() -> None:
        new_config = collect_config_from_ui()
        if new_config is None:
            return

        save_config(new_config)
        update_info_label()
        generated_password = None
        if not str(new_config.get("admin_password", "")).strip():
            updated_config = load_config()
            generated_password = str(updated_config.get("admin_password", "")).strip() or None
            if generated_password:
                admin_password_var.set(generated_password)

        if systemd_available() and is_service_installed():
            install_service()
            run_systemctl("daemon-reload")
            if is_service_active():
                if messagebox.askyesno(APP_TITLE, "Restart JavaStream to apply changes?"):
                    restart_service()
        else:
            host, port = load_server_settings(load_config())
            if any(is_port_open(probe_host, port) for probe_host in status_probe_hosts(host)):
                if messagebox.askyesno(APP_TITLE, "Restart JavaStream to apply changes?"):
                    restart_service()

        if generated_password:
            messagebox.showinfo(
                APP_TITLE,
                "Settings saved.\n\nA new admin password was generated:\n"
                f"{generated_password}",
            )
        else:
            messagebox.showinfo(APP_TITLE, "Settings saved.")

    def refresh_status() -> None:
        running, mode = service_status()
        status_label.config(text="Running" if running else "Stopped")
        status_canvas.itemconfigure(status_dot, fill="#1fd7a2" if running else "#ff5c5c")
        mode_label.config(text=f"Mode: {mode}")
        update_info_label()
        root.after(POLL_INTERVAL_MS, refresh_status)

    def handle_start() -> None:
        try:
            start_service()
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Failed to start JavaStream.\n{exc}")

    def handle_stop() -> None:
        try:
            stop_service()
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Failed to stop JavaStream.\n{exc}")

    def handle_restart() -> None:
        try:
            restart_service()
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Failed to restart JavaStream.\n{exc}")

    def handle_service_toggle() -> None:
        if not systemd_available():
            messagebox.showwarning(
                APP_TITLE,
                "systemd user services are not available. JavaStream will run as a local process.",
            )
            service_var.set(False)
            autostart_var.set(False)
            return
        if service_var.get():
            install_service()
            run_systemctl("daemon-reload")
            start_service()
        else:
            run_systemctl("disable", SERVICE_NAME)
            stop_service()
            remove_service()
            run_systemctl("daemon-reload")
            autostart_var.set(False)

    def handle_autostart_toggle() -> None:
        if not systemd_available():
            autostart_var.set(False)
            return
        if not service_var.get():
            messagebox.showinfo(APP_TITLE, "Enable the background service first.")
            autostart_var.set(False)
            return
        set_autostart(autostart_var.get())
        if autostart_var.get():
            run_systemctl("start", SERVICE_NAME)

    start_button.configure(command=handle_start)
    stop_button.configure(command=handle_stop)
    restart_button.configure(command=handle_restart)
    open_button.configure(command=open_dashboard)
    open_admin_button.configure(command=open_admin)
    service_check.configure(command=handle_service_toggle)
    autostart_check.configure(command=handle_autostart_toggle)
    settings_save_button.configure(command=apply_config_from_ui)
    scrapers_save_button.configure(command=apply_config_from_ui)

    refresh_status()

    def prompt_first_launch_network_setup() -> None:
        if STATE.first_launch_done:
            return

        dialog = tk.Toplevel(root)
        dialog.title("Network Setup")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()

        container = ttk.Frame(dialog, padding=18)
        container.pack(fill="both", expand=True)

        title = ttk.Label(
            container,
            text="Set your machine's static LAN IP",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            container,
            text="Other devices on your network will use this address to connect.",
            foreground="#9fb1ad",
        )
        subtitle.pack(anchor="w", pady=(4, 12))

        form = ttk.Frame(container)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        dialog_host = tk.StringVar(value=server_host_var.get().strip() or connect_host_for_urls(server_host))
        dialog_port = tk.StringVar(value=server_port_var.get().strip() or str(server_port))

        ttk.Label(form, text="LAN IP address").grid(row=0, column=0, sticky="w", padx=(0, 12))
        dialog_host_entry = ttk.Entry(form, textvariable=dialog_host)
        dialog_host_entry.grid(row=0, column=1, sticky="ew")

        def dialog_autodetect() -> None:
            detected = auto_detect_lan_ip()
            if detected:
                dialog_host.set(detected)
            else:
                messagebox.showwarning(
                    APP_TITLE,
                    "Could not auto-detect a LAN IPv4 address.\n\nEnter your static IP manually (example: 192.168.1.10).",
                )

        ttk.Button(form, text="Auto-detect", command=dialog_autodetect).grid(row=0, column=2, padx=(8, 0))

        ttk.Label(form, text="Port").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(10, 0))
        ttk.Entry(form, textvariable=dialog_port, width=10).grid(row=1, column=1, sticky="w", pady=(10, 0))

        def save_and_close() -> None:
            host_text = dialog_host.get().strip()
            if not validate_server_host(host_text):
                messagebox.showerror(
                    APP_TITLE,
                    "Invalid LAN IP address.\n\nEnter a non-loopback IPv4 address (example: 192.168.1.10), or use 0.0.0.0.",
                )
                return
            try:
                port_value = int(dialog_port.get().strip())
            except ValueError:
                messagebox.showerror(APP_TITLE, "Invalid port number.")
                return
            if not (1 <= port_value <= 65535):
                messagebox.showerror(APP_TITLE, "Port must be between 1 and 65535.")
                return

            server_host_var.set(host_text)
            server_port_var.set(str(port_value))
            updated = load_config()
            updated["server"] = {"host": host_text, "port": port_value}
            save_config(updated)
            update_info_label()
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="Continue", command=save_and_close).pack(side="right")
        ttk.Button(actions, text="Cancel", command=cancel).pack(side="right", padx=(0, 8))

        dialog_host_entry.focus_set()
        root.wait_window(dialog)

    def ensure_first_launch_with_setup() -> None:
        if STATE.first_launch_done:
            return
        prompt_first_launch_network_setup()
        ensure_first_launch()

    root.after(600, ensure_first_launch_with_setup)

    return root


if __name__ == "__main__":
    ensure_data_dirs()
    app = build_ui()
    app.mainloop()
