import ipaddress
import re
from urllib.parse import urlparse
from typing import Optional, Tuple
import httpx
import socket


BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

MAX_CONTENT_SIZE = 5 * 1024 * 1024
REQUEST_TIMEOUT = 30
MAX_REDIRECTS = 5


class SSRFError(Exception):
    pass


def is_ip_blocked(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        for blocked_range in BLOCKED_IP_RANGES:
            if ip in blocked_range:
                return True
        return False
    except ValueError:
        return True


def validate_url(url: str) -> Tuple[bool, str]:
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in ("http", "https"):
            return False, "Only HTTP and HTTPS URLs are allowed"
        
        if not parsed.netloc:
            return False, "Invalid URL: no host specified"
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: no hostname"
        
        blocked_patterns = [
            r"localhost",
            r"127\.\d+\.\d+\.\d+",
            r"0\.0\.0\.0",
            r"::1",
            r"metadata\.google",
            r"169\.254\.\d+\.\d+",
        ]
        
        for pattern in blocked_patterns:
            if re.search(pattern, hostname, re.IGNORECASE):
                return False, f"Blocked hostname pattern: {hostname}"
        
        try:
            ip_addresses = socket.getaddrinfo(hostname, None)
            for addr_info in ip_addresses:
                ip_str = addr_info[4][0]
                if is_ip_blocked(ip_str):
                    return False, f"Blocked IP address: {ip_str}"
        except socket.gaierror:
            pass
        
        return True, "OK"
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


async def fetch_url(url: str) -> Tuple[bool, str, Optional[str]]:
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        return False, error_msg, None
    
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
        ) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "URLWatchdog/1.0 (Monitoring Service)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
            )
            
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_CONTENT_SIZE:
                return False, f"Content too large: {content_length} bytes", None
            
            content = response.text[:MAX_CONTENT_SIZE]
            
            return True, "OK", content
            
    except httpx.TimeoutException:
        return False, "Request timed out", None
    except httpx.TooManyRedirects:
        return False, "Too many redirects", None
    except httpx.RequestError as e:
        return False, f"Request error: {str(e)}", None
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", None


def check_keywords(content: str, keywords: list[str]) -> list[str]:
    matched = []
    content_lower = content.lower()
    for keyword in keywords:
        if keyword.lower() in content_lower:
            matched.append(keyword)
    return matched
