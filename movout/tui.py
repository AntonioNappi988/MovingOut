"""MovingOut interactive shell GUI (curses)."""
import curses

from .distro import SUPPORTED_TARGETS
from .animation import play_packing_animation

CTRL_S = 19  # Ctrl+S
CTRL_C = 3   # Ctrl+C (curses usually delivers this as KeyboardInterrupt, handled too)


class Item:
    __slots__ = ("category", "name", "selected", "risk")

    def __init__(self, category, name, selected, risk=None):
        self.category = category
        self.name = name
        self.selected = selected
        self.risk = risk


def pick_target_distro(stdscr, current_family):
    curses.curs_set(0)
    idx = 0
    options = SUPPORTED_TARGETS
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(0, 2, "MovingOut - select the target distro", curses.A_BOLD)
        stdscr.addstr(1, 2, f"Detected current distro: {current_family}")
        for i, (fam, label) in enumerate(options):
            marker = "->" if i == idx else "  "
            same = "  (same family)" if fam == current_family else ""
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            stdscr.addstr(3 + i, 2, f"{marker} {label}{same}", attr)
        stdscr.addstr(h - 2, 2, "Arrows: move  Enter: confirm  Ctrl+C: quit")
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(options)
        elif key in (curses.KEY_ENTER, 10, 13):
            return options[idx][0]
        elif key == CTRL_C:
            return None


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
                       "Arrows: navigate  Enter: toggle  A: toggle category  "
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
        elif key == CTRL_S:
            return "save"
        elif key == CTRL_C:
            return "quit"


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
