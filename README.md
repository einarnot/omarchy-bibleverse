# Daily Bible Verse

A bar widget for [Omarchy](https://omarchy.org/) that shows a daily Bible verse. Click it for the full text; right-click copies the verse.

Verses are bundled offline (no API key) for all 24 Open Translation Bible languages (see below). The reference set comes from [OpenBible.info](https://openbible.info/topics/) topical data, curated down to standalone verses; each language's file lives in `verses/<code>.json` (e.g. `verses/nb-NO.json`), with metadata in `verses/languages.json`.

Each user gets a **random-looking verse that stays fixed for their local calendar day**. Different users (different `$USER`) get different verses on the same day.

## Languages

The widget follows the system locale (`Qt.locale()`, falling back to `$LANG`/`$LANGUAGE`) and defaults to English (`en-GB`) when the locale is not supported. A missing or empty verse file also falls back to English.

| Code | Language | Verses |
| ---- | -------- | ------ |
| `en-GB` | English (British) | 2896 |
| `hi-IN` | Hindi (हिन्दी) | 2896 |
| `fa-IR` | Persian (فارسی) | 2896 |
| `fr-FR` | French (Français) | 2896 |
| `nb-NO` | Norwegian (Norsk Bokmål) | 2890 |
| `de-DE` | German (Deutsch) | 2896 |
| `ar-EG` | Arabic (العربية) | 2711 |
| `ja-JP` | Japanese (日本語) | 2857 |
| `pt-BR` | Portuguese (Português) | 2895 |
| `es-ES` | Spanish (Español) | 2896 |
| `zh-CN` | Chinese (简体中文) | 2631 |
| `id-ID` | Indonesian (Bahasa Indonesia) | 2883 |
| `so-SO` | Somali (Soomaali) | 2896 |
| `he-IL` | Hebrew (עברית) | 2580 |
| `ru-RU` | Russian (Русский) | 2868 |
| `it-IT` | Italian (Italiano) | 2896 |
| `ko-KR` | Korean (한국어) | 2849 |
| `ml-IN` | Malayalam (മലയാളം) | 2772 |
| `da-DK` | Danish (Dansk) | 2896 |
| `fi-FI` | Finnish (Suomi) | 2896 |
| `is-IS` | Icelandic (Íslenska) | 2880 |
| `nl-NL` | Dutch (Nederlands) | 2896 |
| `sv-SE` | Swedish (Svenska) | 2896 |
| `sw-TZ` | Swahili (Kiswahili) | 2896 |

Counts differ because some upstream translations are still missing chapters (e.g. Matthew 22 in `nb-NO`); each language simply rotates over its own available verses. Bare language tags map to the bundled variant (`en` → `en-GB`, `pt` → `pt-BR`, `zh` → `zh-CN`, `no`/`nn` → `nb-NO`).

Override the language manually (e.g. for testing):

```sh
omarchy bar set einarnot.bibleverse language nb-NO   # <code> | auto (default)
```

The panel's clickable language tag opens a selector containing all bundled languages. Choose **Default system language** to return to automatic locale detection. The choice is saved in the widget's bar settings.

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
- Right click copies `"text" — Reference (Translation name)`
- Middle click reloads the verse list
- In the panel, press `c` or Enter, or click **COPY**
- In the panel, press `a` or click **ASK** to open the default agent with an interpretation prompt
- In the panel, press `l` to open the language selector; use Up/Down and Enter to choose a language
- Escape closes the panel

The bar shows a short reference (`John 3:16`). To show the full book name:

```sh
omarchy bar set einarnot.bibleverse format reference
```

Set it back with `short`.

## Regenerating verses

```sh
python3 scripts/build-verses-otb.py   # fetch OTB + curate + build all 24 languages
```

This sparse-clones only the verse JSON from [OpenTranslationBible/open-bible](https://github.com/OpenTranslationBible/open-bible) (cached in `/tmp/bibleverse-build`, reused on later runs; set `OTB_CHECKOUT` to reuse an existing checkout), downloads the OpenBible topic scores, curates the English text down to verses that work standalone (no mid-story narrative, genealogies, or ritual fragments), then translates the curated set into all 24 languages plus `verses/languages.json` metadata:

```sh
python3 scripts/build-verses-otb.py   # full rebuild
```

The legacy English pipeline (World English Bible) is kept for reference:

```sh
python3 scripts/build-verses.py   # fetch + build + curate (WEB, legacy)
python3 scripts/curate-verses.py  # re-run curation only (shared by the OTB build)
```

## Remove

```sh
omarchy plugin remove einarnot.bibleverse
```

Removal only disables and deletes this plugin checkout. It does not change other bar widgets or rewrite unrelated shell settings.

## License

Plugin code is MIT. Verse data is licensed separately (see below); the widget shows a short attribution line naming the active translation, its license, and source.

- **Verse text (all 24 languages):** Open Translation Bible (OTB) by OpenTranslationBible ([openbible.uk](https://openbible.uk)), used under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/) (see [LICENCE.md](https://github.com/OpenTranslationBible/open-bible/blob/main/LICENCE.md)). Source: [github.com/OpenTranslationBible/open-bible](https://github.com/OpenTranslationBible/open-bible) (`lang/<code>`); the exact upstream commit is recorded in `verses/languages.json`. Changes to the source text: restricted to the curated verse subset; Markdown quote markers (`>`) and stanza separators (`---`) removed. The bundled `verses/*.json` files are shared under the same CC BY-SA 4.0 terms.
- **Reference list:** derived from [OpenBible.info](https://openbible.info/topics/) topical data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: single-verse refs only; OTB text instead of the ESV quotations shown on OpenBible.info.
