#!/usr/bin/env python3
"""news-image-20261119: "The Daily Compass" — Thursday 19 November 2026.

The poster is pre-rendered by tools/render.py into assets/poster.png;
this entrypoint only copies it to /output/entry.png (stdlib only,
no network, deterministic — two runs write identical bytes).
"""
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    shutil.copyfile(os.path.join(ROOT, "assets", "poster.png"),
                    os.path.join(OUT_DIR, "entry.png"))


if __name__ == "__main__":
    main()
