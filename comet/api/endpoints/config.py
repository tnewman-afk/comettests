from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from comet.core.models import settings, web_config
from comet.utils.network import auto_detect_lan_ip

router = APIRouter()
templates = Jinja2Templates("comet/templates")


@router.get("/configure")
@router.get("/{b64config}/configure")
async def configure(request: Request):
    # Import here to avoid circular dependency
    from comet.scrapers.manager import scraper_manager
    
    # Create a copy of web_config with dynamically generated scrapers list
    web_config_with_scrapers = web_config.copy()
    web_config_with_scrapers["availableScrapers"] = scraper_manager.get_scraper_names()

    public_base_url = (settings.PUBLIC_BASE_URL or "").rstrip("/")
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "CUSTOM_HEADER_HTML": settings.CUSTOM_HEADER_HTML
            if settings.CUSTOM_HEADER_HTML
            else "",
            "webConfig": web_config_with_scrapers,
            "proxyDebridStream": settings.PROXY_DEBRID_STREAM,
            "detectedLanIp": auto_detect_lan_ip(),
            "publicBaseUrl": public_base_url,
        },
    )
