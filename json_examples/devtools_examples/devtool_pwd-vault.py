"""密码保险库：主口令 + 盐 派生 keystream 的本地加密存储（教学级实现，生产请用 keyring/1Password）。"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

VAULT = Path("vault.enc.json")


import os


def keystream(master: str, salt: bytes, size: int):
    out = b""
    counter = 0
    while len(out) < size:
        out += hashlib.sha256(master.encode() + salt + str(counter).encode()).digest()
        counter += 1
    return out[:size]


def xor(data: bytes, key: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, key))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["add", "get", "list"])
    ap.add_argument("site")
    ap.add_argument("--master", required=True)
    args = ap.parse_args()
    if VAULT.exists():
        blob = json.loads(VAULT.read_text())
        salt, data = bytes.fromhex(blob["salt"]), bytes.fromhex(blob["data"])
        vault = json.loads(xor(data, keystream(args.master, salt, len(data))))
    else:
        salt, vault = os.urandom(16), {}
    if args.mode == "add":
        import getpass
        vault[args.site] = getpass.getpass("密码: ")
    elif args.mode == "get":
        print(vault.get(args.site) or "<未记录>")
    else:
        print("站点:", sorted(vault))
    plain = json.dumps(vault, ensure_ascii=False).encode()
    data = xor(plain, keystream(args.master, salt, len(plain)))
    VAULT.write_text(json.dumps({"salt": salt.hex(), "data": data.hex()}))


if __name__ == "__main__":
    main()
