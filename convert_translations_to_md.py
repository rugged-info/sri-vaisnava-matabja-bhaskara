#!/usr/bin/env python3
"""
Convert translated verse .txt files into Jekyll-friendly Markdown verse pages.

This version includes ONLY:
- Verse (Mūlapāṭha)
- Transliteration (IAST)
- Literal Translation
- Smooth Translation

It EXCLUDES:
- संवित्करः
- पदपरामर्शः
"""

import argparse
import re
from pathlib import Path


VERSE_NUM_RE = re.compile(r"v(\d{1,6})", re.IGNORECASE)
SOURCE_RE = re.compile(r"^\s*SOURCE_PAGES\s*:\s*(.+?)\s*$", re.M)


def split_blocks(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocks = re.split(r"\n{2,}", text)
    return [b.strip() for b in blocks if b.strip()]


def parse_translated_txt(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="ignore")

    mnum = VERSE_NUM_RE.search(path.name)
    if not mnum:
        raise ValueError(f"Cannot infer verse number from filename: {path.name}")
    verse_num = int(mnum.group(1))

    msrc = SOURCE_RE.search(raw)
    source_pages = msrc.group(1).strip() if msrc else "(unknown)"

    parts = re.split(r"\n{2,}", raw, maxsplit=1)
    translation_part = parts[1] if len(parts) == 2 else raw

    blocks = split_blocks(translation_part)

    return {
        "verse_num": verse_num,
        "source_pages": source_pages,
        "blocks": blocks,
    }


def make_md_full(verse_num: int, src: str, blocks: list[str]) -> str:
    if len(blocks) < 5:
        raise ValueError(f"Expected 5 blocks, got {len(blocks)}")

    dev, iast, _wordbyword, literal, smooth = blocks[:5]

    lines = [
        "---",
        "layout: page",
        f'title: "Verse {verse_num}"',
        "---",
        "",
        "## Verse — मूलपाठः",
        "",
        "```text",
        dev,
        "```",
        "",
        "---",
        "",
        "## Transliteration (IAST)",
        "",
        "```text",
        iast,
        "```",
        "",
        "---",
        "",
        "## Literal Translation",
        "",
        literal,
        "",
        "---",
        "",
        "## Smooth Translation",
        "",
        smooth,
        "",
        "---",
        "",
        "### Source",
        "",
        f"- SOURCE_PAGES: {src}",
        "",
    ]

    return "\n".join(lines)


def make_md_smooth(verse_num: int, src: str, blocks: list[str]) -> str:
    if len(blocks) < 2:
        raise ValueError(f"Expected 2 blocks, got {len(blocks)}")

    dev, smooth = blocks[:2]

    lines = [
        "---",
        "layout: page",
        f'title: "Verse {verse_num}"',
        "---",
        "",
        "## Verse — मूलपाठः",
        "",
        "```text",
        dev,
        "```",
        "",
        "---",
        "",
        "## Smooth Translation",
        "",
        smooth,
        "",
        "---",
        "",
        "### Source",
        "",
        f"- SOURCE_PAGES: {src}",
        "",
    ]

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Convert translated verse .txt files to Markdown (Ramananda only).")
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--protocol", choices=["full", "smooth"], default="full")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob("*.txt"))
    if not files:
        raise SystemExit(f"No .txt files found in {in_dir}")

    for f in files:
        try:
            data = parse_translated_txt(f)
            verse_num = data["verse_num"]
            blocks = data["blocks"]
            src = data["source_pages"]

            out_path = out_dir / f.with_suffix(".md").name
            if out_path.exists() and not args.overwrite:
                if args.verbose:
                    print(f"[SKIP] {out_path.name}")
                continue

            if args.protocol == "full":
                md = make_md_full(verse_num, src, blocks)
            else:
                md = make_md_smooth(verse_num, src, blocks)

            out_path.write_text(md, encoding="utf-8")
            if args.verbose:
                print(f"[WRITE] {out_path}")

        except Exception as e:
            print(f"[FAIL] {f.name}: {e}")

    print(f"[DONE] Markdown written to {out_dir}")


if __name__ == "__main__":
    main()
