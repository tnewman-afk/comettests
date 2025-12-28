from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any

SERVICE_NAME = "javastream.service"

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "javastream"
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "javastream"
SYSTEMD_USER_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "systemd/user"

CONFIG_FILE = CONFIG_DIR / "javastream_config.json"
SERVICE_FILE = SYSTEMD_USER_DIR / SERVICE_NAME


SCRAPER_DEFINITIONS: list[dict[str, Any]] = [
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
                "hint": 'Example: ["oxtorrent","torrent9"] or oxtorrent,torrent9',
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
                "hint": 'Example: ["rarbg","iptorrents"] or rarbg,iptorrents',
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
                "default": "",
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
                "default": "",
                "type": "string",
                "hint": "Full manifest URL without /manifest.json",
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
                "label": "Debridio API Key",
                "default": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "type": "string",
                "placeholder": True,
            },
            {
                "env": "DEBRIDIO_PROVIDER",
                "label": "Debridio provider",
                "default": "realdebrid",
                "type": "string",
                "hint": "alldebrid, debrider, debridlink, easydebrid, premiumize, realdebrid, torbox",
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
                "label": "TorBox API Key",
                "default": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "type": "string",
                "placeholder": True,
            }
        ],
    },
    {
        "key": "yggtorrent",
        "name": "YGGTorrent",
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


def generate_admin_password(length: int = 18) -> str:
    return secrets.token_urlsafe(length)


def build_default_config(*, admin_password: str | None = None) -> dict[str, Any]:
    config: dict[str, Any] = {"admin_password": admin_password or "", "scrapers": {}}
    for scraper in SCRAPER_DEFINITIONS:
        fields: dict[str, Any] = {}
        for field in scraper["fields"]:
            fields[field["env"]] = field.get("default", "")
        config["scrapers"][scraper["key"]] = {
            "enabled": bool(scraper.get("enable_default", False)),
            "fields": fields,
        }
    return config


def load_config(config_file: Path = CONFIG_FILE) -> dict[str, Any]:
    config = build_default_config(admin_password="")
    if not config_file.exists():
        return config
    try:
        data = json.loads(config_file.read_text())
    except (OSError, json.JSONDecodeError):
        return config

    if isinstance(data, dict):
        admin_password = data.get("admin_password")
        if isinstance(admin_password, str):
            config["admin_password"] = admin_password

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

    return config


def save_config(config: dict[str, Any], config_file: Path = CONFIG_FILE) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps(config, indent=2))


def ensure_config(config_file: Path = CONFIG_FILE) -> dict[str, Any]:
    config = load_config(config_file)
    changed = False
    if not isinstance(config.get("admin_password"), str) or not config["admin_password"].strip():
        config["admin_password"] = generate_admin_password()
        changed = True
    if not config_file.exists() or changed:
        save_config(config, config_file)
    return config


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


def build_config_env(config: dict[str, Any]) -> dict[str, str]:
    env: dict[str, str] = {}
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
