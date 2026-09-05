import argparse
import curses
import os
import sys

from . import __version__, distro, packages, services, customscripts, rules
from .tui import Item, pick_target_distro, run_selector, run_packing_animation
from .generator import build_script, write_script


def _scan(source_info):
    pm = source_info["package_manager"]
    pkg_names = packages.get_installed_packages(pm)
    svc_names = services.get_enabled_services()
    script_paths = customscripts.get_custom_scripts(pm)
    return pkg_names, svc_names, script_paths


def _build_categories(source_info, target_family, pkg_names, svc_names, script_paths):
    same_family = source_info["family"] == target_family

    pkg_items = []
    for name in pkg_names:
        if rules.is_hidden(name):
            continue
        risk = rules.risk_reason(name)
        default_selected = True if (risk is None or same_family) else False
        pkg_items.append(Item("Packages", name, default_selected, risk))

    svc_items = []
    for name in svc_names:
        risk = rules.risk_reason(name)
        default_selected = True if (risk is None or same_family) else False
        svc_items.append(Item("Services (systemd)", name, default_selected, risk))

    script_items = []
    for path in script_paths:
        script_items.append(Item("Custom scripts", path, True, None))

    return {
        "Packages": pkg_items,
        "Services (systemd)": svc_items,
        "Custom scripts": script_items,
    }


def cmd_scan(args):
    info = distro.detect_current()
    pkg_names, svc_names, script_paths = _scan(info)
    print(f"Current distro: {info['name']} (family: {info['family']}, "
          f"package manager: {info['package_manager']})")
    print(f"Manually installed packages: {len(pkg_names)}")
    print(f"Enabled services: {len(svc_names)}")
    print(f"Custom scripts found: {len(script_paths)}")


def _curses_main(stdscr, args, info, pkg_names, svc_names, script_paths):
    curses.curs_set(0)
    # Raw mode: without it, Ctrl+C raises SIGINT/KeyboardInterrupt instead of
    # reaching getch(), and Ctrl+S is swallowed by terminal flow control
    # (XOFF), freezing the screen instead of triggering save.
    curses.raw()
    if args.same_distro:
        target_family = info["family"]
    else:
        target_family = pick_target_distro(stdscr, info["family"])
        if target_family is None:
            return None, None

    categories = _build_categories(info, target_family, pkg_names, svc_names, script_paths)
    result = run_selector(stdscr, categories, target_family)
    if result != "save":
        return None, None

    selected_pkgs = [it.name for it in categories["Packages"] if it.selected]
    selected_svcs = [it.name for it in categories["Services (systemd)"] if it.selected]
    selected_scripts = [it.name for it in categories["Custom scripts"] if it.selected]

    all_selected_names = selected_pkgs + selected_svcs + [os.path.basename(p) for p in selected_scripts]
    run_packing_animation(stdscr, all_selected_names)

    content = build_script(info, target_family, selected_pkgs, selected_svcs, selected_scripts)
    return content, target_family


def cmd_run(args):
    info = distro.detect_current()
    print("MovingOut: scanning the system...")
    pkg_names, svc_names, script_paths = _scan(info)

    content, target_family = curses.wrapper(
        _curses_main, args, info, pkg_names, svc_names, script_paths
    )
    if content is None:
        print("Cancelled, no file was generated.")
        return

    out_path = args.output or f"movingout-install-{target_family}.sh"
    write_script(content, out_path)
    print(f"Done. Script generated: {out_path}")
    print(f"Copy it to the new machine and run: bash {out_path}")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="movout",
        description=(
            "MovingOut - Linux distro-hopping / porting tool. Scans packages, "
            "systemd services and custom scripts on this machine and generates "
            "a single .sh installer to reproduce them on a new machine (same "
            "distro or a different one)."
        ),
        epilog=(
            "Examples:\n"
            "  movout -s                 interactive TUI, pick target distro\n"
            "  movout -s -d              interactive TUI, keep current distro\n"
            "  movout -s -o porting.sh   interactive TUI, custom output path\n"
            "  movout -c                 print a scan summary, generate nothing\n"
            "\n"
            "See 'man movout' for the full manual and TUI keybindings."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"MovingOut {__version__}"
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "-s", "--select", action="store_true",
        help="open the interactive TUI and generate the porting script (default action)",
    )
    action.add_argument(
        "-c", "--scan", action="store_true",
        help="print a summary of what would be detected, generate nothing",
    )
    parser.add_argument(
        "-d", "--same-distro", action="store_true",
        help="skip the target-distro picker and reuse the current distro",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE",
        help="path of the generated .sh file (default: movingout-install-<distro>.sh)",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.scan:
            cmd_scan(args)
        else:
            cmd_run(args)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == "__main__":
    main()
