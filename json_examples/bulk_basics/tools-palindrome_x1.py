"""回文判定：'{s}'。"""
def is_palindrome(t):
    t = "".join(ch.lower() for ch in t if ch.isalnum())
    i, j = 0, len(t) - 1
    while i < j:
        if t[i] != t[j]:
            return False
        i += 1
        j -= 1
    return True

samples = "['上海自来水来自海上', 'A man, a plan, a canal: Panama', 'hello']"
for s in samples:
    print(f"{{s!r:>30}} -> {{is_palindrome(s)}}")
