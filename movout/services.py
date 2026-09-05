"""Enabled systemd services, filtered of core/base-system noise."""
import subprocess

HIDE_PREFIXES = (
    "systemd-", "dbus", "getty@", "serial-getty@", "console-getty",
    "user@", "user-runtime-dir@", "rc-local", "networking",
    "polkit", "udisks2", "upower", "ModemManager", "packagekit",
)


def get_enabled_services():
    try:
        out = subprocess.run(
            ["systemctl", "list-unit-files", "--type=service",
             "--state=enabled", "--no-legend", "--no-pager"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        return []
    if out.returncode != 0:
        return []

    services = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        name = line.split()[0]
        name = name[:-len(".service")] if name.endswith(".service") else name
        if name.startswith(HIDE_PREFIXES):
            continue
        services.append(name)
    return sorted(set(services))
