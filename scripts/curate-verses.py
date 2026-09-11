#!/usr/bin/env python3
"""Keep only verses that work as standalone teaching/devotional lines.

Drops genealogies, lists, narrative mid-story lines, dialogue fragments,
ritual minutiae, and other verses that need surrounding context.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "verses.json"
OUT = ROOT / "verses.json"
REPORT = ROOT / "scripts" / "curation-report.json"

WISDOM = {"Proverbs", "Psalms", "Ecclesiastes"}
EPISTLES = {
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Galatians",
    "Ephesians",
    "Philippians",
    "Colossians",
    "1 Thessalonians",
    "2 Thessalonians",
    "1 Timothy",
    "2 Timothy",
    "Titus",
    "Philemon",
    "Hebrews",
    "James",
    "1 Peter",
    "2 Peter",
    "1 John",
    "2 John",
    "3 John",
    "Jude",
}
GOSPELS = {"Matthew", "Mark", "Luke", "John"}
PROPHETS = {
    "Isaiah",
    "Jeremiah",
    "Lamentations",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",
}
TORAH = {"Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"}


def norm(text: str) -> str:
    return (
        str(text or "")
        .strip()
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )


TEACHING = re.compile(
    r"\b("
    r"God|LORD|Lord|Jesus|Christ|Spirit|Father|Savior|Shepherd|"
    r"faith|faithful|believe|belief|love|loved|loves|hope|peace|joy|grace|mercy|"
    r"forgive|forgiveness|repent|repentance|salvation|save|saved|eternal|heaven|"
    r"pray|prayer|worship|praise|bless|blessed|blessing|wisdom|wise|prudent|fool|"
    r"righteous|righteousness|holy|holiness|truth|trust|obey|obedience|"
    r"commandment|neighbor|compassion|kindness|humility|humble|"
    r"rejoice|thanksgiving|thank|grateful|comfort|strengthen|courage|"
    r"light|life|soul|heart|spirit|kingdom|gospel|disciple|reward|"
    r"sin|sins|evil|good|goodness|justice|just|"
    r"fear the|trust in|wait for|seek|ask|knock|serve|"
    r"do not|don't|shall not|you shall|you should|let us|let's|"
    r"whoever|everyone who|he who|she who|those who"
    r")\b",
    re.I,
)

DIVINE = re.compile(
    r"\b(God|LORD|Lord|Jesus|Christ|Holy Spirit|Father|Savior|Shepherd)\b"
)

GENEALOGY = re.compile(
    r"\b("
    r"son of|sons of|daughter of|daughters of|became the father|"
    r"begot|begat|genealogy|generations from|generations of|"
    r"fourteen generations"
    r")\b",
    re.I,
)

NAME_LIST = re.compile(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+)?,\s*){2,}[A-Z]")

NARRATIVE_START = re.compile(
    r"^("
    r"And |Then |"
    r"When he |When she |When they |While he |While she |While they |"
    r"After he |After she |After they |"
    r"As he |As she |As they |"
    r"On that day |In those days |It came to pass|It happened|Meanwhile |"
    r"He went|He came|He took|He rose|He got|He left|He entered|He departed|"
    r"She went|She came|She took|She left|She entered|"
    r"They went|They came|They took|They left|They entered|"
    r"Jesus went|Jesus came|Jesus entered|Jesus left|Jesus sat|Jesus passed|"
    r"Paul went|Paul came|Peter went|Peter came"
    r")",
    re.I,
)

UNANCHORED = re.compile(
    r"^("
    r"He |She |They |It |Him |Her |Them |His |Their |"
    r"But he |But she |But they |For he |For she |For they |For it |"
    r"Therefore he |Therefore she |Therefore they |"
    r"Yet he |Yet they |Also he |Also they"
    r")"
)

DIALOGUE_LEADIN = re.compile(
    r"^("
    r"He said|She said|They said|He answered|She answered|They answered|"
    r"He replied|She replied|He asked|She asked|They asked|"
    r"He spoke|She spoke|They spoke|He cried|She cried|He commanded|saying,"
    r")",
    re.I,
)

JESUS_SPEAKS = re.compile(
    r"\b(Jesus (said|answered|replied|asked|spoke)|he said to (him|her|them))\b",
    re.I,
)

PREPOSITIONAL = re.compile(
    r"^(to |of |from |with |by |into |onto |unto |over |under |about )",
    re.I,
)

RITUAL = re.compile(
    r"\b("
    r"cubits?|shekels?|talents?|ephah|homer|baths?|hin\b|"
    r"bulls?|rams?|he-goats?|turtledoves?|pigeon|"
    r"without blemish|grain offering|burnt offering|sin offering|"
    r"wave offering|peace offering|tent of meeting|nazirite|"
    r"curtain|socket|peg|board|razor shall come|"
    r"feast of unleavened|holy garments|ephod|breastplate|"
    r"atonement money|census of"
    r")\b",
    re.I,
)

GREETING = re.compile(r"(^Greet\b|\bgreet you\b|\bgreet one another\b|\bgreets you\b)", re.I)
ORPHAN_HEADER = re.compile(r"^([;:]|\bon stringed|\baccording to|\bset to\b)", re.I)

HISTORY = re.compile(
    r"\b("
    r"came to Jerusalem|came to Damascus|came to Jericho|came to Bethlehem|"
    r"very great caravan|camels that bore|precious stones|"
    r"took as wife|took to wife|gave him to wife|"
    r"reigned over|began to reign|slept with his fathers|"
    r"was buried|buried him|buried her|"
    r"besieged|encamped|mustered|numbered the people|"
    r"put ashes on|tore her garment|tore his clothes|"
    r"fled from|pursued after|struck him down|"
    r"the child died|she conceived|opened her womb|bore Jacob|bore a son|"
    r"arose, disputing|disguised himself|fight with him|"
    r"came to a cave|camped there|watching from afar|followed Jesus from|"
    r"as he traveled|got close to Damascus|holy anointing oil"
    r")\b",
    re.I,
)

PSALM_HEADER = re.compile(
    r"^For the Chief Musician\b|^A Psalm of\b|^A Song of\b|^A Contemplation of\b|"
    r"^A contemplation by\b|^A Psalm by\b|^A Song by\b",
    re.I,
)

MORAL_LAW = re.compile(
    r"""^['"]?(You shall|You shall not|Honor |Love |Hear, Israel|Remember the|"""
    r"""Don't |Do not |Blessed |I am the LORD)\b""",
    re.I,
)

