from .base import Cipher


class CaesarCipher(Cipher):
    name = "Caesar"
    description = "Shifts each letter by a fixed number (0–25). The classic."
    key_hint = "Shift amount, e.g. 13"

    def _shift(self, text: str, key: str, decrypt: bool) -> str:
        try:
            shift = int(key) % 26
        except ValueError:
            raise ValueError("Caesar key must be a whole number.")
        if decrypt:
            shift = -shift
        result = []
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                result.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                result.append(ch)
        return ''.join(result)

    def encrypt(self, text: str, key: str) -> str:
        return self._shift(text, key, decrypt=False)

    def decrypt(self, text: str, key: str) -> str:
        return self._shift(text, key, decrypt=True)
