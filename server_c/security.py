import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}


class UnsafeTarget(ValueError):
    pass


def validate_public_url(value, resolver=socket.getaddrinfo):
    parsed = urlparse(value)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.hostname or parsed.username or parsed.password:
        raise UnsafeTarget("unsupported_or_credentialed_url")
    if parsed.port not in (None, 80, 443):
        raise UnsafeTarget("unsupported_port")
    try:
        addresses = {item[4][0] for item in resolver(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise UnsafeTarget("unresolvable_host") from exc
    if not addresses:
        raise UnsafeTarget("unresolvable_host")
    for raw in addresses:
        address = ipaddress.ip_address(raw)
        if not address.is_global:
            raise UnsafeTarget("private_or_special_address")
    return value