INCOMPLETE_END = re.compile(r"[,:;]\s*$")
TERMINAL = re.compile(r'[.!?]["\']?\s*$')
QUOTED_SAYING = re.compile(r'"[^"]{12,}"')


def strip_psalm_header(text: str) -> str:
    """Drop superscription clutter so the body can stand alone."""
    t = norm(text)
    # Peel off leading superscription sentences / fragments.
    while True:
        changed = False
        m = re.match(
            r"^(For the Chief Musician\.[^.]*\.\s*"
            r"|For the Chief Musician\.[^.]*?\.?\s+"
            r"|A Psalm by [^.]*\.\s*"
            r"|A Song by [^.]*\.\s*"
            r"|A Contemplation by [^.]*\.\s*"
            r"|A contemplation by [^.]*\.\s*"
            r"|A Psalm of [^.]*\.\s*"
            r"|A Song of [^.]*\.\s*"
            r"|By the sons of Korah\.\s*"
            r"|According to Alamoth\.\s*"
            r"|A Psalm by Asaph\.\s*"
            r")",
            t,
            re.I,
        )
        if m:
            t = t[m.end():].strip()
            changed = True
        # Header without trailing period before body
        m2 = re.match(
            r"^(For the Chief Musician\.?\s*(By the sons of Korah\.?\s*)?(According to Alamoth\.?\s*)?"
            r"|A Psalm by Asaph\.?\s*"
            r"|A contemplation by the sons of Korah\.?\s*)",
            t,
            re.I,
        )
        if m2 and len(m2.group(0).split()) <= 14:
            t = t[m2.end():].strip()
            changed = True
        if not changed:
            break
    # Remove orphaned musical-direction fragments left behind.
    t = re.sub(
        r"^([;:]\s*)?(on stringed instruments\.?\s*|according to [^.]*\.?\s*|set to [^.]*\.?\s*)+",
        "",
        t,
        flags=re.I,
    ).strip()
    return t or norm(text)


def hard_reject(text: str) -> str | None:
    t = norm(text)
    if not t:
        return "empty"
    if re.match(r"^[a-z]", t):
        return "lowercase_continuation"
    if PREPOSITIONAL.match(t):
        return "prepositional_fragment"
    if INCOMPLETE_END.search(t) and not TERMINAL.search(t):
        return "incomplete_sentence"
    if NAME_LIST.match(t):
        return "name_list"
    if GREETING.search(t):
        return "greeting"
    if ORPHAN_HEADER.match(t):
        return "psalm_header_orphan"
    if re.search(r"\bfourteen generations\b", t, re.I):
        return "genealogy"
    if re.search(r"\b(came to a cave|camped there|in Gibeon, the LORD appeared)\b", t, re.I) and not (
        QUOTED_SAYING.search(t) and len(t.split()) <= 35
    ):
        # Keep short clear dream/promise quotes; drop travel framing.
        if not (QUOTED_SAYING.search(t) and TEACHING.search(t) and len(t.split()) <= 30):
            return "historical_narrative"
    if GENEALOGY.search(t) and t.count(",") >= 2:
        return "genealogy"
    if GENEALOGY.search(t) and not DIVINE.search(t):
        return "genealogy"
    if HISTORY.search(t) and not QUOTED_SAYING.search(t):
        return "historical_narrative"
    if RITUAL.search(t) and not MORAL_LAW.match(t):
        return "ritual_or_measure"
    if NARRATIVE_START.match(t) and not QUOTED_SAYING.search(t):
        return "narrative_start"
    if UNANCHORED.match(t) and not DIVINE.search(t):
        return "unanchored_pronoun"
    if DIALOGUE_LEADIN.match(t) and not (QUOTED_SAYING.search(t) and TEACHING.search(t) and DIVINE.search(t)):
        return "dialogue_fragment"
    if not TERMINAL.search(t) and not QUOTED_SAYING.search(t):
        return "no_complete_thought"
    return None


