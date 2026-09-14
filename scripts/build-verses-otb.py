#!/usr/bin/env python3
"""Build verses/<lang>.json for all Open Translation Bible languages.

Source: Open Translation Bible (OTB), https://github.com/OpenTranslationBible/open-bible
(launched July 2025 by OpenTranslationBible, https://openbible.uk),
made available under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0).
Only lang/<code>/{json,books.json,lang.json} is fetched, via a filtered
sparse checkout (no PDFs, no markdown).

Pipeline:
  1. Load the complete OTB en-GB text.
  2. Restrict it to the OpenBible.info topical reference set
     (https://openbible.info/topics/, CC BY 4.0) so the daily verses are
     verses people actually look up, then curate down to standalone
     teaching/devotional verses with the shared curation engine
     (scripts/curate-verses.py).
  3. Translate the curated reference set into every OTB language by
     canonical book order (all languages ship the 66 books in order).
  4. Write verses/<code>.json plus verses/languages.json metadata
     (names, verse counts, license, source commit) for attribution.

Markdown quote markers ('> ') and stanza separators ('---') are stripped;
verse text is otherwise unmodified (noted for CC BY-SA change disclosure).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "verses"
REPORT = ROOT / "scripts" / "curation-report-otb.json"
CACHE = Path("/tmp/bibleverse-build")
OTB_REPO = "https://github.com/OpenTranslationBible/open-bible.git"
OTB_DIR = Path(os.environ.get("OTB_CHECKOUT", str(CACHE / "open-bible")))
OTB_URL = "https://github.com/OpenTranslationBible/open-bible"
OTB_LICENSE = "CC BY-SA 4.0"
OTB_LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
OTB_HOME = "https://openbible.uk"

# (code, English name, native name, launch) from the OTB README language table.
LANGUAGES = [
    ("en-GB", "English", "English (British)", "July 2025"),
    ("hi-IN", "Hindi", "हिन्दी", "July 2025"),
    ("fa-IR", "Persian", "فارسی", "July 2025"),
    ("fr-FR", "French", "Français", "December 2025"),
    ("nb-NO", "Norwegian", "Norsk Bokmål", "December 2025"),
    ("de-DE", "German", "Deutsch", "December 2025"),
    ("ar-EG", "Arabic", "العربية", "December 2025"),
    ("ja-JP", "Japanese", "日本語", "December 2025"),
    ("pt-BR", "Portuguese", "Português (Brazilian)", "December 2025"),
    ("es-ES", "Spanish", "Español (Spain)", "December 2025"),
    ("zh-CN", "Chinese", "简体中文", "December 2025"),
    ("id-ID", "Indonesian", "Bahasa Indonesia", "December 2025"),
    ("so-SO", "Somali", "Soomaali", "December 2025"),
    ("he-IL", "Hebrew", "עברית", "February 2026"),
    ("ru-RU", "Russian", "Русский", "February 2026"),
    ("it-IT", "Italian", "Italiano", "February 2026"),
    ("ko-KR", "Korean", "한국어", "February 2026"),
    ("ml-IN", "Malayalam", "മലയാളം", "March 2026"),
    ("da-DK", "Danish", "Dansk", "April 2026"),
    ("fi-FI", "Finnish", "Suomi", "April 2026"),
    ("is-IS", "Icelandic", "Íslenska", "April 2026"),
    ("nl-NL", "Dutch", "Nederlands", "April 2026"),
    ("sv-SE", "Swedish", "Svenska", "April 2026"),
    ("sw-TZ", "Swahili", "Kiswahili", "April 2026"),
]

# English shorts reused from the WEB book table (OTB en-GB uses the same names).
EN_SHORTS = {
    "Genesis": "Gen",
    "Exodus": "Exod",
    "Leviticus": "Lev",
    "Numbers": "Num",
    "Deuteronomy": "Deut",
    "Joshua": "Josh",
    "Judges": "Judg",
    "Ruth": "Ruth",
    "1 Samuel": "1 Sam",
    "2 Samuel": "2 Sam",
    "1 Kings": "1 Kgs",
    "2 Kings": "2 Kgs",
    "1 Chronicles": "1 Chr",
    "2 Chronicles": "2 Chr",
    "Ezra": "Ezra",
    "Nehemiah": "Neh",
    "Esther": "Esth",
    "Job": "Job",
    "Psalms": "Ps",
    "Proverbs": "Prov",
    "Ecclesiastes": "Eccl",
    "Song of Solomon": "Song",
    "Isaiah": "Isa",
    "Jeremiah": "Jer",
    "Lamentations": "Lam",
    "Ezekiel": "Ezek",
    "Daniel": "Dan",
    "Hosea": "Hos",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obad",
    "Jonah": "Jonah",
    "Micah": "Mic",
    "Nahum": "Nah",
    "Habakkuk": "Hab",
    "Zephaniah": "Zeph",
    "Haggai": "Hag",
    "Zechariah": "Zech",
    "Malachi": "Mal",
    "Matthew": "Matt",
    "Mark": "Mark",
    "Luke": "Luke",
    "John": "John",
    "Acts": "Acts",
    "Romans": "Rom",
    "1 Corinthians": "1 Cor",
    "2 Corinthians": "2 Cor",
    "Galatians": "Gal",
    "Ephesians": "Eph",
    "Philippians": "Phil",
    "Colossians": "Col",
    "1 Thessalonians": "1 Thess",
    "2 Thessalonians": "2 Thess",
    "1 Timothy": "1 Tim",
    "2 Timothy": "2 Tim",
    "Titus": "Titus",
    "Philemon": "Phlm",
    "Hebrews": "Heb",
    "James": "Jas",
    "1 Peter": "1 Pet",
    "2 Peter": "2 Pet",
    "1 John": "1 John",
    "2 John": "2 John",
    "3 John": "3 John",
    "Jude": "Jude",
    "Revelation": "Rev",
}

# Norwegian Bokmål shorts (OTB nb-NO book names).
NB_SHORTS = {
    "1 Mosebok": "1 Mos",
    "2 Mosebok": "2 Mos",
    "3 Mosebok": "3 Mos",
    "4 Mosebok": "4 Mos",
    "5 Mosebok": "5 Mos",
    "Josva": "Jos",
    "Dommerne": "Dom",
    "Rut": "Rut",
    "1 Samuelsbok": "1 Sam",
    "2 Samuelsbok": "2 Sam",
    "1 Kongebok": "1 Kong",
    "2 Kongebok": "2 Kong",
    "1 Krønikebok": "1 Krøn",
    "2 Krønikebok": "2 Krøn",
    "Esra": "Esra",
    "Nehemja": "Neh",
    "Ester": "Est",
    "Job": "Job",
    "Salmene": "Sal",
    "Ordspråkene": "Ordsp",
    "Forkynneren": "Fork",
    "Høysangen": "Høy",
    "Jesaja": "Jes",
    "Jeremia": "Jer",
    "Klagesangene": "Klag",
    "Esekiel": "Esek",
    "Daniel": "Dan",
    "Hosea": "Hos",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadja": "Obad",
    "Jona": "Jona",
    "Mika": "Mika",
    "Nahum": "Nah",
    "Habakkuk": "Hab",
    "Sefanja": "Sef",
    "Haggai": "Hag",
    "Sakarja": "Sak",
    "Malaki": "Mal",
    "Matteus": "Matt",
    "Markus": "Mark",
    "Lukas": "Luk",
    "Johannes": "Joh",
    "Apostlenes gjerninger": "Apg",
    "Romerne": "Rom",
    "1 Korinterne": "1 Kor",
    "2 Korinterne": "2 Kor",
    "Galaterne": "Gal",
    "Efeserne": "Ef",
    "Filipperne": "Fil",
    "Kolosserne": "Kol",
    "1 Tessalonikerne": "1 Tess",
    "2 Tessalonikerne": "2 Tess",
    "1 Timoteus": "1 Tim",
    "2 Timoteus": "2 Tim",
    "Titus": "Tit",
    "Filemon": "Flm",
    "Hebreerne": "Hebr",
    "Jakob": "Jak",
    "1 Peter": "1 Pet",
    "2 Peter": "2 Pet",
    "1 Johannes": "1 Joh",
    "2 Johannes": "2 Joh",
    "3 Johannes": "3 Joh",
    "Judas": "Jud",
    "Åpenbaringen": "Åp",
}

# Per-language short tables. Other languages use the full reference as short.
SHORTS = {"en-GB": EN_SHORTS, "nb-NO": NB_SHORTS}


def read_json(path: Path):
    with path.open(encoding="utf-8-sig") as f:
        return json.load(f)


def ensure_otb() -> Path:
    """Fetch the OTB text (filtered sparse checkout: JSON only, no PDFs)."""
    lang_dir = OTB_DIR / "lang"
    if (lang_dir / "en-GB" / "books.json").exists():
        print(f"Reusing {lang_dir}", file=sys.stderr)
        return lang_dir
    CACHE.mkdir(parents=True, exist_ok=True)
    if not (OTB_DIR / ".git").exists():
        print(f"Cloning {OTB_REPO}", file=sys.stderr)
        subprocess.run(
            [
                "git", "clone", "--depth", "1", "--filter=blob:none",
                "--sparse", "--no-checkout", OTB_REPO, str(OTB_DIR),
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(OTB_DIR), "sparse-checkout", "set",
             "--no-cone", "lang/*/*/json/", "lang/*/books.json", "lang/*/lang.json"],
            check=True,
        )
        subprocess.run(["git", "-C", str(OTB_DIR), "checkout"], check=True)
    if not (lang_dir / "en-GB" / "books.json").exists():
        print(f"Could not find OTB text in {lang_dir}", file=sys.stderr)
        raise SystemExit(1)
    return lang_dir


def clean_part(part: str) -> str:
    """Strip markdown quote markers; drop stanza separators."""
    text = str(part or "").strip()
    if text.startswith(">"):
        text = text[1:].strip()
    if text in ("---", "--", "-"):
        return ""
    return text


def load_language(lang_dir: Path, code: str):
    """Return (ordered book names, {(book, chapter, verse): text})."""
    base = lang_dir / code
    ordered_books = list(read_json(base / "books.json").keys())
    verses: dict[tuple[str, int, int], str] = {}
    for book_dir in sorted(base.iterdir()):
        if not book_dir.is_dir():
            continue
        json_dir = book_dir / "json"
        if not json_dir.is_dir():
            continue
        for chapter_file in sorted(json_dir.glob("*.json")):
            data = read_json(chapter_file)
            try:
                chapter = int(data.get("chapter", 0))
            except (TypeError, ValueError):
                continue
            if chapter <= 0:
                continue
            for entry in data.get("verses", []):
                if "verse" not in entry:
                    continue  # headings / separators carry no verse number
                parts = [clean_part(p) for p in entry.get("text", [])]
                text = " ".join(p for p in parts if p).strip()
                if not text:
                    continue
                try:
                    verse = int(entry["verse"])
                except (TypeError, ValueError):
                    continue
                verses[(book_dir.name, chapter, verse)] = text
    # Key by canonical book name (books.json order matches numbered dirs).
    by_name: dict[tuple[str, int, int], str] = {}
    dir_order = _dir_book_order(base)
    for (dirname, chapter, verse), text in verses.items():
        by_name[(dir_order.get(dirname, dirname), chapter, verse)] = text
    return ordered_books, by_name


def _dir_book_order(base: Path) -> dict[str, str]:
    """Map numbered directory name -> canonical book name via books.json order."""
    ordered = list(read_json(base / "books.json").keys())
    dirs = sorted(
        [d for d in base.iterdir() if d.is_dir() and (d / "json").is_dir()],
        key=lambda d: int(re.match(r"^(\d+)", d.name).group(1)),
    )
    mapping = {}
    for directory, book in zip(dirs, ordered):
        mapping[directory.name] = book
    return mapping


def load_curate_module():
    curate_path = Path(__file__).with_name("curate-verses.py")
    spec = importlib.util.spec_from_file_location("curate_verses", curate_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def load_build_module():
    """Reuse the WEB pipeline's topic-score fetching and OSIS mapping."""
    build_path = Path(__file__).with_name("build-verses.py")
    spec = importlib.util.spec_from_file_location("build_verses", build_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def topical_refs(build_mod) -> set[tuple[str, int, int]]:
    """Unique single-verse (book, chapter, verse) refs from OpenBible topics."""
    import zipfile

    topic_zip = CACHE / "topic-scores.zip"
    build_mod.download(build_mod.TOPIC_ZIP_URL, topic_zip)
    topic_dir = CACHE / "topic-scores"
    topic_txt = topic_dir / "topic-scores.txt"
    if not topic_txt.exists():
        with zipfile.ZipFile(topic_zip) as zf:
            zf.extractall(topic_dir)
    refs: set[tuple[str, int, int]] = set()
    for web_code, chapter, verse in build_mod.load_refs(topic_txt):
        entry = build_mod.WEB_TO_BOOK.get(web_code)
        if not entry:
            continue
        refs.add((entry[0], chapter, verse))
    return refs


def otb_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(OTB_DIR), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def main() -> int:
    lang_dir = ensure_otb()
    available = sorted(d.name for d in lang_dir.iterdir() if d.is_dir())
    codes = [code for code, _, _, _ in LANGUAGES if code in available]
    missing_langs = [code for code, _, _, _ in LANGUAGES if code not in available]
    if missing_langs:
        print(f"OTB languages not in checkout (skipped): {missing_langs}", file=sys.stderr)
    if "en-GB" not in codes:
        print("OTB en-GB text is required", file=sys.stderr)
        return 1

    per_lang: dict[str, tuple[list[str], dict]] = {}
    for code in codes:
        ordered_books, verses = load_language(lang_dir, code)
        per_lang[code] = (ordered_books, verses)
        print(f"Loaded {len(verses)} verses for {code}", file=sys.stderr)

    en_order, en_text = per_lang["en-GB"]

    # Restrict to the OpenBible topical set, then curate (shared schema;
    # English book names match OTB en-GB).
    build_mod = load_build_module()
    topics = topical_refs(build_mod)
    print(f"Topical refs: {len(topics)}", file=sys.stderr)
    # Curation input in the shared schema (English book names match OTB en-GB).
    full = [
        {
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "reference": f"{book} {chapter}:{verse}",
            "short": f"{EN_SHORTS.get(book, book)} {chapter}:{verse}",
            "text": en_text[(book, chapter, verse)],
        }
        for (book, chapter, verse) in sorted(
            (ref for ref in topics if ref in en_text),
            key=lambda kv: (en_order.index(kv[0]), kv[1], kv[2]),
        )
    ]
    print(f"Topical refs present in OTB en-GB: {len(full)}", file=sys.stderr)
    curate_mod = load_curate_module()
    kept, report = curate_mod.curate(full)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Kept {len(kept)} / {len(full)}", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    commit = otb_commit()
    meta = []
    for code, english, native, launch in LANGUAGES:
        if code not in per_lang:
            continue
        order, texts = per_lang[code]
        shorts = SHORTS.get(code, {})
        out = []
        skipped = 0
        for entry in kept:
            idx = en_order.index(entry["book"])
            book = order[idx]
            text = texts.get((book, entry["chapter"], entry["verse"]))
            if not text:
                skipped += 1
                continue
            short = shorts.get(book, book)
            out.append(
                {
                    "book": book,
                    "chapter": entry["chapter"],
                    "verse": entry["verse"],
                    "reference": f"{book} {entry['chapter']}:{entry['verse']}",
                    "short": f"{short} {entry['chapter']}:{entry['verse']}",
                    "text": text,
                }
            )
        out.sort(key=lambda v: (order.index(v["book"]), v["chapter"], v["verse"]))
        (OUT_DIR / f"{code}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        try:
            bible_name = read_json(lang_dir / code / "lang.json").get("NAME", "Open Bible")
        except OSError:
            bible_name = "Open Bible"
        meta.append(
            {
                "code": code,
                "english": english,
                "native": native,
                "bibleName": bible_name,
                "launch": launch,
                "books": len(order),
                "verses": len(out),
                "license": OTB_LICENSE,
                "licenseUrl": OTB_LICENSE_URL,
                "source": OTB_URL,
                "sourceCommit": commit,
            }
        )
        print(f"Wrote verses/{code}.json ({len(out)} verses, {skipped} refs missing)", file=sys.stderr)

    (OUT_DIR / "languages.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote verses/languages.json ({len(meta)} languages)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
