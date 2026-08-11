from .base import Cipher


class RailFenceCipher(Cipher):
    name = "Rail Fence"
    description = "Writes text in a zigzag across N rails, then reads off row by row."
    key_hint = "Number of rails, e.g. 3"

    def encrypt(self, text: str, key: str) -> str:
        try:
            rails = int(key)
            if rails < 2:
                raise ValueError
        except ValueError:
            raise ValueError("Rail Fence key must be an integer >= 2.")

        fence = [[] for _ in range(rails)]
        rail, direction = 0, 1
        for ch in text:
            fence[rail].append(ch)
            if rail == 0:
                direction = 1
            elif rail == rails - 1:
                direction = -1
            rail += direction
        return ''.join(''.join(r) for r in fence)

    def decrypt(self, text: str, key: str) -> str:
        try:
            rails = int(key)
            if rails < 2:
                raise ValueError
        except ValueError:
            raise ValueError("Rail Fence key must be an integer >= 2.")

        n = len(text)
        # Figure out which rail each position belongs to
        pattern = []
        rail, direction = 0, 1
        for _ in range(n):
            pattern.append(rail)
            if rail == 0:
                direction = 1
            elif rail == rails - 1:
                direction = -1
            rail += direction

        # Work out lengths of each rail
        indices = sorted(range(n), key=lambda i: pattern[i])
        result = [''] * n
        for pos, idx in zip(indices, text):
            result[pos] = idx
        return ''.join(result)
