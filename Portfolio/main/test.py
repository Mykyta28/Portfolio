import logging
import platform
import socket
import ssl
import smtplib
import sys
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django import get_version as django_version
from django.conf import settings
from django.shortcuts import render


logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

SITES = [
    ("Google", "https://www.google.com"),
    ("Cloudflare", "https://www.cloudflare.com"),
    ("Microsoft", "https://www.microsoft.com"),
    ("Amazon", "https://www.amazon.com"),
    ("Apple", "https://www.apple.com"),
    ("GitHub", "https://github.com"),
    ("Wikipedia", "https://www.wikipedia.org"),
    ("OpenAI", "https://www.openai.com"),
    ("Mozilla", "https://www.mozilla.org"),
    ("Python", "https://www.python.org"),
]


# ============================================================
# VIEW
# ============================================================

def test(request):

    logs = []

    site_results = []
    smtp_result = {}

    started_at = time.time()

    # ========================================================
    # LOGGER
    # ========================================================

    def add_log(message, level="INFO"):
        timestamp = time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        line = f"[{timestamp}] [{level}] {message}"

        logs.append(line)

        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

    # ========================================================
    # BASIC ENVIRONMENT INFORMATION
    # ========================================================

    add_log("=" * 80)
    add_log("SYSTEM DIAGNOSTIC STARTED")
    add_log("=" * 80)

    add_log(f"Python version: {sys.version}")
    add_log(f"Python executable: {sys.executable}")
    add_log(f"Platform: {platform.platform()}")
    add_log(f"OS: {platform.system()} {platform.release()}")
    add_log(f"Architecture: {platform.machine()}")
    add_log(f"OpenSSL: {ssl.OPENSSL_VERSION}")
    add_log(f"SSL version: {ssl.OPENSSL_VERSION}")
    add_log(f"TLS 1.2 available: {hasattr(ssl.TLSVersion, 'TLSv1_2')}")
    add_log(f"TLS 1.3 available: {hasattr(ssl.TLSVersion, 'TLSv1_3')}")
    add_log(f"Django version: {django_version()}")

    # ========================================================
    # EMAIL SETTINGS
    # ========================================================

    smtp_host = getattr(
        settings,
        "EMAIL_HOST",
        "smtp.gmail.com",
    )

    smtp_port = getattr(
        settings,
        "EMAIL_PORT",
        587,
    )

    smtp_user = getattr(
        settings,
        "EMAIL_HOST_USER",
        "",
    )

    smtp_password = getattr(
        settings,
        "EMAIL_HOST_PASSWORD",
        "",
    )

    smtp_use_tls = getattr(
        settings,
        "EMAIL_USE_TLS",
        True,
    )

    smtp_timeout = getattr(
        settings,
        "EMAIL_TIMEOUT",
        10,
    )

    add_log("=" * 80)
    add_log("CONFIGURATION")
    add_log("=" * 80)

    add_log(f"EMAIL_HOST: {smtp_host}")
    add_log(f"EMAIL_PORT: {smtp_port}")
    add_log(f"EMAIL_USE_TLS: {smtp_use_tls}")
    add_log(f"EMAIL_TIMEOUT: {smtp_timeout}")
    add_log(f"EMAIL_HOST_USER: {smtp_user}")

    if smtp_password:
        add_log("EMAIL_HOST_PASSWORD: configured")
    else:
        add_log(
            "EMAIL_HOST_PASSWORD: EMPTY",
            "WARNING",
        )

    # ========================================================
    # DNS RESOLUTION
    # ========================================================

    def resolve_hostname(hostname, port=443):

        result = {
            "hostname": hostname,
            "ipv4": [],
            "ipv6": [],
            "all": [],
            "errors": [],
        }

        try:
            addresses = socket.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )

            seen = set()

            for family, socktype, proto, canonname, sockaddr in addresses:

                ip = sockaddr[0]

                if ip in seen:
                    continue

                seen.add(ip)

                result["all"].append(ip)

                if family == socket.AF_INET:
                    result["ipv4"].append(ip)

                elif family == socket.AF_INET6:
                    result["ipv6"].append(ip)

        except Exception as exc:

            result["errors"].append(
                f"{type(exc).__name__}: {exc}"
            )

        return result

    # ========================================================
    # TCP TEST
    # ========================================================

    def tcp_test(host, port, ip, family):

        result = {
            "ip": ip,
            "port": port,
            "family": family,
            "success": False,
            "duration": None,
            "error": None,
        }

        sock = None

        try:

            family_name = (
                "IPv4"
                if family == socket.AF_INET
                else "IPv6"
            )

            start = time.perf_counter()

            sock = socket.socket(
                family,
                socket.SOCK_STREAM,
            )

            sock.settimeout(5)

            if family == socket.AF_INET:

                sock.connect(
                    (ip, port)
                )

            else:

                sock.connect(
                    (ip, port, 0, 0)
                )

            duration = (
                time.perf_counter() - start
            )

            result["success"] = True
            result["duration"] = duration

            add_log(
                f"TCP {family_name} {host}:{port} "
                f"-> {ip} OK ({duration:.3f}s)"
            )

        except Exception as exc:

            result["error"] = (
                f"{type(exc).__name__}: {exc}"
            )

            family_name = (
                "IPv4"
                if family == socket.AF_INET
                else "IPv6"
            )

            add_log(
                f"TCP {family_name} {host}:{port} "
                f"-> {ip} FAILED: "
                f"{type(exc).__name__}: {exc}",
                "ERROR",
            )

        finally:

            if sock is not None:

                try:
                    sock.close()
                except Exception:
                    pass

        return result

    # ========================================================
    # WEBSITE TEST
    # ========================================================

    def check_site(name, url):

        result = {
            "name": name,
            "url": url,

            "dns_ok": False,

            "ipv4": [],
            "ipv6": [],
            "all_ips": [],

            "tcp_ipv4": [],
            "tcp_ipv6": [],

            "https_ok": False,
            "http_status": None,
            "response_time": None,

            "error": None,
        }

        hostname = (
            url
            .split("://", 1)[1]
            .split("/", 1)[0]
        )

        add_log(
            f"Starting check: "
            f"{name} ({url})"
        )

        # ----------------------------------------------------
        # DNS
        # ----------------------------------------------------

        dns_start = time.perf_counter()

        dns = resolve_hostname(
            hostname,
            443,
        )

        dns_time = (
            time.perf_counter() - dns_start
        )

        result["ipv4"] = dns["ipv4"]
        result["ipv6"] = dns["ipv6"]
        result["all_ips"] = dns["all"]

        if dns["all"]:

            result["dns_ok"] = True

            add_log(
                f"{name}: DNS OK "
                f"({dns_time:.3f}s)"
            )

            if result["ipv4"]:

                add_log(
                    f"{name}: IPv4 -> "
                    f"{', '.join(result['ipv4'])}"
                )

            if result["ipv6"]:

                add_log(
                    f"{name}: IPv6 -> "
                    f"{', '.join(result['ipv6'])}"
                )

        else:

            error = (
                "; ".join(dns["errors"])
                if dns["errors"]
                else "No addresses returned"
            )

            result["error"] = (
                f"DNS failed: {error}"
            )

            add_log(
                f"{name}: DNS FAILED -> {error}",
                "ERROR",
            )

            return result

        # ----------------------------------------------------
        # TCP IPv4
        # ----------------------------------------------------

        for ip in result["ipv4"][:3]:

            tcp = tcp_test(
                hostname,
                443,
                ip,
                socket.AF_INET,
            )

            result["tcp_ipv4"].append(tcp)

        # ----------------------------------------------------
        # TCP IPv6
        # ----------------------------------------------------

        for ip in result["ipv6"][:3]:

            tcp = tcp_test(
                hostname,
                443,
                ip,
                socket.AF_INET6,
            )

            result["tcp_ipv6"].append(tcp)

        # ----------------------------------------------------
        # HTTPS
        # ----------------------------------------------------

        try:

            request_obj = Request(
                url,
                headers={
                    "User-Agent": (
                        "DjangoConnectivityTest/1.0"
                    )
                },
                method="GET",
            )

            start = time.perf_counter()

            with urlopen(
                request_obj,
                timeout=5,
            ) as response:

                # Only read a tiny portion.
                response.read(1024)

                duration = (
                    time.perf_counter() - start
                )

                result["https_ok"] = True
                result["http_status"] = response.status
                result["response_time"] = duration

                add_log(
                    f"{name}: HTTPS OK -> "
                    f"HTTP {response.status} "
                    f"({duration:.3f}s)"
                )

        except HTTPError as exc:

            duration = (
                time.perf_counter() - start
            )

            # An HTTP error still proves that
            # DNS + TCP + TLS + HTTP worked.
            result["https_ok"] = True
            result["http_status"] = exc.code
            result["response_time"] = duration

            add_log(
                f"{name}: HTTPS reachable -> "
                f"HTTP {exc.code} "
                f"({duration:.3f}s)",
                "WARNING",
            )

        except (URLError, socket.timeout) as exc:

            result["error"] = (
                f"{type(exc).__name__}: {exc}"
            )

            add_log(
                f"{name}: HTTPS FAILED -> "
                f"{type(exc).__name__}: {exc}",
                "ERROR",
            )

        except Exception as exc:

            result["error"] = (
                f"{type(exc).__name__}: {exc}"
            )

            add_log(
                f"{name}: HTTPS ERROR -> "
                f"{type(exc).__name__}: {exc}",
                "ERROR",
            )

        return result

    # ========================================================
    # INTERNET TEST
    # ========================================================

    add_log("=" * 80)
    add_log("STARTING INTERNET CONNECTIVITY TEST")
    add_log("=" * 80)

    internet_start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=len(SITES)
    ) as executor:

        futures = {
            executor.submit(
                check_site,
                name,
                url,
            ): (name, url)

            for name, url in SITES
        }

        for future in as_completed(futures):

            name, url = futures[future]

            try:

                result = future.result()

                site_results.append(result)

            except Exception as exc:

                add_log(
                    f"{name}: unexpected error -> "
                    f"{type(exc).__name__}: {exc}",
                    "ERROR",
                )

                site_results.append({
                    "name": name,
                    "url": url,
                    "dns_ok": False,
                    "ipv4": [],
                    "ipv6": [],
                    "all_ips": [],
                    "tcp_ipv4": [],
                    "tcp_ipv6": [],
                    "https_ok": False,
                    "http_status": None,
                    "response_time": None,
                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                })

    # Restore original order.
    order = {
        name: index
        for index, (name, _) in enumerate(SITES)
    }

    site_results.sort(
        key=lambda item: order[item["name"]]
    )

    internet_duration = (
        time.perf_counter() - internet_start
    )

    internet_success = sum(
        1
        for site in site_results
        if site["dns_ok"]
        and site["https_ok"]
    )

    add_log(
        f"Internet test completed: "
        f"{internet_success}/{len(SITES)} sites "
        f"reachable in "
        f"{internet_duration:.3f}s"
    )

    # ========================================================
    # SMTP TEST
    # ========================================================

    add_log("=" * 80)
    add_log("STARTING SMTP TEST")
    add_log("=" * 80)

    smtp_result = {
        "host": smtp_host,
        "port": smtp_port,
        "user": smtp_user,
        "tls_required": smtp_use_tls,

        "dns_ok": False,

        "ipv4": [],
        "ipv6": [],

        "tcp_ipv4": [],
        "tcp_ipv6": [],

        "connection": False,
        "greeting": False,
        "ehlo": False,

        "extensions": [],

        "starttls": False,
        "tls_version": None,
        "tls_cipher": None,
        "tls_peer": None,

        "auth": False,

        "error": None,
    }

    # --------------------------------------------------------
    # SMTP DNS
    # --------------------------------------------------------

    add_log(
        f"Resolving SMTP host: {smtp_host}"
    )

    smtp_dns = resolve_hostname(
        smtp_host,
        smtp_port,
    )

    smtp_result["ipv4"] = smtp_dns["ipv4"]
    smtp_result["ipv6"] = smtp_dns["ipv6"]

    if smtp_dns["all"]:

        smtp_result["dns_ok"] = True

        add_log(
            f"SMTP DNS OK: "
            f"{', '.join(smtp_dns['all'])}"
        )

    else:

        error = (
            "; ".join(smtp_dns["errors"])
            if smtp_dns["errors"]
            else "No addresses returned"
        )

        smtp_result["error"] = (
            f"SMTP DNS failed: {error}"
        )

        add_log(
            f"SMTP DNS FAILED: {error}",
            "ERROR",
        )

    # --------------------------------------------------------
    # SMTP TCP IPv4
    # --------------------------------------------------------

    if smtp_result["dns_ok"]:

        for ip in smtp_result["ipv4"][:3]:

            tcp = tcp_test(
                smtp_host,
                smtp_port,
                ip,
                socket.AF_INET,
            )

            smtp_result["tcp_ipv4"].append(tcp)

        # ----------------------------------------------------
        # SMTP TCP IPv6
        # ----------------------------------------------------

        for ip in smtp_result["ipv6"][:3]:

            tcp = tcp_test(
                smtp_host,
                smtp_port,
                ip,
                socket.AF_INET6,
            )

            smtp_result["tcp_ipv6"].append(tcp)

    # --------------------------------------------------------
    # REAL SMTP TEST
    # --------------------------------------------------------

    if smtp_result["dns_ok"]:

        smtp = None

        try:

            add_log(
                f"Creating SMTP client for "
                f"{smtp_host}:{smtp_port}"
            )

            # IMPORTANT:
            # Pass host directly to SMTP().
            #
            # This ensures smtplib stores the hostname
            # internally and STARTTLS can use it as
            # server_hostname for TLS/SNI.
            smtp = smtplib.SMTP(
                smtp_host,
                smtp_port,
                timeout=smtp_timeout,
            )

            smtp_result["connection"] = True

            add_log(
                "SMTP TCP connection established"
            )

            # ------------------------------------------------
            # Greeting
            # ------------------------------------------------

            greeting_code = smtp.noop()[0]

            # NOOP isn't the greeting, so rely on
            # the connect() success code exposed
            # by smtplib internally.
            #
            # A successful SMTP() construction means
            # the server already sent 220.

            smtp_result["greeting"] = True

            add_log(
                f"SMTP server greeting received "
                f"(SMTP client connected successfully)"
            )

            add_log(
                f"SMTP NOOP response: "
                f"{greeting_code}"
            )

            # ------------------------------------------------
            # EHLO
            # ------------------------------------------------

            ehlo_code, ehlo_message = smtp.ehlo()

            add_log(
                f"EHLO response: "
                f"{ehlo_code} "
                f"{ehlo_message!r}"
            )

            if ehlo_code == 250:

                smtp_result["ehlo"] = True

                smtp_result["extensions"] = list(
                    smtp.esmtp_features.keys()
                )

                add_log(
                    "EHLO OK"
                )

                add_log(
                    "SMTP extensions: "
                    f"{smtp_result['extensions']}"
                )

            else:

                add_log(
                    "EHLO FAILED",
                    "ERROR",
                )

            # ------------------------------------------------
            # STARTTLS
            # ------------------------------------------------

            if smtp_use_tls:

                if "starttls" not in smtp.esmtp_features:

                    add_log(
                        "SMTP server does NOT "
                        "advertise STARTTLS",
                        "ERROR",
                    )

                else:

                    add_log(
                        "SMTP server supports STARTTLS"
                    )

                    try:

                        tls_context = (
                            ssl.create_default_context()
                        )

                        add_log(
                            "TLS context created"
                        )

                        add_log(
                            f"TLS check_hostname: "
                            f"{tls_context.check_hostname}"
                        )

                        add_log(
                            f"TLS verify_mode: "
                            f"{tls_context.verify_mode}"
                        )

                        tls_start = time.perf_counter()

                        tls_code, tls_message = (
                            smtp.starttls(
                                context=tls_context
                            )
                        )

                        tls_duration = (
                            time.perf_counter()
                            - tls_start
                        )

                        add_log(
                            f"STARTTLS response: "
                            f"{tls_code} "
                            f"{tls_message!r}"
                        )

                        add_log(
                            f"TLS negotiation time: "
                            f"{tls_duration:.3f}s"
                        )

                        if tls_code == 220:

                            smtp_result["starttls"] = True

                            add_log(
                                "STARTTLS SUCCESS"
                            )

                            # --------------------------------
                            # TLS INFORMATION
                            # --------------------------------

                            if smtp.sock:

                                try:

                                    version = (
                                        smtp.sock.version()
                                    )

                                    cipher = (
                                        smtp.sock.cipher()
                                    )

                                    peer = (
                                        smtp.sock.getpeercert()
                                    )

                                    smtp_result[
                                        "tls_version"
                                    ] = version

                                    smtp_result[
                                        "tls_cipher"
                                    ] = cipher

                                    smtp_result[
                                        "tls_peer"
                                    ] = peer

                                    add_log(
                                        f"TLS version: "
                                        f"{version}"
                                    )

                                    add_log(
                                        f"TLS cipher: "
                                        f"{cipher}"
                                    )

                                    if peer:

                                        subject = peer.get(
                                            "subject",
                                            ()
                                        )

                                        issuer = peer.get(
                                            "issuer",
                                            ()
                                        )

                                        add_log(
                                            f"TLS certificate "
                                            f"subject: {subject}"
                                        )

                                        add_log(
                                            f"TLS certificate "
                                            f"issuer: {issuer}"
                                        )

                                except Exception as exc:

                                    add_log(
                                        f"Unable to inspect "
                                        f"TLS socket: "
                                        f"{type(exc).__name__}: "
                                        f"{exc}",
                                        "WARNING",
                                    )

                            # --------------------------------
                            # EHLO AFTER TLS
                            # --------------------------------

                            ehlo2_code, ehlo2_message = (
                                smtp.ehlo()
                            )

                            add_log(
                                f"EHLO after TLS: "
                                f"{ehlo2_code} "
                                f"{ehlo2_message!r}"
                            )

                            if ehlo2_code != 250:

                                add_log(
                                    "EHLO after TLS FAILED",
                                    "ERROR",
                                )

                        else:

                            add_log(
                                "STARTTLS FAILED",
                                "ERROR",
                            )

                    except ssl.SSLCertVerificationError as exc:

                        smtp_result["error"] = (
                            f"TLS certificate verification "
                            f"failed: {exc}"
                        )

                        add_log(
                            "TLS CERTIFICATE VERIFICATION "
                            "FAILED",
                            "ERROR",
                        )

                        add_log(
                            f"Certificate error: {exc}",
                            "ERROR",
                        )

                    except ssl.SSLError as exc:

                        smtp_result["error"] = (
                            f"SSL error: {exc}"
                        )

                        add_log(
                            f"SSL ERROR: "
                            f"{type(exc).__name__}: {exc}",
                            "ERROR",
                        )

                    except ValueError as exc:

                        smtp_result["error"] = (
                            f"TLS configuration error: {exc}"
                        )

                        add_log(
                            f"TLS VALUE ERROR: {exc}",
                            "ERROR",
                        )

                    except Exception as exc:

                        smtp_result["error"] = (
                            f"STARTTLS error: "
                            f"{type(exc).__name__}: {exc}"
                        )

                        add_log(
                            f"STARTTLS ERROR: "
                            f"{type(exc).__name__}: "
                            f"{exc}",
                            "ERROR",
                        )

            # ------------------------------------------------
            # SMTP AUTHENTICATION
            # ------------------------------------------------

            if (
                smtp_result["starttls"]
                and smtp_user
                and smtp_password
            ):

                add_log(
                    f"Attempting SMTP authentication "
                    f"as {smtp_user}"
                )

                try:

                    smtp.login(
                        smtp_user,
                        smtp_password,
                    )

                    smtp_result["auth"] = True

                    add_log(
                        "SMTP AUTHENTICATION SUCCESS"
                    )

                except smtplib.SMTPAuthenticationError as exc:

                    smtp_result["error"] = (
                        f"SMTP authentication failed: "
                        f"{exc.smtp_code} "
                        f"{exc.smtp_error!r}"
                    )

                    add_log(
                        f"SMTP AUTH FAILED: "
                        f"code={exc.smtp_code}, "
                        f"message={exc.smtp_error!r}",
                        "ERROR",
                    )

                except smtplib.SMTPException as exc:

                    smtp_result["error"] = (
                        f"SMTP auth error: {exc}"
                    )

                    add_log(
                        f"SMTP AUTH ERROR: "
                        f"{type(exc).__name__}: "
                        f"{exc}",
                        "ERROR",
                    )

                except Exception as exc:

                    smtp_result["error"] = (
                        f"AUTH error: "
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )

                    add_log(
                        f"SMTP AUTH ERROR: "
                        f"{type(exc).__name__}: "
                        f"{exc}",
                        "ERROR",
                    )

            elif smtp_result["starttls"]:

                add_log(
                    "SMTP AUTH skipped: "
                    "username or password is empty",
                    "WARNING",
                )

        except smtplib.SMTPConnectError as exc:

            smtp_result["error"] = (
                f"SMTP connection error: "
                f"{exc}"
            )

            add_log(
                f"SMTP CONNECTION ERROR: "
                f"{exc}",
                "ERROR",
            )

        except socket.timeout as exc:

            smtp_result["error"] = (
                f"SMTP timeout: {exc}"
            )

            add_log(
                "SMTP CONNECTION TIMEOUT",
                "ERROR",
            )

        except OSError as exc:

            smtp_result["error"] = (
                f"Network error: "
                f"{type(exc).__name__}: {exc}"
            )

            add_log(
                f"SMTP NETWORK ERROR: "
                f"{type(exc).__name__}: "
                f"{exc}",
                "ERROR",
            )

        except Exception as exc:

            smtp_result["error"] = (
                f"Unexpected SMTP error: "
                f"{type(exc).__name__}: {exc}"
            )

            add_log(
                f"UNEXPECTED SMTP ERROR: "
                f"{type(exc).__name__}: "
                f"{exc}",
                "ERROR",
            )

        finally:

            if smtp is not None:

                try:

                    smtp.quit()

                    add_log(
                        "SMTP connection closed"
                    )

                except Exception as exc:

                    add_log(
                        f"SMTP close warning: "
                        f"{type(exc).__name__}: "
                        f"{exc}",
                        "WARNING",
                    )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    smtp_network_ok = (
        smtp_result["dns_ok"]
        and (
            any(
                item["success"]
                for item in smtp_result["tcp_ipv4"]
            )
            or any(
                item["success"]
                for item in smtp_result["tcp_ipv6"]
            )
        )
        and smtp_result["connection"]
        and smtp_result["greeting"]
        and smtp_result["ehlo"]
    )

    smtp_ok = (
        smtp_network_ok
        and (
            not smtp_use_tls
            or smtp_result["starttls"]
        )
        and smtp_result["auth"]
    )

    overall_ok = (
        internet_success > 0
        and smtp_ok
    )

    total_duration = (
        time.time() - started_at
    )

    add_log("=" * 80)

    if overall_ok:

        add_log(
            "OVERALL RESULT: ALL TESTS PASSED"
        )

    else:

        add_log(
            "OVERALL RESULT: SOME TESTS FAILED",
            "ERROR",
        )

    add_log(
        f"Total diagnostic time: "
        f"{total_duration:.3f}s"
    )

    add_log("=" * 80)

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        "test.html",
        {
            "logs": logs,
            "site_results": site_results,
            "smtp_result": smtp_result,

            "internet_success": internet_success,
            "internet_total": len(SITES),

            "internet_ok": internet_success > 0,
            "smtp_network_ok": smtp_network_ok,
            "smtp_ok": smtp_ok,
            "overall_ok": overall_ok,

            "total_duration": total_duration,
        },
    )