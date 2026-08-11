from .base import Cipher


class VigenereCipher(Cipher):
    name = "Vigenère"
    description = "Polyalphabetic substitution using a repeating keyword. Much harder to crack than Caesar."
    key_hint = "Keyword, e.g. SECRET"

    def _process(self, text: str, key: str, decrypt: bool) -> str:
        key = self.clean(key)
        if not key:
            raise ValueError("Vigenère key must contain letters.")
        result = []
        key_idx = 0
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                shift = ord(key[key_idx % len(key)]) - ord('A')
                if decrypt:
                    shift = -shift
                result.append(chr((ord(ch) - base + shift) % 26 + base))
                key_idx += 1
            else:
                result.append(ch)
        return ''.join(result)

    def encrypt(self, text: str, key: str) -> str:
        return self._process(text, key, decrypt=False)

    def decrypt(self, text: str, key: str) -> str:
        return self._process(text, key, decrypt=True)


class BeaufortCipher(Cipher):
    name = "Beaufort"
    description = "Reciprocal variant of Vigenère — encrypt and decrypt use the same operation."
    key_hint = "Keyword, e.g. ANCHOR"

    def _process(self, text: str, key: str) -> str:
        key = self.clean(key)
        if not key:
            raise ValueError("Beaufort key must contain letters.")
        result = []
        key_idx = 0
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                k = ord(key[key_idx % len(key)]) - ord('A')
                c = ord(ch.upper()) - ord('A')
                result.append(chr((k - c) % 26 + base))
                key_idx += 1
            else:
                result.append(ch)
        return ''.join(result)

    def encrypt(self, text: str, key: str) -> str:
        return self._process(text, key)

    def decrypt(self, text: str, key: str) -> str:
        return self._process(text, key)  # reciprocal
