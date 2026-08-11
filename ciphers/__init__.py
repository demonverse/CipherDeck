from .caesar import CaesarCipher
from .vigenere import VigenereCipher, BeaufortCipher
from .atbash import AtbashCipher, ROT13Cipher
from .railfence import RailFenceCipher
from .playfair import PlayfairCipher
from .enigma import EnigmaCipher

CIPHERS = {
    "caesar":    CaesarCipher(),
    "vigenere":  VigenereCipher(),
    "beaufort":  BeaufortCipher(),
    "atbash":    AtbashCipher(),
    "rot13":     ROT13Cipher(),
    "railfence": RailFenceCipher(),
    "playfair":  PlayfairCipher(),
    "enigma":    EnigmaCipher(),
}
