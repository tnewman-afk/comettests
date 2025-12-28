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


def get_base_url(request: Request) -> str:
    """
    Get the base URL to use for addon URLs (manifest, streams, etc.).
    
    This ensures that URLs are always accessible from other devices on the network,
    not just from localhost.
    
    Priority:
    1. PUBLIC_BASE_URL environment variable (if set)
    2. Request hostname if it's not localhost/wildcard
    3. Detected LAN IP as fallback
    4. Request origin as final fallback
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Base URL string (e.g., "http://192.168.1.10:8000")
    """
    from comet.core.models import settings
    
    # First priority: use PUBLIC_BASE_URL if configured
    if settings.PUBLIC_BASE_URL:
        return settings.PUBLIC_BASE_URL.rstrip("/")
    
    # Get request hostname
    request_host = request.url.hostname or "localhost"
    request_port = request.url.port
    
    # If request is not from localhost/wildcard, use it
    if request_host not in (LOOPBACK_HOSTS | WILDCARD_HOSTS):
        port_str = f":{request_port}" if request_port and request_port not in (80, 443) else ""
        return f"{request.url.scheme}://{request_host}{port_str}"
    
    # Fallback to detected LAN IP
    detected_ip = auto_detect_lan_ip()
    if detected_ip:
        port_str = f":{request_port}" if request_port and request_port not in (80, 443) else ""
        return f"{request.url.scheme}://{detected_ip}{port_str}"
    
    # Final fallback: use request origin as-is
    return f"{request.url.scheme}://{request.url.netloc}"


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
