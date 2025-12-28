import random
import string

from fastapi import APIRouter, Request

from comet.core.config_validation import config_check
from comet.core.models import settings
from comet.debrid.manager import get_debrid_extension

router = APIRouter()


@router.get("/manifest.json")
@router.get("/{b64config}/manifest.json")
async def manifest(request: Request, b64config: str = None):
    base_manifest = {
        "id": settings.ADDON_ID,
        "description": "JavaStream is a fast torrent/debrid search add-on for Stremio.",
        "version": "2.0.0",
        "catalogs": [],
        "resources": [
            {
                "name": "stream",
                "types": ["movie", "series"],
                "idPrefixes": ["tt", "kitsu"],
            }
        ],
        "types": ["movie", "series", "anime", "other"],
        "logo": "https://i.imgur.com/jmVoVMu.jpeg",
        "background": "https://i.imgur.com/WwnXB3k.jpeg",
        "behaviorHints": {"configurable": True, "configurationRequired": False},
    }

    config = config_check(b64config)
    if not config:
        base_manifest["name"] = "❌ | JavaStream"
        base_manifest["description"] = (
            f"⚠️ OBSOLETE CONFIGURATION, PLEASE RE-CONFIGURE ON {request.url.scheme}://{request.url.netloc} ⚠️"
        )
        return base_manifest

    if b64config:
        suffix = "".join(ch for ch in str(b64config) if ch.isalnum())[:8]
        if suffix:
            base_manifest["id"] = f"{settings.ADDON_ID}.{suffix}"

    debrid_extension = get_debrid_extension(config["debridService"])
    base_manifest["name"] = (
        f"{settings.ADDON_NAME}{(' | ' + debrid_extension) if debrid_extension != 'TORRENT' else ''}"
    )

    return base_manifest
