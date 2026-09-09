"""Best-effort online validation that a translated package name actually
exists for the target distro.

Repology (repology.org) is the primary source: it already aggregates
package presence across every distro we care about, so one query tells us
whether a name is right instead of trusting a hand-maintained table
blindly. When Repology has no data at all for a package, we fall back to a
couple of official per-distro APIs that have clean JSON responses (Arch,
Fedora/RHEL). Everything is cached on disk and every network failure
degrades to "unknown" -- this can only add information to the generated
script, it must never block or fail the tool.
"""
import json
import os
import time
import urllib.error
import urllib.request

from . import mapping

CACHE_PATH = os.path.expanduser("~/.cache/movout/pkg_validate.json")
CACHE_TTL = 30 * 24 * 3600  # 30 days -- package availability rarely churns
REQUEST_TIMEOUT = 5
USER_AGENT = "MovingOut/pkgvalidate (+https://github.com/AntonioNappi988/MovingOut)"

# Repology repo-id prefixes for each family. Broad on purpose (no pinned
# version) so a hit on any reasonably current release of that family counts.
REPOLOGY_FAMILY_PREFIXES = {
    "debian": ("debian_", "ubuntu_", "raspbian_", "devuan_", "mx_", "kali_", "pureos_"),
    "fedora": ("fedora_",),
    "rhel": ("epel_", "rpmfusion_el_", "openeuler_"),
    "arch": ("arch", "manjaro_", "endeavouros", "archpower_"),
    "suse": ("opensuse_",),
    "alpine": ("alpine_",),
}
_ALL_KNOWN_PREFIXES = tuple(p for prefixes in REPOLOGY_FAMILY_PREFIXES.values() for p in prefixes)

# Consecutive network-level failures (DNS/connect/timeout, not "not found")
# after which we stop hitting the network for the rest of this batch and
# just mark everything left as "unknown" -- avoids hanging for minutes when
# offline with many selected packages.
_MAX_CONSECUTIVE_NETWORK_ERRORS = 2


def _load_cache():
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


class _NetworkError(Exception):
    """Raised for connection-level failures, as opposed to a well-formed
    HTTP response telling us the package doesn't exist."""


def _http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise _NetworkError(str(e))
    except Exception as e:
        raise _NetworkError(str(e))


def _http_status(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        raise _NetworkError(str(e))


def _repology_check(name, family):
    """True/False/None = found for this family / known project but not for
    this family / no data at all for this project name."""
    data = _http_json(f"https://repology.org/api/v1/project/{name}")
    if not data:
        return None

    target_prefixes = REPOLOGY_FAMILY_PREFIXES.get(family, ())
    found_for_target = False
    found_for_any_known = False
    for entry in data:
        repo = entry.get("repo", "")
        if repo.startswith(target_prefixes):
            found_for_target = True
        if repo.startswith(_ALL_KNOWN_PREFIXES):
            found_for_any_known = True

    if found_for_target:
        return True
    if found_for_any_known:
        return False
    return None


def _arch_check(name):
    data = _http_json(f"https://archlinux.org/packages/search/json/?name={name}")
    if data is None:
        return None
    return bool(data.get("results"))


def _fedora_check(name):
    status = _http_status(f"https://mdapi.fedoraproject.org/rawhide/pkg/{name}")
    return status == 200


def _live_check(original_name, translated_name, target_family):
    result = _repology_check(original_name, target_family)
    if result is None and translated_name != original_name:
        result = _repology_check(translated_name, target_family)
    if result is not None:
        return result

    if target_family == "arch":
        return _arch_check(translated_name)
    if target_family in ("fedora", "rhel"):
        return _fedora_check(translated_name)
    return None  # no reliable free API for this family yet -> unknown


def _is_plain_package_name(name):
    """Some MAP entries aren't a literal package name at all -- a dnf group
    ("@development-tools") or a zypper pattern invocation ("-t pattern
    devel_basis"). Those can never be looked up as a regular package, so
    validating them would only produce false "missing" results."""
    return name and not name.startswith(("@", "-")) and " " not in name


def validate_many(pairs, target_family):
    """pairs: iterable of (original_name, translated_name).
    Returns dict translated_name -> "verified" | "missing" | "unknown".
    Best-effort: never raises, degrades to "unknown" on any error, and stops
    hitting the network entirely after a few consecutive connection
    failures (e.g. offline) so it can't hang the whole batch."""
    cache = _load_cache()
    out = {}
    consecutive_network_errors = 0
    network_disabled = False

    for original, translated in pairs:
        if translated in out:
            continue  # duplicate translated name already resolved this run

        if not _is_plain_package_name(translated):
            out[translated] = "unknown"
            continue

        key = f"{target_family}:{translated}"
        cached = cache.get(key)
        if cached and time.time() - cached["ts"] < CACHE_TTL:
            out[translated] = cached["status"]
            continue

        if network_disabled:
            out[translated] = "unknown"
            continue

        try:
            result = _live_check(original, translated, target_family)
            consecutive_network_errors = 0
        except _NetworkError:
            consecutive_network_errors += 1
            if consecutive_network_errors >= _MAX_CONSECUTIVE_NETWORK_ERRORS:
                network_disabled = True
            out[translated] = "unknown"
            continue

        status = "unknown" if result is None else ("verified" if result else "missing")
        out[translated] = status
        cache[key] = {"status": status, "ts": time.time()}

    _save_cache(cache)
    return out


def validate_selected(pkg_names, target_family):
    """Convenience wrapper: translates each package name for target_family
    and validates the result. Returns dict translated_name -> status."""
    pairs = [(name, mapping.translate(name, target_family)) for name in pkg_names]
    return validate_many(pairs, target_family)