def keep_for_book(book: str, text: str) -> str | None:
    """Return None to keep, or a reason string to drop."""
    t = norm(text)
    teaching = bool(TEACHING.search(t))
    divine = bool(DIVINE.search(t))
    quoted = bool(QUOTED_SAYING.search(t))
    complete = bool(TERMINAL.search(t))

    if book in WISDOM:
        if book == "Psalms":
            t = strip_psalm_header(t)
            teaching = bool(TEACHING.search(t))
            divine = bool(DIVINE.search(t))
            complete = bool(TERMINAL.search(t))
            if len(t.split()) < 6:
                return "psalm_header_only"
        if complete and (teaching or divine or re.search(r"\b(wise|fool|prudent|righteous|wicked)\b", t, re.I)):
            return None
        return "not_teaching_standalone"

    if book in EPISTLES:
        if teaching and complete:
            # Drop pronoun-first lines that clearly depend on prior argument,
            # unless God/Christ is named in the same verse.
            if UNANCHORED.match(t) and not divine:
                return "unanchored_pronoun"
            return None
        return "not_teaching_standalone"

    if book in GOSPELS:
        if HISTORY.search(t) and not re.match(r"^Blessed ", t):
            return "gospel_needs_context"
        if re.match(r"^Blessed ", t):
            return None
        if NARRATIVE_START.match(t):
            # Keep only when a teaching quote dominates the verse.
            if not (quoted and teaching and len(t.split()) <= 45):
                return "gospel_needs_context"
        if quoted and teaching:
            return None
        if JESUS_SPEAKS.search(t) and teaching and (quoted or complete):
            return None
        if teaching and divine and complete and not NARRATIVE_START.match(t):
            return None
        return "gospel_needs_context"

    if book in PROPHETS:
        if divine and teaching and complete and not HISTORY.search(t):
            return None
        if quoted and divine and teaching:
            return None
        return "prophet_needs_context"

    if book in TORAH:
        if RITUAL.search(t) or HISTORY.search(t):
            return "torah_needs_context"
        if MORAL_LAW.match(t) and teaching and complete:
            return None
        if divine and teaching and complete and quoted:
            return None
        # Short clear favor/promise lines
        if divine and teaching and complete and len(t.split()) <= 18:
            return None
        return "torah_needs_context"

    # Remaining historical books / Revelation narrative: only strong quoted teaching.
    quote_text = " ".join(QUOTED_SAYING.findall(t))
    if quoted and divine and TEACHING.search(quote_text) and complete and not HISTORY.search(t):
        return None
    if teaching and divine and complete and re.match(r"^(Don't |Do not |Fear |Trust |Love |Blessed |Rejoice )", t):
        return None
    return "historical_needs_context"


def reject_reason(verse: dict) -> str | None:
    book = verse.get("book", "")
    raw = verse.get("text", "")
    text = strip_psalm_header(raw) if book == "Psalms" else norm(raw)

    hard = hard_reject(text)
    if hard:
        return hard
    return keep_for_book(book, text)


def curate(verses: list[dict]) -> tuple[list[dict], dict]:
    kept: list[dict] = []
    reasons: dict[str, int] = {}
    removed_examples: dict[str, list[str]] = {}

    for v in verses:
        text = strip_psalm_header(v["text"]) if v.get("book") == "Psalms" else v["text"]
        reason = reject_reason({**v, "text": text})
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
            bucket = removed_examples.setdefault(reason, [])
            if len(bucket) < 5:
                bucket.append(f"{v.get('short')}: {norm(v.get('text', ''))[:120]}")
            continue
        kept.append(
            {
                "book": v["book"],
                "chapter": v["chapter"],
                "verse": v["verse"],
                "reference": v["reference"],
                "short": v["short"],
                "text": text if v.get("book") == "Psalms" else v["text"],
            }
        )

    kept.sort(key=lambda x: (x["book"], x["chapter"], x["verse"]))
    return kept, {"removed": reasons, "examples": removed_examples, "kept": len(kept)}


def main() -> int:
    verses = json.loads(SRC.read_text(encoding="utf-8"))
    if not isinstance(verses, list):
        print("verses.json must be a list", file=sys.stderr)
        return 1

    # If already curated, allow rebuilding from sibling full dump when present.
    full = Path("/tmp/bibleverse-build/verses-full.json")
    if full.exists() and len(verses) < 5000:
        verses = json.loads(full.read_text(encoding="utf-8"))

    kept, report = curate(verses)
    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Kept {len(kept)} / {len(verses)} "
        f"(removed {len(verses) - len(kept)})",
        file=sys.stderr,
    )
    for reason, count in sorted(report["removed"].items(), key=lambda kv: -kv[1]):
        print(f"  {count:5d}  {reason}", file=sys.stderr)
    print(f"Wrote {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
