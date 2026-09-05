"""Distro & package-manager detection."""
import shutil

# family -> package manager binary used for install commands
FAMILY_PM = {
    "debian": "apt",
    "fedora": "dnf",
    "rhel": "dnf",
    "arch": "pacman",
    "suse": "zypper",
    "alpine": "apk",
}

# Known distro ids grouped by family (fallback via ID_LIKE too)
ID_TO_FAMILY = {
    "debian": "debian", "ubuntu": "debian", "linuxmint": "debian",
    "pop": "debian", "raspbian": "debian", "kali": "debian", "elementary": "debian",
    "fedora": "fedora",
    "rhel": "rhel", "centos": "rhel", "rocky": "rhel", "almalinux": "rhel",
    "arch": "arch", "manjaro": "arch", "endeavouros": "arch",
    "opensuse": "suse", "opensuse-leap": "suse", "opensuse-tumbleweed": "suse", "sles": "suse",
    "alpine": "alpine",
}

SUPPORTED_TARGETS = [
    ("debian", "Debian / Ubuntu / Mint (apt)"),
    ("fedora", "Fedora (dnf)"),
    ("rhel", "RHEL / CentOS / Rocky / Alma (dnf)"),
    ("arch", "Arch / Manjaro (pacman)"),
    ("suse", "openSUSE (zypper)"),
    ("alpine", "Alpine (apk)"),
]


def _parse_os_release(path="/etc/os-release"):
    data = {}
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                data[k] = v.strip('"')
    except FileNotFoundError:
        pass
    return data


def detect_current():
    """Return dict: id, name, family, package_manager."""
    info = _parse_os_release()
    os_id = info.get("ID", "linux").lower()
    id_like = info.get("ID_LIKE", "").lower().split()
    name = info.get("PRETTY_NAME", os_id)

    family = ID_TO_FAMILY.get(os_id)
    if not family:
        for cand in id_like:
            family = ID_TO_FAMILY.get(cand)
            if family:
                break
    if not family:
        # fallback: probe which package manager binary exists
        for fam, pm in FAMILY_PM.items():
            if shutil.which(pm):
                family = fam
                break
    if not family:
        family = "debian"

    return {
        "id": os_id,
        "name": name,
        "family": family,
        "package_manager": FAMILY_PM.get(family, "apt"),
    }


def pm_for_family(family):
    return FAMILY_PM.get(family, "apt")
