# Cipher Machine

A standalone cipher machine: a Raspberry Pi Zero 2 W with a 3.5" screen
that boots straight into eight historical ciphers, from a Hebrew scribe's
mirror alphabet to the Wehrmacht Enigma. No login, no desktop, no network.
Power it on, pick a cipher, type.

Built as a gift for a teenager who likes codes.

Three interfaces, one cipher engine: a curses terminal app for the Pi, a
Flask web app for a local network, and a
**[browser version](https://github.com/YOURNAME/REPONAME)** that needs no
server at all.

---

## The ciphers

| | Cipher | Era | Key |
|---|---|---|---|
| 🔁 | **Atbash** | Judea, c.600 BC | none |
| | **Caesar** | Rome, c.50 BC | a number, 0–25 |
| | **Rail Fence** | uncertain | number of rails |
| | **Vigenère** | Italy, 1553 | a keyword |
| | **Playfair** | London, 1854 | a keyword |
| 🔁 | **Beaufort** | England, 1857 | a keyword |
| 🔁 | **Enigma** | Germany, 1918 | e.g. `I II III AAA` |
| 🔁 | **ROT13** | Usenet, 1980s | none |

🔁 = reciprocal: the same operation encrypts and decrypts.

### Enigma keys

Three rotors and three start positions, at minimum:

```
I II III AAA
```

Rotors are Roman numerals `I` to `V`, given left to right as they sit in
the machine. Ring settings and plugboard pairs are optional:

```
I II III AAA BBB          with ring settings
I II III AAA BBB AB CD    with ring settings and two plug pairs
```

This is Enigma I with reflector B, including the double-stepping anomaly
of the real machine — and its fatal flaw, faithfully reproduced: **no
letter ever encrypts to itself.** Encrypt two hundred A's and count how
many come back.

`test_ciphers.py` checks all three properties: the historical vector
`AAAAA` → `BDZGO`, the double-step sequence `ADV AEW BFX BFY`, and the
no-self-mapping guarantee.

---

## Running it

### Terminal (what the Pi runs)

```bash
python3 curses_app.py
```

No dependencies beyond the standard library. Designed for a 60×20 terminal
— the Pi's 3.5" screen at a readable console font — but adapts to anything
larger, and refuses to draw below 44×14.

```
up/down or 1-8   choose a cipher        Tab    next field
Enter            open / run             Esc    back to the menu
```

### Local web server

```bash
pip install flask
python3 app.py
```

Serves on port 5000, reachable from any device on the same network. Find
the Pi with `hostname -I`.

### Tests

```bash
python3 test_ciphers.py
```

Round trips every cipher against five sample texts, verifies the Enigma
properties, and confirms that bad keys raise `ValueError` rather than
crashing — so the interface can show a message instead of dying.

---

## Structure

```
curses_app.py        terminal interface (the Pi)
app.py               Flask interface (local network)
test_ciphers.py      test suite
templates/
    index.html       Flask template
ciphers/
    base.py          abstract Cipher class — the shared interface
    caesar.py        Caesar
    vigenere.py      Vigenère and Beaufort
    atbash.py        Atbash and ROT13
    railfence.py     Rail Fence
    playfair.py      Playfair
    enigma.py        Enigma
    __init__.py      the CIPHERS registry
```

The engine knows nothing about how it is displayed. Every cipher exposes
`encrypt(text, key)` and `decrypt(text, key)`, so the calling code never
needs to know which one it is holding:

```python
from ciphers import CIPHERS

CIPHERS['caesar'].encrypt('Hello, World!', '3')      # 'Khoor, Zruog!'
CIPHERS['enigma'].encrypt('HELLO', 'I II III AAA')   # 'ILBDA'
```

That separation is why the same package drives three front ends, and why
porting to JavaScript meant reimplementing eight algorithms rather than
untangling them from a user interface.

### Adding a cipher

Subclass `Cipher`, implement the two methods, add it to the registry in
`__init__.py`. Both interfaces pick it up automatically — including the key
field, which hides itself when `requires_key` is `False`, and the hint text
shown inside it.

```python
from .base import Cipher

class ReverseCipher(Cipher):
    name = "Reverse"
    description = "Writes the message backwards."
    key_hint = "(no key required)"
    requires_key = False

    def encrypt(self, text: str, key: str = "") -> str:
        return text[::-1]

    def decrypt(self, text: str, key: str = "") -> str:
        return text[::-1]
```

---

## Behaviour worth knowing

**Case and punctuation survive** Caesar, Vigenère, Beaufort, Atbash and
ROT13. `Hello, World!` encrypts to `Khoor, Zruog!` rather than shouting.

**Rail Fence keeps spaces** and zigzags them along with the letters, so
`HELLO WORLD` becomes `HOREL OLLWD`.

**Playfair and Enigma strip everything but letters**, as the originals did.
Playfair also folds J into I and pads doubled letters with X — except when
the doubled letter *is* X, where it uses Q.

**Bad keys raise `ValueError`**, never anything else. Both interfaces catch
it and show the message, so a typo produces a red line rather than a crash.

---

## Known issue: non-ASCII input

`str.isalpha()` returns `True` for accented and non-Latin letters, so
characters like `é` and `日` get arithmetic done to them. `café` encrypts to
`fdij` under a Caesar shift of three — the `é` has become a `j`. Atbash
raises `ValueError` outright.

The fix is an explicit ASCII test in place of `ch.isalpha()`:

```python
if 'A' <= ch.upper() <= 'Z':
```

in `caesar.py`, `vigenere.py` and `atbash.py`, plus `clean()` in `base.py`,
which affects Playfair, Enigma and Rail Fence. **Not yet applied.**

---

## The hardware

- Raspberry Pi Zero 2 W
- Waveshare 3.5" RPi LCD (F), ST7796S controller, over SPI
- Raspberry Pi OS Lite (Trixie), no desktop
- USB keyboard via an OTG adapter

Nine wires: power, ground, the four SPI lines, plus data/command, reset and
backlight. Touch is not connected.

The curses app runs as a systemd service that owns `tty1`, with the login
prompt disabled so nothing competes for the screen:

```ini
[Unit]
Description=Cipher Machine
After=multi-user.target systemd-user-sessions.service

[Service]
ExecStart=/usr/bin/python3 /home/pi/cipher_machine/curses_app.py
StandardInput=tty
StandardOutput=tty
TTYPath=/dev/tty1
Restart=always
User=pi
ExecStartPre=/bin/sleep 10

[Install]
WantedBy=multi-user.target
```

Two details that are load-bearing rather than decorative. `quiet
loglevel=3` in `cmdline.txt` stops late boot messages painting over the
interface — curses caches what it believes is on screen, so anything else
writing to `tty1` leaves the app running invisibly underneath. And
`ExecStartPre=/bin/sleep 10` gives the console time to settle at its final
dimensions, because curses reads the terminal size once at startup and
never asks again.

---

## A word of warning

**Do not use any of this to protect anything that matters.**

Every cipher here has been thoroughly broken, most of them long ago.
Caesar falls to twenty-five guesses. Vigenère fell to Kasiski in 1863.
Enigma fell to Polish mathematicians and then to Bletchley Park.

That is exactly why they are worth playing with. Each one is small enough
to hold in your head and work with a pencil, and you can see precisely why
it was trusted and precisely why it stopped being trustworthy. Modern
cryptography is unbroken but opaque; these are broken but transparent.

---

## Licence

GNU General Public License v3.0 or later. See `LICENSE`.

---

If this was any fun, you can [buy me a coffee](https://ko-fi.com/thedemonverse).
