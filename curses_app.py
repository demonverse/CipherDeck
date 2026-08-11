"""Cipher Machine — terminal (curses) front end.

Run with:  python3 curses_app.py
The cipher logic in ciphers/ is untouched; this file replaces app.py
and templates/ as the interface layer.

Designed for a 60x20 terminal (the Pi's 3.5" screen at a readable
console font) but adapts to anything larger. Needs at least 44x14.

Keys:
  Menu:       up/down or 1-8 to choose, Enter to open, Q to shut down
  Workspace:  Tab / up / down  move between fields
              left/right       toggle encrypt/decrypt (on Mode field)
                               or move cursor (in text fields)
              Enter            run the cipher
              Esc              back to the menu
"""
import os
os.environ.setdefault('ESCDELAY', '25')   # make Esc respond instantly

import curses
import textwrap
from ciphers import CIPHERS
import subprocess

# ---------------------------------------------------------------- helpers

def safe_addstr(win, y, x, text, attr=0):
    """addstr that never crashes on the bottom-right cell or overflow.

    curses raises an error if you write past the edge of the window
    (including the very last cell, a historical quirk). Clipping here
    keeps the drawing code simple.
    """
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    win.addnstr(y, x, text, w - x - 1, attr)


class LineEditor:
    """A single-line text field with a cursor and horizontal scrolling.

    curses gives us raw keypresses; everything else — inserting
    characters, backspace, moving the cursor, scrolling long text
    within a narrow field — we do ourselves.
    """

    def __init__(self, text=""):
        self.text = text
        self.cursor = len(text)
        self.offset = 0           # first visible character (scroll position)

    def handle(self, ch):
        if ch in (curses.KEY_LEFT,):
            self.cursor = max(0, self.cursor - 1)
        elif ch in (curses.KEY_RIGHT,):
            self.cursor = min(len(self.text), self.cursor + 1)
        elif ch in (curses.KEY_HOME,):
            self.cursor = 0
        elif ch in (curses.KEY_END,):
            self.cursor = len(self.text)
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if self.cursor > 0:
                self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
                self.cursor -= 1
        elif ch == curses.KEY_DC:                       # Delete key
            self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
        elif 32 <= ch <= 126:                           # printable ASCII
            self.text = self.text[:self.cursor] + chr(ch) + self.text[self.cursor:]
            self.cursor += 1

    def render(self, win, y, x, width, focused, placeholder=""):
        # Keep the cursor inside the visible window by scrolling.
        if self.cursor < self.offset:
            self.offset = self.cursor
        if self.cursor >= self.offset + width:
            self.offset = self.cursor - width + 1
        visible = self.text[self.offset:self.offset + width]

        if not self.text and placeholder and not focused:
            safe_addstr(win, y, x, placeholder[:width], curses.A_DIM)
        else:
            attr = curses.A_UNDERLINE if focused else 0
            safe_addstr(win, y, x, visible.ljust(width), attr)
        if focused:
            try:
                win.move(y, x + (self.cursor - self.offset))
            except curses.error:
                pass


# ---------------------------------------------------------------- screens

def confirm_shutdown(stdscr):
    """Ask before powering off. Returns True if confirmed."""
    curses.curs_set(0)
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        safe_addstr(stdscr, 0, 1, " SHUT DOWN ", curses.A_REVERSE)
        safe_addstr(stdscr, 2, 1, "Power off the cipher machine?")
        safe_addstr(stdscr, 4, 1, "Wait for the green light to stop")
        safe_addstr(stdscr, 5, 1, "blinking before unplugging.")
        safe_addstr(stdscr, h - 1, 1, "Y confirm  ·  N or Esc cancel",
                    curses.A_DIM)
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (ord('y'), ord('Y')):
            return True
        if ch in (ord('n'), ord('N'), 27):
            return False

def menu_screen(stdscr):
    """Cipher selection. Returns a cipher id, or None to quit."""
    ids = list(CIPHERS.keys())
    selected = 0
    curses.curs_set(0)

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        safe_addstr(stdscr, 0, 1, " CIPHER MACHINE ", curses.A_REVERSE)

        for i, cid in enumerate(ids):
            cipher = CIPHERS[cid]
            line = f" {i + 1}. {cipher.name:<11}"
            attr = curses.A_REVERSE if i == selected else 0
            safe_addstr(stdscr, 2 + i, 1, line, attr)
            safe_addstr(stdscr, 2 + i, 2 + len(line),
                        cipher.description, curses.A_DIM)

        safe_addstr(stdscr, h - 1, 1,
                    "up/down or 1-8 choose · Enter open · Q shut down", curses.A_DIM)
        stdscr.refresh()

        ch = stdscr.getch()
        if ch in (curses.KEY_UP, ord('k')):
            selected = (selected - 1) % len(ids)
        elif ch in (curses.KEY_DOWN, ord('j')):
            selected = (selected + 1) % len(ids)
        elif ord('1') <= ch <= ord(str(min(9, len(ids)))):
            return ids[ch - ord('1')]
        elif ch in (curses.KEY_ENTER, 10, 13):
            return ids[selected]
        elif ch in (ord('q'), ord('Q')):
            return None


