#!/usr/bin/env python3
"""
Create index.md files for verse_root_dir/01..10
Each index lists links to verses in verses/.
"""

from pathlib import Path
import re

ROOT = Path("docs/verse_root_dir")
VERSE_RE = re.compile(r"v(\d{1,6})\.md$", re.IGNORECASE)

SECTION_TITLES = {
    "01": "First Reply — Investigation of Reality",
    "02": "Second Reply — Determination of the Mantra",
    "03": "Third Reply — Meditation",
    "04": "Fourth Reply — Means to Liberation",
    "05": "Fifth Reply — Supreme Dharma",
    "06": "Sixth Reply — Classification of Vaiṣṇavas",
    "07": "Seventh Reply — Characteristics of the Vaiṣṇava",
    "08": "Eighth Reply — Proper Use of Time",
    "09": "Ninth Reply — Attainment",
    "10": "Tenth Reply — Places Suitable for Residence",
}


def verse_num(p: Path) -> int:
    m = VERSE_RE.search(p.name)
    return int(m.group(1)) if m else 10**9


def main():
    for section in sorted(SECTION_TITLES.keys()):
        sec_dir = ROOT / section
        verses_dir = sec_dir / "verses"
        index_path = sec_dir / "index.md"

        if not verses_dir.is_dir():
            print(f"[SKIP] {verses_dir} not found")
            continue

        verses = sorted(verses_dir.glob("v*.md"), key=verse_num)

        lines = [
            "---",
            "layout: page",
            f'title: "{SECTION_TITLES[section]}"',
            "---",
            "",
            "## Verses (Mūlapāṭha)",
            "",
        ]

        if not verses:
            lines.append("_No verses found in this section._")
        else:
            for v in verses:
                # relative link; GitHub Pages-safe
                lines.append(f"- [{v.stem}](verses/{v.stem}.html)")

        index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[WRITE] {index_path} ({len(verses)} verses)")


if __name__ == "__main__":
    main()
