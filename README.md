<div align="center">
  <img src="movingoutlogo.png" alt="MovingOut logo" width="200"/>
  <h1>MovingOut (<code>movout</code>)</h1>
  <p><em>The ultimate Linux distro-hopping and system migration tool for the terminal.</em></p>
  
  [![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm--Noncommercial--1.0.0-blue.svg)](LICENSE)
  [![GitHub](https://img.shields.io/badge/GitHub-AntonioNappi988-181717.svg?style=flat&logo=github)](https://github.com/AntonioNappi988)
  [![Portfolio](https://img.shields.io/badge/Portfolio-antonionappi.pages.dev-0055FF.svg?style=flat&logo=googlechrome)](https://antonionappi.pages.dev)
</div>

## 🚀 Overview

**MovingOut** is a pure shell/terminal tool designed to make Linux distro-hopping and system porting painless. It scans your current machine for manually installed packages, enabled systemd services, and custom user scripts, then generates a single, self-contained `.sh` script to replicate your setup on a new machine.

Everything runs entirely in the terminal via a `curses`-based TUI (Text User Interface). No graphical desktop, X11, or Wayland dependencies required—it works perfectly over plain SSH!

---

## ✨ Features
- 📦 **Cross-Distro Translation:** Automatically translates package names between distros (e.g., `apt` to `dnf` to `pacman`) using a best-effort mapping system.
- ⚙️ **Systemd Services & Scripts:** Detects enabled services and embeds custom scripts (`~/bin`, `/usr/local/bin`, `/usr/local/sbin`, etc.) as base64 payloads to restore them perfectly.
- 🛡️ **Smart Filtering:** Hides base-system packages (which don't need porting) and flags risky items (like Desktop Environments, kernels, or GPU drivers) when migrating between different distro families.
- 🖥️ **TUI Driven:** Fast, keyboard-navigable interactive interface.
- 🚀 **Fault-Tolerant Output:** The generated script never stops on a single failure; errors are safely logged to `movingout-failed.log` while the rest of the installation continues.

## 📥 Installation

### Quick Install (From Source)
Installs the library to `/usr/local/lib/movout`, creates the executable in `/usr/local/bin`, and installs the `movout(1)` man page.
```bash
# Clone the repository first, then run:
bash install.sh
```

### Package Managers NOT WORKING NEEDS IMPLEMENTATION! 
Build and install it via your native package manager (after cloning/downloading the repo):

**Debian / Ubuntu / Mint:**
```bash
bash packaging/build-deb.sh
sudo apt install ./movout_1.0.0_all.deb
```

**Arch Linux / Manjaro (AUR-style):**
```bash
cd packaging
makepkg -si
```
*(Note: For AUR maintainers, check `packaging/PKGBUILD`. Run `updpkgsums` in `packaging/` after tagging a GitHub release to update checksums).*

## 💻 Usage

Simply type `movout` to launch the interactive TUI. 

### Command Line Options
```bash
movout                 # Open the interactive TUI (default action)
movout -s              # Open the interactive TUI explicitly
movout -c              # Dry-run: print a scan summary without generating a script
movout -s -d           # Skip the target-distro picker (assumes current distro)
movout -s -o /path/sh  # Generate the script at a custom output path
movout -h              # Show full help and option list
movout -v              # Print version
man movout             # View the full manual and TUI keybindings
```

## 🔄 The Migration Flow

1. **Target Distro Selection:** Choose your destination (Debian/Ubuntu, Fedora, RHEL, Arch, openSUSE, Alpine). If moving to the same distro, everything defaults to selected automatically.
2. **Item Selection:** Review packages, services, and scripts.
   - *Base packages* are hidden entirely as porting them makes no sense.
   - *System-critical items* (DEs, display managers, kernels, bootloaders) are shown with a **(!)** reason and are unselected by default when crossing distro families.
3. **Pack & Export:** Hit `Ctrl+S` to watch the box-packing animation and generate your migration script!

## ⌨️ TUI Key Bindings

| Key | Action |
|---|---|
| `↑` / `↓` | Navigate list items |
| `Enter` | Toggle selection for the highlighted item |
| `A` | Toggle selection for the entire current category |
| `Ctrl+S` | Save selections and generate the script |
| `Ctrl+C` | Quit immediately without saving |

## 🛠️ Extending & Customizing

Want to improve the cross-distro intelligence? Contributions are welcome!
- **`movout/mapping.py`**: Add or refine package-name translations across different distributions.
- **`movout/rules.py`**: Add regex patterns or rules to hide or flag specific packages during the scan.

## 👨‍💻 Author

Created by **Antonio Nappi**  
[GitHub](https://github.com/AntonioNappi988) | [Portfolio](https://antonionappi.pages.dev)

## 📄 License

Released under the [PolyForm Noncommercial License 1.0.0](LICENSE). You are free to use, modify, and share it for any noncommercial purpose (personal use, hobby projects, education, research, nonprofits, etc.), provided you keep the required copyright/license notice. Selling the software, sublicensing it, or using it for any commercial purpose is not permitted.
