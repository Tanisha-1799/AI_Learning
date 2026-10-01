"""Centralized SSL/network configuration for OpenAI and embedding calls."""
from dataclasses import dataclass
import os
import platform
import ssl
from urllib.parse import urlparse

import httpx


@dataclass
class NetworkSettings:
    ca_bundle: str | None
    allow_insecure_ssl: bool
    proxy_url: str | None
    base_url: str | None
    timeout_sec: float
    max_retries: int
    use_system_cert_store: bool


def _normalize_proxy_url(proxy_value: str | None) -> str | None:
    if not proxy_value:
        return None
    proxy_value = proxy_value.strip()
    if not proxy_value:
        return None
    parsed = urlparse(proxy_value)
    if parsed.scheme:
        return proxy_value
    return f"http://{proxy_value}"


def _detect_windows_proxy() -> str | None:
    """Best-effort detection of Windows user proxy settings when env vars are absent."""
    if platform.system().lower() != "windows":
        return None
    try:
        import winreg

        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if int(enabled) != 1:
                return None
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
    except Exception:
        return None

    if not server:
        return None

    server = str(server).strip()
    if not server:
        return None

    if ";" in server or "=" in server:
        parts = [p.strip() for p in server.split(";") if p.strip()]
        for part in parts:
            if "=" not in part:
                continue
            proto, value = part.split("=", 1)
            if proto.strip().lower() == "https":
                return _normalize_proxy_url(value)
        for part in parts:
            if "=" not in part:
                continue
            _, value = part.split("=", 1)
            if value.strip():
                return _normalize_proxy_url(value)
        return None

    return _normalize_proxy_url(server)


def load_network_settings() -> NetworkSettings:
    ca_bundle = os.getenv("OPENAI_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    allow_insecure_ssl = os.getenv("ALLOW_INSECURE_SSL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    proxy_url = (
        os.getenv("OPENAI_PROXY")
        or os.getenv("HTTPS_PROXY")
        or os.getenv("https_proxy")
        or os.getenv("HTTP_PROXY")
        or os.getenv("http_proxy")
        or os.getenv("ALL_PROXY")
        or os.getenv("all_proxy")
    )
    proxy_url = _normalize_proxy_url(proxy_url) or _detect_windows_proxy()
    base_url = os.getenv("OPENAI_BASE_URL")

    timeout_raw = os.getenv("OPENAI_TIMEOUT_SEC", "60")
    retries_raw = os.getenv("OPENAI_MAX_RETRIES", "2")
    use_system_cert_store = os.getenv("OPENAI_USE_SYSTEM_CERT_STORE", "true").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    try:
        timeout_sec = float(timeout_raw)
    except ValueError:
        timeout_sec = 60.0

    try:
        max_retries = int(retries_raw)
    except ValueError:
        max_retries = 2

    if ca_bundle and not os.path.isfile(ca_bundle):
        print(f"WARNING: CA bundle path does not exist: {ca_bundle}")
        print("         Falling back to default TLS trust store for this run.")
        ca_bundle = None

    if ca_bundle:
        os.environ["SSL_CERT_FILE"] = ca_bundle
        os.environ["REQUESTS_CA_BUNDLE"] = ca_bundle
        os.environ["CURL_CA_BUNDLE"] = ca_bundle

    return NetworkSettings(
        ca_bundle=ca_bundle,
        allow_insecure_ssl=allow_insecure_ssl,
        proxy_url=proxy_url,
        base_url=base_url,
        timeout_sec=timeout_sec,
        max_retries=max_retries,
        use_system_cert_store=use_system_cert_store,
    )


def create_http_client(settings: NetworkSettings) -> httpx.Client:
    verify_setting = settings.ca_bundle if settings.ca_bundle else (False if settings.allow_insecure_ssl else True)

    if (
        settings.use_system_cert_store
        and not settings.ca_bundle
        and not settings.allow_insecure_ssl
    ):
        try:
            import truststore

            verify_setting = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except Exception:
            verify_setting = True

    if settings.allow_insecure_ssl:
        print("WARNING: SSL certificate verification is disabled (ALLOW_INSECURE_SSL=true).")
        print("         Use this only for local debugging and never in production.\n")

    kwargs = {
        "verify": verify_setting,
        "timeout": settings.timeout_sec,
        "trust_env": True,
        "follow_redirects": True,
    }
    if settings.proxy_url:
        kwargs["proxy"] = settings.proxy_url

    return httpx.Client(**kwargs)


def print_network_summary(settings: NetworkSettings) -> None:
    print("Network config summary:")
    print(f"  OPENAI_BASE_URL      : {settings.base_url or '(default)'}")
    print(f"  OPENAI_CA_BUNDLE     : {settings.ca_bundle or '(not set)'}")
    print(f"  OPENAI_PROXY/HTTPS_PROXY: {settings.proxy_url or '(not set)'}")
    print(f"  ALLOW_INSECURE_SSL   : {settings.allow_insecure_ssl}")
    print(f"  OPENAI_USE_SYSTEM_CERT_STORE: {settings.use_system_cert_store}")
    print(f"  OPENAI_TIMEOUT_SEC   : {settings.timeout_sec}")
    print(f"  OPENAI_MAX_RETRIES   : {settings.max_retries}")


def print_connection_guidance() -> None:
    print("Troubleshooting checklist:")
    print("  1) Set OPENAI_CA_BUNDLE to your corporate root CA PEM file.")
    print("  2) If your network requires proxy, set OPENAI_PROXY or HTTPS_PROXY.")
    print("  3) If using a gateway endpoint, set OPENAI_BASE_URL.")
    print("  4) Keep OPENAI_USE_SYSTEM_CERT_STORE=true to use OS trust roots.")
    print("  5) Raise OPENAI_TIMEOUT_SEC (for slow networks) and OPENAI_MAX_RETRIES.")
    print("  6) For local-only testing, ALLOW_INSECURE_SSL=true (unsafe).")


def describe_exception(exc: Exception) -> str:
    """Return nested cause/context details for connection errors."""
    parts = [f"{type(exc).__name__}: {exc}"]
    cause = getattr(exc, "__cause__", None)
    context = getattr(exc, "__context__", None)
    if cause is not None:
        parts.append(f"Caused by {type(cause).__name__}: {cause}")
    if context is not None and context is not cause:
        parts.append(f"Context {type(context).__name__}: {context}")
    return " | ".join(parts)