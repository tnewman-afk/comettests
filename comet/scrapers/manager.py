import asyncio
import importlib
import inspect
import os
import pkgutil
from typing import Dict, List, Optional

import aiohttp

from comet.core.logger import logger
from comet.core.models import settings
from comet.scrapers.base import BaseScraper
from comet.scrapers.models import ScrapeRequest
from comet.services.anime import anime_mapper
from comet.utils.parsing import associate_urls_credentials

class ScraperManager:
    def __init__(self):
        self.scrapers: Dict[str, BaseScraper] = {}
        self.scraper_requires_url: Dict[str, bool] = {}
        self.discover_scrapers()

    def discover_scrapers(self):
        """
        Dynamically discover and load scraper classes from the scrapers directory.
        """
        package = "comet.scrapers"
        path = os.path.dirname(__file__)

        for _, name, _ in pkgutil.iter_modules([path]):
            if name in ["base", "manager", "models"]:  # Skip base, manager, and models
                continue

            module = importlib.import_module(f"{package}.{name}")

            # Find classes inheriting from BaseScraper
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseScraper)
                    and obj is not BaseScraper
                ):
                    self.scrapers[obj.__name__] = obj
                    url_param = inspect.signature(obj.__init__).parameters.get("url")
                    self.scraper_requires_url[obj.__name__] = (
                        url_param is not None
                        and url_param.default is inspect.Parameter.empty
                    )

    def _get_scraper_setting_key(self, scraper_name: str) -> tuple:
        """
        Get the setting key and clean name for a scraper.
        
        Args:
            scraper_name: The scraper class name (e.g., "TorrentioScraper")
            
        Returns:
            Tuple of (setting_key, scraper_name_clean)
        """
        scraper_name_clean = scraper_name.replace("Scraper", "")
        setting_key = f"SCRAPE_{scraper_name_clean.upper()}"
        return setting_key, scraper_name_clean

    def get_scraper_names(self) -> list:
        """
        Get a sorted list of all available scraper names.
        Returns clean scraper names without the "Scraper" suffix.
        
        Returns:
            List of scraper names (e.g., ["Aiostreams", "Bitmagnet", ...])
        """
        return sorted([
            self._get_scraper_setting_key(name)[1]
            for name in self.scrapers.keys()
        ])

    def get_recommended_scrapers(self) -> list:
        """
        Get a list of recommended scrapers for users to enable.
        Returns scrapers that are easy to set up or commonly used.
        """
        # Prioritize scrapers that work out of the box or are commonly used
        recommended = []
        priority_scrapers = ["Torrentio", "Zilean", "Jackett", "Prowlarr"]
        
        # Create priority mapping for O(1) lookup during sorting
        priority_map = {name: i for i, name in enumerate(priority_scrapers)}
        
        for scraper_name in self.scrapers.keys():
            _, scraper_name_clean = self._get_scraper_setting_key(scraper_name)
            if scraper_name_clean in priority_scrapers:
                recommended.append(scraper_name_clean)
        
        # Return in priority order if found, otherwise return what we have
        return sorted(recommended, key=lambda x: priority_map.get(x, 999))

    def has_enabled_scrapers(self, context: str = "live", enabled_scrapers: Optional[List[str]] = None) -> bool:
        """
        Check if any scrapers are enabled for the given context.
        
        Args:
            context: The context to check ("live" or "background")
            enabled_scrapers: Optional list of user-selected scrapers from web UI
            
        Returns:
            True if at least one scraper is enabled, False otherwise
        """
        # If user explicitly selected scrapers in web UI, those are enabled
        if enabled_scrapers is not None:
            return bool(enabled_scrapers)
        
        # Otherwise, check .env settings
        for scraper_name in self.scrapers.keys():
            setting_key, scraper_name_clean = self._get_scraper_setting_key(scraper_name)
            
            if hasattr(settings, setting_key):
                if settings.is_scraper_enabled(
                    getattr(settings, setting_key), context
                ):
                    return True
        
        return False

    async def _scrape_wrapper(
        self, name: str, scraper: BaseScraper, request: ScrapeRequest
    ):
        try:
            return name, await scraper.scrape(request)
        except Exception as e:
            logger.warning(f"Scraper {name} failed: {e}")  # todo: better error handling
            return name, []

    async def scrape_all(self, request: ScrapeRequest, session: aiohttp.ClientSession):
        tasks = []
        
        # Check if any scrapers are enabled (considering both .env and user selection)
        if not self.has_enabled_scrapers(request.context, request.enabled_scrapers):
            logger.warning(
                f"No scrapers are enabled for context '{request.context}'. "
                "Please select scrapers in the web setup UI or configure at least one scraper in your .env file "
                "(e.g., SCRAPE_TORRENTIO=true, SCRAPE_ZILEAN=true, etc.) "
                "to fetch torrents. Without scrapers, no results can be found."
            )
        
        for scraper_name, scraper_class in self.scrapers.items():
            # Determine if scraper should be enabled
            # Convention: Scraper class name "NyaaScraper" -> settings.SCRAPE_NYAA
            setting_key, scraper_name_clean = self._get_scraper_setting_key(scraper_name)

            try:
                # Check if scraper is in user's selection (if specified)
                if request.enabled_scrapers is not None:
                    # User selected scrapers via web UI - only use those in the list
                    if scraper_name_clean not in request.enabled_scrapers:
                        continue
                    # This scraper is in user's selection, enable it (skip .env check)
                else:
                    # No web UI selection, check .env settings
                    if hasattr(settings, setting_key):
                        if not settings.is_scraper_enabled(
                            getattr(settings, setting_key), request.context
                        ):
                            continue
                    else:
                        logger.debug(
                            f"No {setting_key} found for {scraper_name_clean}, disabling"
                        )
                        continue

                if (
                    scraper_name == "NyaaScraper"
                    and settings.NYAA_ANIME_ONLY
                    and not anime_mapper.is_anime_content(
                        request.media_id, request.media_only_id
                    )
                ):
                    continue

                if scraper_name == "MediaFusionScraper":
                    url_credentials_pairs = associate_urls_credentials(
                        settings.MEDIAFUSION_URL, settings.MEDIAFUSION_API_PASSWORD
                    )
                    if url_credentials_pairs:
                        for i, (url, password) in enumerate(url_credentials_pairs):
                            scraper = scraper_class(self, session, url, password)
                            tasks.append(
                                self._scrape_wrapper(
                                    f"{scraper_name_clean} #{i + 1}", scraper, request
                                )
                            )

                elif scraper_name == "AiostreamsScraper":
                    url_credentials_pairs = associate_urls_credentials(
                        settings.AIOSTREAMS_URL,
                        settings.AIOSTREAMS_USER_UUID_AND_PASSWORD,
                    )
                    if url_credentials_pairs:
                        for i, (url, credentials) in enumerate(url_credentials_pairs):
                            scraper = scraper_class(self, session, url, credentials)
                            tasks.append(
                                self._scrape_wrapper(
                                    f"{scraper_name_clean} #{i + 1}", scraper, request
                                )
                            )

                else:
                    url_setting_key = f"{scraper_name_clean.upper()}_URL"
                    if scraper_name == "StremthruScraper":
                        url_setting_key = "STREMTHRU_SCRAPE_URL"

                    urls = getattr(settings, url_setting_key, None)
                    if isinstance(urls, str):
                        urls = [urls]

                    requires_url = self.scraper_requires_url.get(scraper_name, False)

                    if not urls and requires_url:
                        logger.warning(
                            f"Missing {url_setting_key} for {scraper_name_clean}, skipping scraper"
                        )
                        continue

                    if urls:
                        for i, url in enumerate(urls):
                            scraper = scraper_class(self, session, url)
                            tasks.append(
                                self._scrape_wrapper(
                                    f"{scraper_name_clean} #{i + 1}", scraper, request
                                )
                            )
                    else:
                        scraper = scraper_class(self, session)
                        tasks.append(
                            self._scrape_wrapper(scraper_name_clean, scraper, request)
                        )
            except Exception as e:
                logger.warning(
                    f"Skipping {scraper_name_clean} due to initialization error: {e}"
                )

        for future in asyncio.as_completed(tasks):
            try:
                yield await future
            except Exception as e:
                logger.error(
                    f"Error during scraping: {e}"
                )  # todo: better error handling


scraper_manager = ScraperManager()
