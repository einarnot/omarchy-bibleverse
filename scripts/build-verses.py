#!/usr/bin/env python3
"""Build verses.json from OpenBible.info topical data + WEB text.

Verse references come from OpenBible.info topical scores
(https://openbible.info/topics/), licensed CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/

Verse text is World English Bible (WEB) from eBible.org, public domain.
ESV quotations shown on openbible.info pages are NOT redistributed.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "verses.json"
CACHE = Path("/tmp/bibleverse-build")
TOPIC_ZIP_URL = "https://a.openbible.info/data/topic-scores.zip"
WEB_ZIP_URL = "https://ebible.org/Scriptures/engwebp_vpl.zip"
MIN_SCORE = 2

OSIS_TO_WEB = {
    "Gen": "GEN",
    "Exod": "EXO",
    "Lev": "LEV",
    "Num": "NUM",
    "Deut": "DEU",
    "Josh": "JOS",
    "Judg": "JDG",
    "Ruth": "RUT",
    "1Sam": "1SA",
    "2Sam": "2SA",
    "1Kgs": "1KI",
    "2Kgs": "2KI",
    "1Chr": "1CH",
    "2Chr": "2CH",
    "Ezra": "EZR",
    "Neh": "NEH",
    "Esth": "EST",
    "Job": "JOB",
    "Ps": "PSA",
    "Prov": "PRO",
    "Eccl": "ECC",
    "Song": "SNG",
    "Isa": "ISA",
    "Jer": "JER",
    "Lam": "LAM",
    "Ezek": "EZK",
    "Dan": "DAN",
    "Hos": "HOS",
    "Joel": "JOL",
    "Amos": "AMO",
    "Obad": "OBA",
    "Jonah": "JON",
    "Mic": "MIC",
    "Nah": "NAM",
    "Hab": "HAB",
    "Zeph": "ZEP",
    "Hag": "HAG",
    "Zech": "ZEC",
    "Mal": "MAL",
    "Matt": "MAT",
    "Mark": "MRK",
    "Luke": "LUK",
    "John": "JHN",
    "Acts": "ACT",
    "Rom": "ROM",
    "1Cor": "1CO",
    "2Cor": "2CO",
    "Gal": "GAL",
    "Eph": "EPH",
    "Phil": "PHP",
    "Col": "COL",
    "1Thess": "1TH",
    "2Thess": "2TH",
    "1Tim": "1TI",
    "2Tim": "2TI",
    "Titus": "TIT",
    "Phlm": "PHM",
    "Heb": "HEB",
    "Jas": "JAS",
    "1Pet": "1PE",
    "2Pet": "2PE",
    "1John": "1JN",
    "2John": "2JN",
    "3John": "3JN",
    "Jude": "JUD",
    "Rev": "REV",
}

WEB_TO_BOOK = {
    "GEN": ("Genesis", "Gen"),
    "EXO": ("Exodus", "Exod"),
    "LEV": ("Leviticus", "Lev"),
    "NUM": ("Numbers", "Num"),
    "DEU": ("Deuteronomy", "Deut"),
    "JOS": ("Joshua", "Josh"),
    "JDG": ("Judges", "Judg"),
    "RUT": ("Ruth", "Ruth"),
    "1SA": ("1 Samuel", "1 Sam"),
    "2SA": ("2 Samuel", "2 Sam"),
    "1KI": ("1 Kings", "1 Kgs"),
    "2KI": ("2 Kings", "2 Kgs"),
    "1CH": ("1 Chronicles", "1 Chr"),
    "2CH": ("2 Chronicles", "2 Chr"),
    "EZR": ("Ezra", "Ezra"),
    "NEH": ("Nehemiah", "Neh"),
    "EST": ("Esther", "Esth"),
    "JOB": ("Job", "Job"),
    "PSA": ("Psalms", "Ps"),
    "PRO": ("Proverbs", "Prov"),
    "ECC": ("Ecclesiastes", "Eccl"),
    "SNG": ("Song of Solomon", "Song"),
    "ISA": ("Isaiah", "Isa"),
    "JER": ("Jeremiah", "Jer"),
    "LAM": ("Lamentations", "Lam"),
    "EZK": ("Ezekiel", "Ezek"),
    "DAN": ("Daniel", "Dan"),
    "HOS": ("Hosea", "Hos"),
    "JOL": ("Joel", "Joel"),
    "AMO": ("Amos", "Amos"),
    "OBA": ("Obadiah", "Obad"),
    "JON": ("Jonah", "Jonah"),
    "MIC": ("Micah", "Mic"),
    "NAM": ("Nahum", "Nah"),
    "HAB": ("Habakkuk", "Hab"),
    "ZEP": ("Zephaniah", "Zeph"),
    "HAG": ("Haggai", "Hag"),
    "ZEC": ("Zechariah", "Zech"),
    "MAL": ("Malachi", "Mal"),
    "MAT": ("Matthew", "Matt"),
    "MRK": ("Mark", "Mark"),
    "LUK": ("Luke", "Luke"),
    "JHN": ("John", "John"),
    "ACT": ("Acts", "Acts"),
    "ROM": ("Romans", "Rom"),
    "1CO": ("1 Corinthians", "1 Cor"),
    "2CO": ("2 Corinthians", "2 Cor"),
    "GAL": ("Galatians", "Gal"),
    "EPH": ("Ephesians", "Eph"),
    "PHP": ("Philippians", "Phil"),
    "COL": ("Colossians", "Col"),
    "1TH": ("1 Thessalonians", "1 Thess"),
    "2TH": ("2 Thessalonians", "2 Thess"),
    "1TI": ("1 Timothy", "1 Tim"),
    "2TI": ("2 Timothy", "2 Tim"),
    "TIT": ("Titus", "Titus"),
    "PHM": ("Philemon", "Phlm"),
    "HEB": ("Hebrews", "Heb"),
    "JAS": ("James", "Jas"),
    "1PE": ("1 Peter", "1 Pet"),
    "2PE": ("2 Peter", "2 Pet"),
    "1JN": ("1 John", "1 John"),
    "2JN": ("2 John", "2 John"),
    "3JN": ("3 John", "3 John"),
    "JUD": ("Jude", "Jude"),
    "REV": ("Revelation", "Rev"),
}

OSIS_RE = re.compile(r"^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)$")
VPL_RE = re.compile(r"^([1-3A-Z]{3}) (\d+):(\d+) (.+)$")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    print(f"Downloading {url}", file=sys.stderr)
    urllib.request.urlretrieve(url, dest)


def parse_osis(osis: str) -> tuple[str, int, int] | None:
    if "-" in osis:
        return None
    m = OSIS_RE.match(osis)
    if not m:
        return None
    book, chapter, verse = m.group(1), int(m.group(2)), int(m.group(3))
    web = OSIS_TO_WEB.get(book)
    if not web:
        return None
    return web, chapter, verse


def load_refs(path: Path) -> set[tuple[str, int, int]]:
    """Collect unique single-verse refs from OpenBible topic scores."""
    refs: set[tuple[str, int, int]] = set()
    with path.open(encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i == 0 or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            osis, raw_score = parts[1], parts[2]
            parsed = parse_osis(osis)
            if not parsed:
                continue
            try:
                score = int(raw_score)
            except ValueError:
                score = 0
            if score < MIN_SCORE:
                continue
            refs.add(parsed)
    return refs


def load_web(path: Path) -> dict[tuple[str, int, int], str]:
    verses: dict[tuple[str, int, int], str] = {}
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            m = VPL_RE.match(line.rstrip("\n"))
            if not m:
                continue
            book, chapter, verse, text = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
            verses[(book, chapter, verse)] = text.strip()
    return verses


def build() -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    topic_zip = CACHE / "topic-scores.zip"
    web_zip = CACHE / "engwebp_vpl.zip"
    download(TOPIC_ZIP_URL, topic_zip)
    download(WEB_ZIP_URL, web_zip)

    topic_dir = CACHE / "topic-scores"
    web_dir = CACHE / "web_vpl"
    if not (topic_dir / "topic-scores.txt").exists():
        with zipfile.ZipFile(topic_zip) as zf:
            zf.extractall(topic_dir)
    if not (web_dir / "engwebp_vpl.txt").exists():
        with zipfile.ZipFile(web_zip) as zf:
            zf.extractall(web_dir)

    refs = load_refs(topic_dir / "topic-scores.txt")
    web = load_web(web_dir / "engwebp_vpl.txt")

    out: list[dict] = []
    missing = 0
    for key in sorted(refs, key=lambda k: (k[0], k[1], k[2])):
        text = web.get(key)
        if not text:
            missing += 1
            continue
        book_code, chapter, verse = key
        book, short_book = WEB_TO_BOOK[book_code]
        out.append(
            {
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "reference": f"{book} {chapter}:{verse}",
                "short": f"{short_book} {chapter}:{verse}",
                "text": text,
            }
        )

    print(
        f"Built {len(out)} verses from OpenBible refs "
        f"({missing} refs missing from WEB)",
        file=sys.stderr,
    )
    return out


def main() -> int:
    verses = build()
    OUT.write_text(json.dumps(verses, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote raw {OUT} ({len(verses)} verses)", file=sys.stderr)

    # Standalone teaching/devotional pass
    import importlib.util

    curate_path = Path(__file__).with_name("curate-verses.py")
    spec = importlib.util.spec_from_file_location("curate_verses", curate_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
