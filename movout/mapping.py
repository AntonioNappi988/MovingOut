"""Best-effort package name translation across distro families.

Key = canonical/generic name (usually the Debian name). Value = dict of
family -> name on that family. Missing family falls back to the generic
name unchanged (still installed with a best-effort attempt in the
generated script; failures are logged, not fatal).
"""

MAP = {
    "python3-pip": {"fedora": "python3-pip", "rhel": "python3-pip", "arch": "python-pip", "suse": "python3-pip", "apk": "py3-pip"},
    "build-essential": {"fedora": "@development-tools", "rhel": "@development-tools", "arch": "base-devel", "suse": "-t pattern devel_basis", "apk": "build-base"},
    "nodejs": {"fedora": "nodejs", "rhel": "nodejs", "arch": "nodejs", "suse": "nodejs", "apk": "nodejs"},
    "npm": {"fedora": "npm", "rhel": "npm", "arch": "npm", "suse": "npm", "apk": "npm"},
    "curl": {},
    "wget": {},
    "git": {},
    "vim": {},
    "neovim": {"apk": "neovim"},
    "htop": {},
    "tmux": {},
    "docker.io": {"fedora": "docker", "rhel": "docker", "arch": "docker", "suse": "docker", "apk": "docker"},
    "docker-compose": {},
    "openssh-server": {"fedora": "openssh-server", "rhel": "openssh-server", "arch": "openssh", "suse": "openssh", "apk": "openssh"},
    "ffmpeg": {},
    "unzip": {},
    "zip": {},
    "gcc": {},
    "make": {},
    "python3": {"arch": "python"},
    "python3-venv": {"fedora": "python3-virtualenv", "rhel": "python3-virtualenv", "arch": "python-virtualenv", "suse": "python3-virtualenv", "apk": "py3-virtualenv"},
    "libssl-dev": {"fedora": "openssl-devel", "rhel": "openssl-devel", "arch": "openssl", "suse": "libopenssl-devel", "apk": "openssl-dev"},
    "libpq-dev": {"fedora": "libpq-devel", "rhel": "libpq-devel", "arch": "postgresql-libs", "suse": "postgresql-devel", "apk": "postgresql-dev"},
}


def translate(name, target_family):
    entry = MAP.get(name)
    if entry is None:
        return name
    return entry.get(target_family, name)
