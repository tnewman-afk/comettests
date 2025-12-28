import ipaddress
import socket
from functools import lru_cache

import aiohttp
from fastapi import Request

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}

WILDCARD_HOSTS = {"0.0.0.0", "::", "[::]"}
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


@lru_cache(maxsize=1)
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


def get_client_ip(request: Request):
    return (
        request.headers["cf-connecting-ip"]
        if "cf-connecting-ip" in request.headers
        else request.client.host
    )


async def fetch_with_proxy_fallback(
    session: aiohttp.ClientSession, url: str, headers: dict = None, params: dict = None
):
    from comet.core.models import settings

    try:
        async with session.get(url, headers=headers, params=params) as response:
            return await response.json()
    except Exception as first_error:
        if settings.BYPASS_PROXY_URL:
            try:
                async with session.get(
                    url,
                    headers=headers,
                    proxy=settings.BYPASS_PROXY_URL,
                    params=params,
                ) as response:
                    return await response.json()
            except Exception as second_error:
                raise second_error
        else:
            raise first_error
