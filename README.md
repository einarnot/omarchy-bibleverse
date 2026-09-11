# Daily Bible Verse

A bar widget for [Omarchy](https://omarchy.org/) that shows a daily World English Bible verse. Click it for the full text; right-click copies the verse.

Verses are bundled offline (no API key). References come from [OpenBible.info](https://openbible.info/topics/); the full WEB text ships in `verses.json`.

Each user gets a **random-looking verse that stays fixed for their local calendar day**. Different users (different `$USER`) get different verses on the same day.

## Install

```sh
omarchy plugin add https://github.com/einarnot/omarchy-bibleverse.git --enable
```

Place it on the bar if it did not land where you want:

```sh
omarchy bar put einarnot.bibleverse --section center
```

## Usage

- Left click opens or closes the verse panel
- Right click copies `"text" — Reference (WEB)`
- Middle click reloads the verse list
- In the panel, press `c` or Enter, or click **COPY**
- In the panel, press `a` or click **ASK** to open the default agent with an interpretation prompt
- Escape closes the panel

The bar shows a short reference (`John 3:16`). To show the full book name:

```sh
omarchy bar set einarnot.bibleverse format reference
```

Set it back with `short`.

## Regenerating verses

```sh
python3 scripts/build-verses.py
```

This downloads OpenBible topic scores and the WEB verse-per-line text, collects
unique single-verse references, then curates them down to verses that work
standalone (no mid-story narrative, genealogies, or ritual fragments):

```sh
python3 scripts/build-verses.py   # fetch + build + curate
python3 scripts/curate-verses.py  # re-run curation only
```

## Remove

```sh
omarchy plugin remove einarnot.bibleverse
```

Removal only disables and deletes this plugin checkout. It does not change other bar widgets or rewrite unrelated shell settings.

## License

Plugin code is MIT.

- **Verse text:** World English Bible (WEB), public domain
- **Reference list:** derived from [OpenBible.info](https://openbible.info/topics/) topical data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: single-verse refs only; WEB text instead of ESV quotations shown on OpenBible.info.
