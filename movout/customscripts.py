"""Detect custom scripts/binaries not owned by the package manager.

These need to be copied verbatim into the generated installer (embedded
as base64) because the target distro's repos won't provide them.
"""
import os
import stat
import subprocess

SCAN_DIRS = [
    os.path.expanduser("~/bin"),
    os.path.expanduser("~/.local/bin"),
    "/usr/local/bin",
    "/usr/local/sbin",
]

_OWNER_CHECKERS = {
    "apt": lambda p: subprocess.run(["dpkg", "-S", p], capture_output=True).returncode == 0,
    "dnf": lambda p: subprocess.run(["rpm", "-qf", p], capture_output=True).returncode == 0,
    "pacman": lambda p: subprocess.run(["pacman", "-Qo", p], capture_output=True).returncode == 0,
    "zypper": lambda p: subprocess.run(["rpm", "-qf", p], capture_output=True).returncode == 0,
    "apk": lambda p: subprocess.run(["apk", "info", "-W", p], capture_output=True).returncode == 0,
}


def _is_executable(path):
    try:
        st = os.stat(path)
        return bool(st.st_mode & stat.S_IXUSR) and not stat.S_ISDIR(st.st_mode)
    except OSError:
        return False


def get_custom_scripts(package_manager):
    checker = _OWNER_CHECKERS.get(package_manager)
    found = []
    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            full = os.path.join(d, name)
            if not _is_executable(full):
                continue
            if checker and checker(full):
                continue  # owned by a package, will be reinstalled normally
            found.append(full)
    return found
