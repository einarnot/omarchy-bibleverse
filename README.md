# Daily Bible Verse

A bar widget for [Omarchy](https://omarchy.org/) that shows today's World English Bible verse. Click it for the full text; right-click copies the verse.

The verse is chosen from a bundled 366-verse list by calendar day, so it stays the same all day, works offline, and needs no API key.

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

## Remove

```sh
omarchy plugin remove einarnot.bibleverse
```

Removal only disables and deletes this plugin checkout. It does not change other bar widgets or rewrite unrelated shell settings.

## License

Plugin code is MIT. Verse text is World English Bible, public domain.
