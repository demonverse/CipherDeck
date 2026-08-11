from .base import Cipher

# Historical rotor wirings for the Wehrmacht Enigma I.
# Each string says where A..Z map to going "forward" (right to left
# through the machine). The letter after the comma below is the notch:
# when this letter is visible in the window, the NEXT keypress also
# steps the rotor to the left of this one.
ROTOR_SPECS = {
    "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV":  ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V":   ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
}

REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"


def _idx(ch):
    return ord(ch) - ord('A')


class _Rotor:
    def __init__(self, name, position, ring):
        wiring, notch = ROTOR_SPECS[name]
        self.forward = [_idx(c) for c in wiring]
        self.backward = [0] * 26
        for i, o in enumerate(self.forward):
            self.backward[o] = i
        self.notch = _idx(notch)
        self.pos = _idx(position)    # letter showing in the window
        self.ring = _idx(ring)       # ring setting (Ringstellung)

    def at_notch(self):
        return self.pos == self.notch

    def step(self):
        self.pos = (self.pos + 1) % 26

    def enc_forward(self, c):
        shift = self.pos - self.ring
        return (self.forward[(c + shift) % 26] - shift) % 26

    def enc_backward(self, c):
        shift = self.pos - self.ring
        return (self.backward[(c + shift) % 26] - shift) % 26


class EnigmaCipher(Cipher):
    name = "Enigma"
    description = ("Simulates the WW2 German Enigma I: plugboard, three rotors, "
                   "reflector B. Reciprocal — same settings encrypt and decrypt.")
    key_hint = "3 rotors + start, e.g.I II III AAA"

    def _parse_key(self, key: str):
        """Key format, space separated:

            ROTOR ROTOR ROTOR POSITIONS [RINGS] [PLUG PLUG ...]

        e.g.  "I II III AAA"            basic setup
              "III I V QEV"             different rotors and start positions
              "I II III AAA BBB AB CD"  with ring settings and plugboard pairs
        """
        tokens = key.upper().split()
        if len(tokens) < 4:
            raise ValueError(
                "Enigma key needs at least: three rotors and start positions, "
                "e.g. 'I II III AAA'.")

        rotor_names = tokens[0:3]
        for r in rotor_names:
            if r not in ROTOR_SPECS:
                raise ValueError(
                    f"Unknown rotor '{r}'. Available: I, II, III, IV, V.")

        positions = tokens[3]
        if len(positions) != 3 or not positions.isalpha():
            raise ValueError("Start positions must be three letters, e.g. AAA.")

        rest = tokens[4:]
        rings = "AAA"
        if rest and len(rest[0]) == 3 and rest[0].isalpha():
            rings = rest[0]
            rest = rest[1:]

        used = set()
        plugboard = {}
        for pair in rest:
            if len(pair) != 2 or not pair.isalpha() or pair[0] == pair[1]:
                raise ValueError(
                    f"Plugboard pair '{pair}' must be two different letters, e.g. AB.")
            a, b = pair[0], pair[1]
            if a in used or b in used:
                raise ValueError(f"Letter in plug pair '{pair}' is already plugged.")
            used.update(pair)
            plugboard[a] = b
            plugboard[b] = a

        # The key reads left-to-right as on the machine; the signal
        # enters at the RIGHT, so build [left, middle, right].
        left = _Rotor(rotor_names[0], positions[0], rings[0])
        middle = _Rotor(rotor_names[1], positions[1], rings[1])
        right = _Rotor(rotor_names[2], positions[2], rings[2])
        return left, middle, right, plugboard

    def _step(self, left, middle, right):
        """Rotor stepping, including the double-step anomaly.

        The middle rotor's pawl can engage whenever the middle rotor
        itself sits at its notch — so on that press the middle rotor
        steps AGAIN (its second step in two presses) and carries the
        left rotor with it. Otherwise the middle rotor only steps when
        the right rotor is at its notch. The right rotor steps on
        every keypress, like the units wheel of an odometer.
        """
        if middle.at_notch():
            left.step()
            middle.step()
        elif right.at_notch():
            middle.step()
        right.step()

    def _process(self, text: str, key: str) -> str:
        left, middle, right, plugboard = self._parse_key(key)
        reflector = [_idx(c) for c in REFLECTOR_B]
        result = []
        for ch in self.clean(text):
            # Rotors step BEFORE the electrical contact is made.
            self._step(left, middle, right)

            c = _idx(plugboard.get(ch, ch))
            c = right.enc_forward(c)
            c = middle.enc_forward(c)
            c = left.enc_forward(c)
            c = reflector[c]
            c = left.enc_backward(c)
            c = middle.enc_backward(c)
            c = right.enc_backward(c)
            out = chr(c + ord('A'))
            result.append(plugboard.get(out, out))
        return ''.join(result)

    def encrypt(self, text: str, key: str) -> str:
        return self._process(text, key)

    def decrypt(self, text: str, key: str) -> str:
        return self._process(text, key)  # reciprocal, thanks to the reflector
