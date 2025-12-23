from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from comet.core.models import settings, web_config

router = APIRouter()
templates = Jinja2Templates("comet/templates")


@router.get("/configure")
@router.get("/{b64config}/configure")
async def configure(request: Request):
    # Import here to avoid circular dependency
    from comet.scrapers.manager import scraper_manager
    
    # Get available scrapers dynamically from the scraper manager
    available_scrapers = sorted([
        scraper_manager._get_scraper_setting_key(name)[1]
        for name in scraper_manager.scrapers.keys()
    ])
    
    # Create a copy of web_config with dynamically generated scrapers list
    web_config_with_scrapers = web_config.copy()
    web_config_with_scrapers["availableScrapers"] = available_scrapers
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "CUSTOM_HEADER_HTML": settings.CUSTOM_HEADER_HTML
            if settings.CUSTOM_HEADER_HTML
            else "",
            "webConfig": web_config_with_scrapers,
            "proxyDebridStream": settings.PROXY_DEBRID_STREAM,
        },
    )
