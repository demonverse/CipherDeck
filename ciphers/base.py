from abc import ABC, abstractmethod


class Cipher(ABC):
    name: str = ""
    description: str = ""
    key_hint: str = ""  # shown in UI as placeholder/hint
    requires_key: bool = True  # UI skips the key field when False

    @abstractmethod
    def encrypt(self, text: str, key: str) -> str:
        pass

    @abstractmethod
    def decrypt(self, text: str, key: str) -> str:
        pass

    def clean(self, text: str) -> str:
        """Strip non-alpha, uppercase. Most ciphers want this."""
        return ''.join(c.upper() for c in text if c.isalpha())
