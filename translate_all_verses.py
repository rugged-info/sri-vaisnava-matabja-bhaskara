#!/usr/bin/env python3
"""
Batch-translate verse/unit .txt files using OpenAI.

Input file format expected:

SOURCE_PAGES: page_0047.txt

=== मूलपाठः ===
<Devanagari verse text>

Behavior:
- Translates ONLY the text after the marker line "=== मूलपाठः ==="
- Preserves the provenance header verbatim (everything up to and including marker)
- Processes all .txt files in a directory (sorted)
- Writes one output file per input file
- Skips already-translated outputs unless --overwrite is passed
- Verbose logging shows progress + file currently processing

Examples:
  python translate_all_verses.py --input verses_txt --out translations_txt --protocol full --verbose
  python translate_all_verses.py --input verses_txt --out translations_txt --protocol smooth --verbose
  python translate_all_verses.py --input verses_txt --out translations_txt --protocol full --start v000090.txt --verbose
  python translate_all_verses.py --input verses_txt --out translations_txt --protocol full --overwrite --verbose
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from openai import OpenAI


# Robust marker (tolerates spacing)
MULA_MARK_RE = re.compile(r"^===\s*मूलपाठः\s*===$", re.M)


def vlog(enabled: bool, msg: str) -> None:
    if enabled:
        print(msg, flush=True)


def read_unit_txt(path: Path) -> tuple[str, str]:
    """
    Returns (provenance_text, mula_text)
    provenance_text includes the marker line.
    mula_text is everything after the marker.
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    m = MULA_MARK_RE.search(raw)
    if not m:
        raise ValueError("Missing marker line like: === मूलपाठः ===")

    provenance = raw[:m.end()].rstrip() + "\n"
    mula = raw[m.end():].strip()
    if not mula:
        raise ValueError("No verse text found after the marker.")
    return provenance, mula


def prompt_full_protocol(mula: str) -> str:
    return f"""Apply the Sanskrit Translation Protocol to the following Sanskrit verse.

Rules:
- Output EXACTLY these 5 parts in this order, separated by a blank line:
  1) Original Sanskrit (Devanāgarī) — reproduce exactly
  2) IAST transliteration
  3) Word-by-word breakdown: for each word give (IAST form), base/dictionary form,
     and grammatical labels (case/number/gender; person/number/tense/mood/voice;
     indeclinables; compound type such as tatpuruṣa, bahuvrīhi, etc.)
  4) Literal translation (close, with grammatical notes in parentheses)
  5) Smooth English translation
- No extra commentary
- No headings, bullets, or numbering
- Be exact, not paraphrastic

Verse:
{mula}
"""


def prompt_smooth(mula: str) -> str:
    return f"""Translate the following Sanskrit verse.

Output ONLY:
- The original Devanāgarī (exactly as given)
- Then a smooth English translation

No commentary.

Verse:
{mula}
"""


def call_openai_with_retry(
    client: OpenAI,
    model: str,
    prompt: str,
    *,
    max_retries: int = 6,
    verbose: bool = False,
) -> str:
    delay = 2.0
    last_err: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.responses.create(model=model, input=prompt)
            text = (resp.output_text or "").strip()
            if not text:
                raise RuntimeError("Empty response text from API.")
            return text
        except Exception as e:
            last_err = e
            if attempt == max_retries:
                break
            vlog(verbose, f"[WARN] API error (attempt {attempt}/{max_retries}): {e}")
            vlog(verbose, f"[WARN] Sleeping {delay:.1f}s then retrying...")
            time.sleep(delay)
            delay = min(delay * 1.8, 30.0)

    raise RuntimeError(f"API call failed after {max_retries} attempts: {last_err}") from last_err


def iter_txt_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.glob("*.txt"))


def make_output_path(out_dir: Path, input_file: Path) -> Path:
    # Write translated output with same filename into out_dir
    return out_dir / input_file.name


def main():
    ap = argparse.ArgumentParser(description="Batch translate verse/unit .txt files (one API call per file).")
    ap.add_argument("--input", required=True, help="Input .txt file OR directory containing verse .txt files")
    ap.add_argument("--out", required=True, help="Output directory for translated .txt files")
    ap.add_argument("--protocol", choices=["full", "smooth"], default="full", help="Translation protocol")
    ap.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model name")
    ap.add_argument("--verbose", action="store_true", help="Print progress + file start/finish logs")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing translated outputs")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be processed without calling the API")
    ap.add_argument("--start", default=None,
                    help="Start processing at this filename (e.g., v000090.txt). Files before are skipped.")
    ap.add_argument("--sleep", type=float, default=0.0,
                    help="Optional sleep seconds between API calls (helps rate limiting).")

    args = ap.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY is not set in your environment.")
        print("Example (zsh):  export OPENAI_API_KEY='sk-...'\n")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"[ERROR] Input not found: {input_path}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = iter_txt_files(input_path)
    if not files:
        sys.exit("[ERROR] No .txt files found to process.")

    # Optional start-at behavior
    if args.start:
        start_name = Path(args.start).name
        if start_name not in {p.name for p in files}:
            sys.exit(f"[ERROR] --start file not found in input set: {start_name}")
        # Skip until we hit start_name
        started = False
        filtered = []
        for p in files:
            if p.name == start_name:
                started = True
            if started:
                filtered.append(p)
        files = filtered

    client = OpenAI()

    total = len(files)
    translated = 0
    skipped = 0
    failed = 0

    vlog(args.verbose, f"[INFO] Found {total} file(s) to consider.")
    vlog(args.verbose, f"[INFO] Protocol={args.protocol} Model={args.model}")
    vlog(args.verbose, f"[INFO] Output dir: {out_dir}")

    for idx, in_file in enumerate(files, start=1):
        out_file = make_output_path(out_dir, in_file)

        if out_file.exists() and not args.overwrite:
            skipped += 1
            vlog(args.verbose, f"[SKIP {idx}/{total}] {in_file.name} -> exists ({out_file.name})")
            continue

        vlog(args.verbose, f"\n[START {idx}/{total}] {in_file.name}")

        try:
            provenance, mula = read_unit_txt(in_file)

            if args.dry_run:
                vlog(args.verbose, "[DRY] Would call API with verse text below:")
                print(mula)
                vlog(args.verbose, f"[DRY] Would write: {out_file}")
                continue

            prompt = prompt_full_protocol(mula) if args.protocol == "full" else prompt_smooth(mula)

            vlog(args.verbose, f"[CALL] API request for {in_file.name} ...")
            result = call_openai_with_retry(client, args.model, prompt, verbose=args.verbose)
            vlog(args.verbose, f"[DONE] API response received for {in_file.name}")

            out_file.write_text(provenance + "\n\n" + result + "\n", encoding="utf-8")
            translated += 1
            vlog(args.verbose, f"[WRITE] {out_file}")

            if args.sleep and args.sleep > 0:
                vlog(args.verbose, f"[SLEEP] {args.sleep:.2f}s")
                time.sleep(args.sleep)

            vlog(args.verbose, f"[FINISH {idx}/{total}] {in_file.name}")

        except KeyboardInterrupt:
            print("\n[STOP] Interrupted by user (Ctrl-C). Safe to rerun; completed outputs are saved.")
            break
        except Exception as e:
            failed += 1
            print(f"[FAIL {idx}/{total}] {in_file.name}: {e}", file=sys.stderr)

    print("\n[SUMMARY]")
    print(f"  translated: {translated}")
    print(f"  skipped   : {skipped}")
    print(f"  failed    : {failed}")
    print(f"  output dir: {out_dir}")


if __name__ == "__main__":
    main()
