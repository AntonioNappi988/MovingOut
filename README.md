![MovingOut logo](movingoutlogo.png)

# MovingOut (`movout`)

A pure shell/terminal tool for **Linux distro-hopping / porting**: it scans
the current machine (manually installed packages, enabled systemd services,
custom scripts in `~/bin`, `~/.local/bin`, `/usr/local/bin`,
`/usr/local/sbin`) and generates a single self-installing `.sh` script to run
on the new machine.

Everything runs inside the terminal via `curses` — there is no graphical
window, desktop app, or X11/Wayland dependency. It works over plain SSH.

## Install

Quick install from source:
```bash
bash install.sh
```
Installs the library to `/usr/local/lib/movout`, creates the `movout`
command in `/usr/local/bin`, and installs the `movout(1)` man page.

Package-manager install (build it yourself once you clone/download the repo):
```bash
# Debian / Ubuntu / Mint
bash packaging/build-deb.sh
sudo apt install ./movout_1.0.0_all.deb

# Arch / Manjaro (AUR-style package)
cd packaging
makepkg -si
```
See `packaging/PKGBUILD` if you want to publish it to the AUR yourself
(after tagging a GitHub release, run `updpkgsums` in `packaging/` to fill in
the real checksum instead of `SKIP`).

## Usage
```bash
movout            # open the interactive TUI (default action, same as -s)
movout -s         # open the interactive TUI explicitly
movout -c         # print a scan summary, generate nothing
movout -s -d      # skip target-distro picker, keep the current distro
movout -s -o /tmp/porting.sh   # custom output path
movout -h         # full option list
movout -v         # print version
man movout        # full manual + TUI keybindings
```

## Flow
1. **Target distro selection** (Debian/Ubuntu, Fedora, RHEL, Arch, openSUSE,
   Alpine) — if it's the same as the current one, everything defaults to
   selected, no extra care needed.
2. **Item selection**: packages, services, custom scripts. Everything is
   selected by default, **except**:
   - base-system packages/services (hidden entirely, porting them makes no
     sense)
   - desktop environments, display managers, kernel/GPU drivers, bootloader:
     shown with a **(!) reason**, unselected by default when the target
     distro is a different family (they might not work there).
3. **Ctrl+S**: plays the box-packing animation, then writes the `.sh` file.

## TUI key bindings
| Key | Action |
|---|---|
| Up/Down arrows | navigate |
| Enter | toggle selection |
| A | toggle the whole current category |
| Ctrl+S | save and generate the script |
| Ctrl+C | quit without generating |

## About the generated script
- Uses the correct package manager for the chosen distro (`apt`, `dnf`,
  `pacman`, `zypper`, `apk`) and translates package names when needed
  (`mapping.py`, best-effort).
- A single package/service failure never stops the script: failures are
  logged to `movingout-failed.log`.
- Custom scripts are embedded (base64) and restored to their original path.

## Extending
- `movout/mapping.py`: add more package-name translations across distros.
- `movout/rules.py`: add patterns to hide/flag more packages.

## Author
Created by **Antonio Nappi** — [GitHub](https://github.com/AntonioNappi988) — [portfolio](https://antonionappi.pages.dev)

## License
Released under the [MIT license](LICENSE): use it, modify it, and integrate
it freely, including in commercial projects, as long as you keep the
copyright notice and license in copies/derivatives.
