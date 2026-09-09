"""MovingOut interactive shell GUI (curses)."""
import curses
import os
import threading

from . import __version__, APP_NAME
from .distro import SUPPORTED_TARGETS
from .animation import play_packing_animation, play_install_animation

CTRL_S = 19  # Ctrl+S
CTRL_C = 3   # Ctrl+C (curses usually delivers this as KeyboardInterrupt, handled too)
CTRL_F = 6   # Ctrl+F (search)


def _draw_app_header(stdscr, w):
    """Top banner shown on every screen: app name + version, centered."""
    banner = f"{APP_NAME} v{__version__}"
    col = max(0, (w - len(banner)) // 2)
    stdscr.addstr(0, col, banner[: w - 1], curses.A_BOLD)


def run_scanning_animation(stdscr, work_fn, message="Scanning system (packages, services, scripts)..."):
    """Runs work_fn() in a background thread while drawing an indeterminate
    progress bar, so the command is clearly acknowledged even when the scan
    is slow (large package lists). Returns work_fn()'s return value."""
    result = {}

    def _target():
        result["value"] = work_fn()

    t = threading.Thread(target=_target)
    t.start()

    h, w = stdscr.getmaxyx()
    top = h // 2
    left = max(1, (w - max(len(message), 26)) // 2)
    bar_w = 24
    frame = 0

    stdscr.nodelay(True)
    while t.is_alive():
        stdscr.erase()
        _draw_app_header(stdscr, w)
        try:
            stdscr.addstr(top - 1, left, message[: w - 1], curses.A_BOLD)
        except curses.error:
            pass
        pos = frame % (bar_w * 2)
        pos = pos if pos < bar_w else (bar_w * 2 - pos) - 1
        bar = "[" + (" " * pos) + "=" + (" " * (bar_w - pos - 1)) + "]"
        try:
            stdscr.addstr(top + 1, left, bar)
        except curses.error:
            pass
        stdscr.refresh()
        curses.napms(80)
        frame += 1

    t.join()
    stdscr.nodelay(False)
    return result.get("value")


class Item:
    __slots__ = ("category", "name", "selected", "risk")

    def __init__(self, category, name, selected, risk=None):
        self.category = category
        self.name = name
        self.selected = selected
        self.risk = risk


def pick_target_distro(stdscr, current_family, found_scripts=None):
    """Combined picker: choose a target distro to create a new porting script
    ("create" mode), or pick a previously-generated script found on this
    machine to run it here directly ("install" mode). Both live on the same
    screen/step, install entries appear below the distro list.

    Returns (mode, value):
      ("create", family)  - user picked a target distro
      ("install", path)   - user picked an existing script to run
      (None, None)         - cancelled
    """
    curses.curs_set(0)
    distro_entries = list(SUPPORTED_TARGETS)  # (family, label)
    install_entries = list(found_scripts or [])  # absolute paths
    total = len(distro_entries) + len(install_entries)
    idx = 0

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        _draw_app_header(stdscr, w)
        stdscr.addstr(1, 2, "MovingOut - select the target distro", curses.A_BOLD)
        stdscr.addstr(2, 2, f"Detected current distro: {current_family}")

        row = 4
        for i, (fam, label) in enumerate(distro_entries):
            marker = "->" if i == idx else "  "
            same = "  (same family)" if fam == current_family else ""
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            stdscr.addstr(row, 2, f"{marker} {label}{same}"[: w - 3], attr)
            row += 1

        row += 1
        wall = "-" * max(10, w - 4)
        stdscr.addstr(row, 2, wall[: w - 3])
        row += 1
        stdscr.addstr(
            row, 2,
            f"Install an existing migration script for '{current_family}':",
            curses.A_BOLD | curses.A_UNDERLINE,
        )
        row += 1
        if not install_entries:
            stdscr.addstr(
                row, 2,
                "  No .sh installation script found for this distro."[: w - 3],
                curses.A_DIM,
            )
            row += 1
        for j, path in enumerate(install_entries):
            i = len(distro_entries) + j
            marker = "->" if i == idx else "  "
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            line = (f"{marker} Run on this machine: '{os.path.basename(path)}' "
                    f"(found in {os.path.dirname(path) or '.'}) - Enter to install")
            stdscr.addstr(row, 2, line[: w - 3], attr)
            row += 1

        stdscr.addstr(h - 2, 2, "Arrows: move  Enter: confirm  Ctrl+C: quit")
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % total
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % total
        elif key in (curses.KEY_ENTER, 10, 13):
            if idx < len(distro_entries):
                return "create", distro_entries[idx][0]
            return "install", install_entries[idx - len(distro_entries)]
        elif key == CTRL_C:
            return None, None


def _build_flat_list(categories):
    """categories: dict name -> list[Item]. Returns flat list of (kind, payload)
    where kind is 'header' or 'item'."""
    flat = []
    for cat_name, items in categories.items():
        flat.append(("header", cat_name))
        for it in items:
            flat.append(("item", it))
    return flat


def run_selector(stdscr, categories, target_family):
    """categories: dict category_name -> list[Item]
    Returns 'save' or 'quit'.
    """
    curses.curs_set(0)
    flat = _build_flat_list(categories)
    # cursor starts at first selectable item
    cursor = next((i for i, (k, _) in enumerate(flat) if k == "item"), 0)
    top = 0
    last_query = ""

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.erase()
        _draw_app_header(stdscr, w)
        stdscr.addstr(1, 2, f"MovingOut - target: {target_family}", curses.A_BOLD)
        stdscr.addstr(2, 2, "Enter: toggle selection   A: toggle whole category")

        body_h = h - 6
        if cursor < top:
            top = cursor
        if cursor >= top + body_h:
            top = cursor - body_h + 1

        row = 4
        for i in range(top, min(len(flat), top + body_h)):
            kind, payload = flat[i]
            if kind == "header":
                stdscr.addstr(row, 2, f"-- {payload} --", curses.A_BOLD | curses.A_UNDERLINE)
            else:
                it = payload
                box = "[x]" if it.selected else "[ ]"
                attr = curses.A_REVERSE if i == cursor else curses.A_NORMAL
                warn = f"  (!) {it.risk}" if it.risk else ""
                line = f"  {box} {it.name}{warn}"
                stdscr.addstr(row, 2, line[: w - 3], attr)
            row += 1

        stdscr.addstr(h - 2, 2,
                       "Arrows: navigate  Enter: toggle  A: toggle category  Ctrl+F: search  "
                       "Ctrl+S: save & generate  Ctrl+C: quit")
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            j = cursor - 1
            while j >= 0 and flat[j][0] != "item":
                j -= 1
            if j >= 0:
                cursor = j
        elif key in (curses.KEY_DOWN, ord("j")):
            j = cursor + 1
            while j < len(flat) and flat[j][0] != "item":
                j += 1
            if j < len(flat):
                cursor = j
        elif key in (curses.KEY_ENTER, 10, 13):
            flat[cursor][1].selected = not flat[cursor][1].selected
        elif key in (ord("a"), ord("A")):
            _toggle_category(flat, cursor)
        elif key == CTRL_F:
            query = _prompt_search(stdscr, last_query)
            if query:
                last_query = query
                match = _find_next_match(flat, cursor, query)
                if match is not None:
                    cursor = match
                else:
                    _flash_message(stdscr, f"'{query}' not found")
        elif key == CTRL_S:
            return "save"
        elif key == CTRL_C:
            return "quit"


def _prompt_search(stdscr, initial=""):
    """Inline search prompt on the last row. Returns the typed query, or
    None if the user cancelled with Esc."""
    h, w = stdscr.getmaxyx()
    query = initial
    curses.curs_set(1)
    try:
        while True:
            stdscr.addstr(h - 1, 2, " " * (w - 3))
            prompt = f"Search (name): {query}"
            stdscr.addstr(h - 1, 2, prompt[: w - 3])
            stdscr.move(h - 1, min(2 + len(prompt), w - 1))
            stdscr.refresh()

            key = stdscr.getch()
            if key in (curses.KEY_ENTER, 10, 13):
                return query
            elif key == 27:  # Esc
                return None
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                query = query[:-1]
            elif 32 <= key <= 126:
                query += chr(key)
    finally:
        curses.curs_set(0)


def _find_next_match(flat, cursor, query):
    """Search item names (case-insensitive substring), starting right after
    the current cursor and wrapping around the whole list."""
    if not flat:
        return None
    q = query.lower()
    n = len(flat)
    for offset in range(1, n + 1):
        i = (cursor + offset) % n
        kind, payload = flat[i]
        if kind == "item" and q in payload.name.lower():
            return i
    return None


def _flash_message(stdscr, msg):
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h - 1, 2, " " * (w - 3))
    stdscr.addstr(h - 1, 2, msg[: w - 3], curses.A_BOLD)
    stdscr.refresh()
    curses.napms(900)


def _toggle_category(flat, cursor):
    # find category start/end around cursor
    start = cursor
    while start > 0 and flat[start][0] != "header":
        start -= 1
    end = start + 1
    while end < len(flat) and flat[end][0] != "header":
        end += 1
    items = [p for k, p in flat[start:end] if k == "item"]
    if not items:
        return
    new_state = not all(it.selected for it in items)
    for it in items:
        it.selected = new_state


def run_packing_animation(stdscr, item_names):
    play_packing_animation(stdscr, item_names)


def confirm_install(stdscr, path):
    """Curses-based y/N confirmation before running a previously-generated
    script found on this machine. Returns True/False."""
    curses.curs_set(0)
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    _draw_app_header(stdscr, w)
    stdscr.addstr(2, 2, "MovingOut - confirm installation", curses.A_BOLD)
    stdscr.addstr(4, 2, f"Run '{os.path.basename(path)}' on this machine now?"[: w - 3])
    stdscr.addstr(5, 2, path[: w - 3])
    stdscr.addstr(h - 2, 2, "y: confirm   n / Ctrl+C: cancel and go back")
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (ord("y"), ord("Y")):
            return True
        if key in (ord("n"), ord("N"), CTRL_C, 27):
            return False


def run_install_animation(stdscr, path):
    play_install_animation(stdscr, os.path.basename(path))
