"""Heuristics to flag items that should NOT be auto-selected when porting."""
import re

# Matches -> entirely hidden from the list (base OS plumbing, never port).
HIDDEN_PATTERNS = [
    r"^base-files$", r"^systemd$", r"^systemd-.*", r"^ubuntu-.*",
    r"^fedora-release.*", r"^filesystem$", r"^glibc$", r"^arch-install-scripts$",
    r"^shim-signed$", r"^grub-common$", r"^initramfs-tools$", r"^dracut$",
    r"^alpine-base$", r"^alpine-keys$",
]

# Matches -> shown, but UNCHECKED by default with a warning reason.
RISKY_RULES = [
    (r"gnome-shell|gnome-session|gdm3?$", "GNOME desktop environment: may differ on the new distro"),
    (r"plasma-desktop|plasma-workspace|sddm$", "KDE Plasma desktop environment: check compatibility"),
    (r"xfce4-session|xfdesktop|lightdm$", "XFCE desktop / display manager: check compatibility"),
    (r"mate-session|cinnamon|budgie-desktop|lxqt-session|lxde-common|lxdm", "Alternative desktop environment: may not be available"),
    (r"^linux-image.*|^linux-headers.*|^kernel-.*", "Kernel package: specific to the old machine, do not port"),
    (r"nvidia-.*|broadcom-.*-dkms|virtualbox-dkms|.*-dkms$", "Kernel driver/module: must be reinstalled manually on the new distro"),
    (r"^xserver-xorg-video-.*", "Specific graphics driver: check the new machine's hardware"),
    (r"grub-pc|grub-efi|grub2-common|systemd-boot", "Bootloader: should not be migrated, already handled by the new install"),
]


def is_hidden(name):
    return any(re.match(p, name) for p in HIDDEN_PATTERNS)


def risk_reason(name):
    for pattern, reason in RISKY_RULES:
        if re.match(pattern, name, re.IGNORECASE):
            return reason
    return None
