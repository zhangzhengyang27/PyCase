"""gitignore 生成：python xxx.py python node macos > .gitignore"""
import argparse

TEMPLATES = {
    "python": "__pycache__/\n*.py[cod]\n.venv/\n*.egg-info/\n.pytest_cache/\n.mypy_cache/\ndist/",
    "node": "node_modules/\nout/\n*.tsbuildinfo\n.env.local",
    "macos": ".DS_Store\n._*",
    "ide": ".idea/\n.vscode/",
    "python-notebook": ".ipynb_checkpoints/",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stacks", nargs="+", choices=TEMPLATES)
    args = ap.parse_args()
    print("# 由 gitignore-gen 生成")
    for stack in args.stacks:
        print(f"\n# --- {stack} ---\n{TEMPLATES[stack]}")


if __name__ == "__main__":
    main()
