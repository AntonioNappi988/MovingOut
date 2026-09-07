"""MovingOut interactive shell GUI (curses)."""
import curses
import os

from .distro import SUPPORTED_TARGETS
from .animation import play_packing_animation

CTRL_S = 19  # Ctrl+S
CTRL_C = 3   # Ctrl+C (curses usually delivers this as KeyboardInterrupt, handled too)
CTRL_F = 6   # Ctrl+F (search)


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
        stdscr.addstr(0, 2, "MovingOut - select the target distro", curses.A_BOLD)
        stdscr.addstr(1, 2, f"Detected current distro: {current_family}")

        row = 3
        for i, (fam, label) in enumerate(distro_entries):
            marker = "->" if i == idx else "  "
            same = "  (same family)" if fam == current_family else ""
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            stdscr.addstr(row, 2, f"{marker} {label}{same}"[: w - 3], attr)
            row += 1

        if install_entries:
            row += 1
            stdscr.addstr(row, 2, "-- Install mode: run an existing migration script --",
                          curses.A_BOLD | curses.A_UNDERLINE)
            row += 1
            for j, path in enumerate(install_entries):
                i = len(distro_entries) + j
                marker = "->" if i == idx else "  "
                attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
                line = (f"{marker} Found '{os.path.basename(path)}' in "
                        f"{os.path.dirname(path) or '.'} - run it on this machine?")
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
        stdscr.addstr(0, 2, f"MovingOut - target: {target_family}", curses.A_BOLD)
        stdscr.addstr(1, 2, "Enter: toggle selection   A: toggle whole category")

        body_h = h - 5
        if cursor < top:
            top = cursor
        if cursor >= top + body_h:
            top = cursor - body_h + 1

        row = 3
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
