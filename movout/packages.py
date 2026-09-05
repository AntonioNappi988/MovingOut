"""List manually/explicitly installed packages per package manager.

We deliberately fetch only *explicitly requested* packages (excluding
automatic dependencies) so the porting list stays small and meaningful.
"""
import subprocess


def _run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if out.returncode != 0:
            return []
        return [l.strip() for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def get_installed_packages(package_manager):
    if package_manager == "apt":
        pkgs = _run(["apt-mark", "showmanual"])
        if pkgs:
            return sorted(set(pkgs))
        # fallback
        lines = _run(["dpkg", "--get-selections"])
        return sorted({l.split()[0] for l in lines if "deinstall" not in l})

    if package_manager == "dnf":
        pkgs = _run(["dnf", "repoquery", "--userinstalled", "--qf", "%{name}"])
        if pkgs:
            return sorted(set(pkgs))
        return sorted(set(_run(["rpm", "-qa", "--qf", "%{NAME}\n"])))

    if package_manager == "pacman":
        return sorted(set(_run(["pacman", "-Qqe"])))

    if package_manager == "zypper":
        lines = _run(["zypper", "--xmlout", "se", "--installed-only"])
        if lines:
            import re
            names = re.findall(r'name="([^"]+)"', "\n".join(lines))
            if names:
                return sorted(set(names))
        return sorted(set(_run(["rpm", "-qa", "--qf", "%{NAME}\n"])))

    if package_manager == "apk":
        return sorted(set(_run(["apk", "info", "-e"])))

    return []
