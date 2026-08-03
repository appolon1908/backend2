import ipaddress
import socket
from urllib.parse import urlparse

from rest_framework import serializers


def validate_webhook_url(value, allow_local=False):
    parsed = urlparse(value)
    if parsed.scheme not in ({"http", "https"} if allow_local else {"https"}) or not parsed.hostname:
        raise serializers.ValidationError("Webhook URL must use HTTPS.")
    host = parsed.hostname.lower().rstrip(".")
    blocked_names = {"localhost", "metadata.google.internal", "169.254.169.254", "metadata"}
    if host in blocked_names:
        raise serializers.ValidationError("Private and metadata destinations are not allowed.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)}
    except socket.gaierror:
        addresses = set()
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified) and not allow_local:
            raise serializers.ValidationError("Private and metadata destinations are not allowed.")
    return True
