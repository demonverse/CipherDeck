from .base import Cipher


class PlayfairCipher(Cipher):
    name = "Playfair"
    description = "Digraph substitution using a 5×5 key square. I=J. Used by British military in WW1."
    key_hint = "Keyword, e.g. MONARCHY"

    def _build_square(self, key: str):
        key = self.clean(key).replace('J', 'I')
        seen, square = set(), []
        for ch in key + 'ABCDEFGHIKLMNOPQRSTUVWXYZ':
            if ch not in seen:
                seen.add(ch)
                square.append(ch)
        grid = [square[i*5:(i+1)*5] for i in range(5)]
        pos = {ch: (r, c) for r, row in enumerate(grid) for c, ch in enumerate(row)}
        return grid, pos

    def _prepare(self, text: str) -> list:
        text = self.clean(text).replace('J', 'I')
        pairs = []
        i = 0
        while i < len(text):
            a = text[i]
            # Pad with X, but use Q when the letter itself is X —
            # a pair of identical letters can't go through the square.
            pad = 'Q' if a == 'X' else 'X'
            if i + 1 == len(text):
                pairs.append((a, pad))
                i += 1
            elif text[i] == text[i+1]:
                pairs.append((a, pad))
                i += 1
            else:
                pairs.append((a, text[i+1]))
                i += 2
        return pairs

    def _apply(self, pairs, grid, pos, decrypt: bool) -> str:
        step = -1 if decrypt else 1
        result = []
        for a, b in pairs:
            ra, ca = pos[a]
            rb, cb = pos[b]
            if ra == rb:
                result += [grid[ra][(ca + step) % 5], grid[rb][(cb + step) % 5]]
            elif ca == cb:
                result += [grid[(ra + step) % 5][ca], grid[(rb + step) % 5][cb]]
            else:
                result += [grid[ra][cb], grid[rb][ca]]
        return ''.join(result)

    def encrypt(self, text: str, key: str) -> str:
        grid, pos = self._build_square(key)
        return self._apply(self._prepare(text), grid, pos, decrypt=False)

    def decrypt(self, text: str, key: str) -> str:
        grid, pos = self._build_square(key)
        text = self.clean(text).replace('J', 'I')
        if not text:
            raise ValueError("Playfair ciphertext must contain letters.")
        if len(text) % 2 != 0:
            raise ValueError("Playfair ciphertext must have an even number of letters.")
        pairs = [(text[i], text[i+1]) for i in range(0, len(text), 2)]
        return self._apply(pairs, grid, pos, decrypt=True)
