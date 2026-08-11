from .base import Cipher


class AtbashCipher(Cipher):
    name = "Atbash"
    description = "Hebrew mirror cipher — A↔Z, B↔Y, etc. No key needed."
    key_hint = "(no key required)"
    requires_key = False

    def _process(self, text: str) -> str:
        result = []
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                result.append(chr(base + 25 - (ord(ch) - base)))
            else:
                result.append(ch)
        return ''.join(result)

    def encrypt(self, text: str, key: str = "") -> str:
        return self._process(text)

    def decrypt(self, text: str, key: str = "") -> str:
        return self._process(text)  # reciprocal


class ROT13Cipher(Cipher):
    name = "ROT13"
    description = "Caesar with a fixed shift of 13. Used online to hide spoilers. No key needed."
    key_hint = "(no key required)"
    requires_key = False

    def _process(self, text: str) -> str:
        result = []
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                result.append(chr((ord(ch) - base + 13) % 26 + base))
            else:
                result.append(ch)
        return ''.join(result)

    def encrypt(self, text: str, key: str = "") -> str:
        return self._process(text)

    def decrypt(self, text: str, key: str = "") -> str:
        return self._process(text)
