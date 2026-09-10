"""Complete the bulletin host's omitted intermediate chain without bypassing TLS."""

import ssl
from pathlib import Path

from requests.certs import where


def bulletin_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=where())
    context.load_verify_locations(
        cafile=Path(__file__).parent / "certificates/globalsign-rsa-ov-2018.pem"
    )
    return context
