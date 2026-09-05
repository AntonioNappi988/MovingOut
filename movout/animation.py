"""Box-packing animation played while the .sh installer is being written."""
import curses
import time

BOX_TOP = "  .------------------------.  "
BOX_SIDE_EMPTY = "  |                        |  "
BOX_BOTTOM = "  '------------------------'  "
FILL_CHAR = "#"
BOX_INNER_WIDTH = 24
BOX_INNER_HEIGHT = 6


def play_packing_animation(stdscr, items, min_seconds=1.2, max_seconds=3.5):
    """Draws a box that fills up with '#' rows as items get packed.

    items: list of names (packages/services/scripts) just for label text.
    """
    if not items:
        items = ["(vuoto)"]
    h, w = stdscr.getmaxyx()
    top = max(1, h // 2 - (BOX_INNER_HEIGHT + 4) // 2)
    left = max(1, w // 2 - 15)

    n = len(items)
    total_frames = max(BOX_INNER_HEIGHT, min(n, 60))
    delay = max(min_seconds, min(max_seconds, n * 0.02)) / total_frames

    stdscr.nodelay(True)
    for frame in range(total_frames + 1):
        stdscr.erase()
        title = "MovingOut is packing your new machine..."
        stdscr.addstr(top - 2, max(0, left - 2), title[: w - 1])

        filled_rows = int(BOX_INNER_HEIGHT * frame / total_frames)
        stdscr.addstr(top, left, BOX_TOP)
        for r in range(BOX_INNER_HEIGHT):
            row_top = top + 1 + r
            if r >= BOX_INNER_HEIGHT - filled_rows:
                line = "  |" + (FILL_CHAR * BOX_INNER_WIDTH) + "|  "
            else:
                line = BOX_SIDE_EMPTY
            try:
                stdscr.addstr(row_top, left, line)
            except curses.error:
                pass
        stdscr.addstr(top + 1 + BOX_INNER_HEIGHT, left, BOX_BOTTOM)

        idx = min(int(n * frame / total_frames), n - 1)
        label = f"[{idx + 1}/{n}] packing: {items[idx]}"
        try:
            stdscr.addstr(top + BOX_INNER_HEIGHT + 3, max(0, left - 2), label[: w - 1])
        except curses.error:
            pass

        pct = int(100 * frame / total_frames)
        bar_w = 30
        filled = int(bar_w * frame / total_frames)
        bar = "[" + ("=" * filled) + (" " * (bar_w - filled)) + f"] {pct}%"
        try:
            stdscr.addstr(top + BOX_INNER_HEIGHT + 5, max(0, left - 2), bar)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(delay)

    stdscr.nodelay(False)
