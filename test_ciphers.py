"""Round-trip tests for all ciphers.

Run with:  python test_ciphers.py
No dependencies beyond the standard library — safe to run on the Pi.
"""
from ciphers import CIPHERS

SAMPLES = [
    "Hello, World!",
    "Attack at dawn",
    "The quick brown fox jumps over the lazy dog",
    "xx marks the spot",          # doubled-X Playfair edge case
    "A",                          # single character
]

KEYS = {
    "caesar":    "7",
    "vigenere":  "SECRET",
    "beaufort":  "ANCHOR",
    "atbash":    "",
    "rot13":     "",
    "railfence": "3",
    "playfair":  "MONARCHY",
    "enigma":    "I II III AAA",
}

# Playfair is lossy by design: it strips punctuation/case, merges J into I,
# and inserts padding letters. So we compare against the cleaned original
# and only check that the decryption *contains* the message letters in order.
LOSSY = {"playfair"}
# Enigma strips punctuation/case but keeps all 26 letters, so its
# round trip must equal the cleaned original exactly.
CLEANED = {"enigma"}


def check(cipher_id, text):
    cipher = CIPHERS[cipher_id]
    key = KEYS[cipher_id]
    enc = cipher.encrypt(text, key)
    dec = cipher.decrypt(enc, key)

    if cipher_id in CLEANED:
        ok = (dec == cipher.clean(text))
    elif cipher_id in LOSSY:
        original = cipher.clean(text).replace('J', 'I')
        # Strip padding candidates from comparison by walking through dec
        # and matching original letters in order.
        it = iter(dec)
        ok = all(ch in it for ch in original)
    else:
        ok = (dec == text)

    status = "ok " if ok else "FAIL"
    print(f"  [{status}] {cipher_id:<10} {text!r:<50} -> {enc!r}")
    return ok


def check_enigma():
    """Historical test vector + the double-step anomaly."""
    e = CIPHERS["enigma"]
    ok = True

    v = e.encrypt("AAAAA", "I II III AAA")
    good = (v == "BDZGO")
    print(f"  [{'ok ' if good else 'FAIL'}] enigma: AAAAA -> {v} (expect BDZGO)")
    ok &= good

    # Middle-rotor double step: window ADU steps ADV, AEW, BFX, BFY
    left, middle, right, _ = e._parse_key("I II III ADU")
    seq = []
    for _ in range(4):
        e._step(left, middle, right)
        seq.append(chr(left.pos+65) + chr(middle.pos+65) + chr(right.pos+65))
    good = (seq == ["ADV", "AEW", "BFX", "BFY"])
    print(f"  [{'ok ' if good else 'FAIL'}] enigma: double-step {seq}")
    ok &= good

    # A letter must never encrypt to itself (reflector property)
    msg = e.clean("THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG" * 5)
    enc = e.encrypt(msg, "IV I V QEV BBB AB CD")
    good = not any(a == b for a, b in zip(msg, enc))
    print(f"  [{'ok ' if good else 'FAIL'}] enigma: never maps a letter to itself")
    ok &= good
    return ok


def check_bad_keys():
    """Bad keys must raise ValueError (not crash), so the UI can show a message."""
    cases = [
        ("caesar", "hello", "abc"),
        ("vigenere", "hello", "123"),
        ("beaufort", "hello", ""),
        ("railfence", "hello", "1"),
        ("playfair", "ODDLENGTH", None),  # None => decrypt odd-length ciphertext
        ("enigma", "hello", "I II VIII AAA"),
        ("enigma", "hello", "I II III AAA AB AC"),
    ]
    all_ok = True
    for cipher_id, text, key in cases:
        try:
            if key is None:
                CIPHERS[cipher_id].decrypt("ABC", "MONARCHY")  # 3 letters, odd
            else:
                CIPHERS[cipher_id].encrypt(text, key)
            print(f"  [FAIL] {cipher_id}: bad key did not raise ValueError")
            all_ok = False
        except ValueError:
            print(f"  [ok ] {cipher_id}: bad key raised ValueError")
    return all_ok


def check_messy_ciphertext():
    """Decrypt should survive lowercase/spaced input (the Playfair bug)."""
    pf = CIPHERS["playfair"]
    enc = pf.encrypt("Attack at dawn", "MONARCHY")
    messy = enc.lower()[:4] + " " + enc.lower()[4:]   # lowercase + a space
    try:
        dec = pf.decrypt(messy, "MONARCHY")
        print(f"  [ok ] playfair: messy ciphertext decrypts -> {dec!r}")
        return True
    except Exception as e:
        print(f"  [FAIL] playfair: messy ciphertext crashed: {e}")
        return False


if __name__ == "__main__":
    ok = True
    print("Round trips:")
    for cid in CIPHERS:
        for s in SAMPLES:
            ok &= check(cid, s)
    print("\nEnigma:")
    ok &= check_enigma()
    print("\nBad keys:")
    ok &= check_bad_keys()
    print("\nMessy ciphertext:")
    ok &= check_messy_ciphertext()
    print("\n" + ("All tests passed." if ok else "SOME TESTS FAILED."))
    raise SystemExit(0 if ok else 1)