def work_screen(stdscr, cipher_id):
    """Encrypt/decrypt workspace for one cipher. Returns on Esc."""
    cipher = CIPHERS[cipher_id]
    needs_key = getattr(cipher, "requires_key", True)

    mode_encrypt = True
    key_field = LineEditor()
    text_field = LineEditor()
    result_lines = []
    result_is_error = False

    # Focusable fields, top to bottom. Key field only if the cipher uses one.
    fields = ["mode"] + (["key"] if needs_key else []) + ["text"]
    focus = len(fields) - 1        # start on the text field

    key_row = 4
    text_row = 6 if needs_key else 4

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        inner = w - 10             # width available for input fields

        safe_addstr(stdscr, 0, 1, f" {cipher.name.upper()} ", curses.A_REVERSE)
        safe_addstr(stdscr, 1, 1, "-" * (w - 2), curses.A_DIM)

        # --- Mode row
        label = "[ Encrypt ]" if mode_encrypt else "[ Decrypt ]"
        attr = curses.A_REVERSE if fields[focus] == "mode" else curses.A_BOLD
        safe_addstr(stdscr, 2, 1, "Mode ")
        safe_addstr(stdscr, 2, 7, label, attr)
        if fields[focus] == "mode":
            safe_addstr(stdscr, 2, 9 + len(label),
                        "left/right to switch", curses.A_DIM)

        # --- Key row
        if needs_key:
            safe_addstr(stdscr, key_row, 1, "Key  ")
            key_field.render(stdscr, key_row, 7, inner,
                             False, cipher.key_hint)

        # --- Text row
        safe_addstr(stdscr, text_row, 1, "Text ")
        text_field.render(stdscr, text_row, 7, inner, False)

        # --- Result area
        sep_row = text_row + 2
        safe_addstr(stdscr, sep_row, 1, "-" * (w - 2), curses.A_DIM)
        first = sep_row + 1
        avail = max(1, h - first - 2)
        colour = curses.color_pair(2) if result_is_error else curses.color_pair(1)
        for i, line in enumerate(result_lines[:avail]):
            safe_addstr(stdscr, first + i, 1, line, colour | curses.A_BOLD)
        if len(result_lines) > avail:
            safe_addstr(stdscr, first + avail - 1, 1, "...(more)", curses.A_DIM)

        safe_addstr(stdscr, h - 1, 1,
                    "Tab next field · Enter run · Esc menu", curses.A_DIM)

        # Draw the focused editor last so the hardware cursor lands in it.
        if fields[focus] == "key":
            curses.curs_set(1)
            key_field.render(stdscr, key_row, 7, inner, True, cipher.key_hint)
        elif fields[focus] == "text":
            curses.curs_set(1)
            text_field.render(stdscr, text_row, 7, inner, True)
        else:
            curses.curs_set(0)

        stdscr.refresh()
        ch = stdscr.getch()

        if ch == 27:                                    # Esc
            return
        elif ch in (9, curses.KEY_DOWN):                # Tab / down arrow
            focus = (focus + 1) % len(fields)
        elif ch in (curses.KEY_BTAB, curses.KEY_UP):    # Shift-Tab / up arrow
            focus = (focus - 1) % len(fields)
        elif ch in (curses.KEY_ENTER, 10, 13):          # run it
            try:
                fn = cipher.encrypt if mode_encrypt else cipher.decrypt
                result = fn(text_field.text, key_field.text)
                result_lines = textwrap.wrap(result, w - 3) or ["(empty result)"]
                result_is_error = False
            except ValueError as e:
                result_lines = textwrap.wrap(str(e), w - 3)
                result_is_error = True
        elif fields[focus] == "mode" and ch in (curses.KEY_LEFT,
                                                curses.KEY_RIGHT, ord(' ')):
            mode_encrypt = not mode_encrypt
        elif fields[focus] == "key":
            key_field.handle(ch)
        elif fields[focus] == "text":
            text_field.handle(ch)


# ---------------------------------------------------------------- main

def main(stdscr):
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # results
    curses.init_pair(2, curses.COLOR_RED, -1)     # errors

    while True:
        h, w = stdscr.getmaxyx()
        if h < 14 or w < 44:
            stdscr.erase()
            safe_addstr(stdscr, 0, 0, "Terminal too small (need 44x14). Q quits.")
            stdscr.refresh()
            if stdscr.getch() in (ord('q'), ord('Q'), 27):
                return
            continue


        cipher_id = menu_screen(stdscr)
        if cipher_id is None:
            if confirm_shutdown(stdscr):
                stdscr.erase()
                safe_addstr(stdscr, 2, 1, "Shutting down...")
                stdscr.refresh()
                subprocess.run(["sudo", "systemctl", "poweroff"])
                return
            continue
        work_screen(stdscr, cipher_id)

if __name__ == '__main__':
    curses.wrapper(main)
