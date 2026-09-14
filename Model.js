function parseVerses(raw) {
  try {
    var data = JSON.parse(String(raw || ""))
    return Array.isArray(data) ? data : []
  } catch (e) {
    return []
  }
}

function fileUrlToPath(url) {
  var value = String(url || "")
  if (value.indexOf("file://") === 0) return decodeURIComponent(value.slice(7))
  return value
}

function dateKey(date) {
  var d = date instanceof Date ? date : new Date(date)
  return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate()
}

// FNV-1a 32-bit. Stable across reloads so the same user+day keeps the same verse.
function hashString(value) {
  var s = String(value || "")
  var h = 2166136261
  for (var i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function normalizeUserId(userId) {
  var id = String(userId || "").trim()
  return id || "local"
}

// Pick a verse that looks random across days/users, but is sticky for the
// whole local calendar day for a given userId (typically $USER).
function verseForDate(verses, date, userId) {
  var list = Array.isArray(verses) ? verses : []
  if (list.length === 0) return null
  var key = normalizeUserId(userId) + "|" + dateKey(date)
  var index = hashString(key) % list.length
  return list[index] || null
}

function barLabel(verse, format) {
  if (!verse) return ""
  return String(format || "short") === "reference" ? String(verse.reference || "") : String(verse.short || verse.reference || "")
}

function verticalLines(label) {
  var text = String(label || "")
  var split = text.lastIndexOf(" ")
  if (split <= 0) return text ? [text] : []
  return [text.slice(0, split), text.slice(split + 1)]
}

// Verse lists are bundled per language under verses/<code>.json, one file
// per Open Translation Bible language. Anything unsupported falls back
// to DEFAULT_LANGUAGE.
var DEFAULT_LANGUAGE = "en-GB"
var SUPPORTED_LANGUAGES = [
  "en-GB", "hi-IN", "fa-IR", "fr-FR", "nb-NO", "de-DE", "ar-EG", "ja-JP",
  "pt-BR", "es-ES", "zh-CN", "id-ID", "so-SO", "he-IL", "ru-RU", "it-IT",
  "ko-KR", "ml-IN", "da-DK", "fi-FI", "is-IS", "nl-NL", "sv-SE", "sw-TZ"
]

// Map locale primary tags to a bundled language. Regional variants fall
// back to the bundled one (e.g. pt-PT -> pt-BR, zh-TW -> zh-CN), and the
// Norwegian macrolanguage ("no") and Nynorsk ("nn") use Bokmål ("nb-NO").
var LANGUAGE_ALIASES = {
  en: "en-GB",
  hi: "hi-IN",
  fa: "fa-IR",
  fr: "fr-FR",
  nb: "nb-NO",
  no: "nb-NO",
  nn: "nb-NO",
  de: "de-DE",
  ar: "ar-EG",
  ja: "ja-JP",
  pt: "pt-BR",
  es: "es-ES",
  zh: "zh-CN",
  id: "id-ID",
  so: "so-SO",
  he: "he-IL",
  ru: "ru-RU",
  it: "it-IT",
  ko: "ko-KR",
  ml: "ml-IN",
  da: "da-DK",
  fi: "fi-FI",
  is: "is-IS",
  nl: "nl-NL",
  sv: "sv-SE",
  sw: "sw-TZ"
}

var DAILY_VERSE_LABELS = {
  "en-GB": "DAILY BIBLE VERSE",
  "hi-IN": "दैनिक बाइबल पद",
  "fa-IR": "آیه روزانه کتاب مقدس",
  "fr-FR": "VERSET BIBLIQUE DU JOUR",
  "nb-NO": "DAGENS BIBELVERS",
  "de-DE": "TAGESBIBELVERS",
  "ar-EG": "آية الكتاب المقدس اليومية",
  "ja-JP": "今日の聖書の言葉",
  "pt-BR": "VERSÍCULO BÍBLICO DIÁRIO",
  "es-ES": "VERSÍCULO BÍBLICO DEL DÍA",
  "zh-CN": "每日圣经经文",
  "id-ID": "AYAT ALKITAB HARIAN",
  "so-SO": "AAYADDA BILBILKA MAALINLAHA",
  "he-IL": "פסוק התנ״ך היומי",
  "ru-RU": "БИБЛЕЙСКИЙ СТИХ ДНЯ",
  "it-IT": "VERSO BIBLICO DEL GIORNO",
  "ko-KR": "오늘의 성경 구절",
  "ml-IN": "ദൈനംദിന ബൈബിൾ വാക്യം",
  "da-DK": "DAGENS BIBELVERS",
  "fi-FI": "PÄIVÄN RAAMATUNKOHTA",
  "is-IS": "BIBLÍUVERS DAGSINS",
  "nl-NL": "BIJBELVERS VAN DE DAG",
  "sv-SE": "DAGENS BIBELVERS",
  "sw-TZ": "AYA YA BIBLIA YA KILA SIKU"
}

// "nb_NO.UTF-8" -> "nb-no", "pt-BR" -> "pt-br", "" -> "".
function normalizeLanguage(tag) {
  var value = String(tag || "").trim()
  if (!value) return ""
  value = value.split("@")[0]
  value = value.split(".")[0]
  value = value.replace(/_/g, "-")
  return value.toLowerCase()
}

// Resolve any locale tag (or explicit setting) to a bundled language,
// defaulting to English when unsupported.
function resolveLanguage(requested, available) {
  var list = Array.isArray(available) ? available : SUPPORTED_LANGUAGES
  var norm = normalizeLanguage(requested)
  var i
  for (i = 0; i < list.length; i++) {
    if (String(list[i]).toLowerCase() === norm) return String(list[i])
  }
  var mapped = LANGUAGE_ALIASES[norm.split("-")[0]] || ""
  for (i = 0; i < list.length; i++) {
    if (String(list[i]).toLowerCase() === mapped.toLowerCase() && mapped) return String(list[i])
  }
  return DEFAULT_LANGUAGE
}

function versesFileForLanguage(language) {
  return "verses/" + resolveLanguage(language, SUPPORTED_LANGUAGES) + ".json"
}

// Metadata entry ({code, english, native, bibleName, ...}) from
// verses/languages.json for a language, or null.
function languageEntry(languages, language) {
  var resolved = resolveLanguage(language, SUPPORTED_LANGUAGES).toLowerCase()
  if (!Array.isArray(languages)) return null
  for (var i = 0; i < languages.length; i++) {
    var entry = languages[i]
    if (entry && String(entry.code || "").toLowerCase() === resolved) return entry
  }
  return null
}

function languageOptions(languages) {
  var options = [{ value: "auto", label: "Default system language" }]
  for (var i = 0; i < SUPPORTED_LANGUAGES.length; i++) {
    var code = SUPPORTED_LANGUAGES[i]
    var entry = languageEntry(languages, code)
    var label = entry && entry.english ? String(entry.english) : code
    options.push({ value: code, label: label + " (" + code + ")" })
  }
  return options
}

// Display name of the translation (for copy payloads and prompts).
function translationLabel(language, languages) {
  var entry = languageEntry(languages, language)
  if (entry && entry.bibleName) return String(entry.bibleName)
  return "OTB"
}

function dailyVerseLabel(language) {
  var resolved = resolveLanguage(language, SUPPORTED_LANGUAGES)
  return DAILY_VERSE_LABELS[resolved] || DAILY_VERSE_LABELS[DEFAULT_LANGUAGE]
}

// Active verse list: requested language when loaded, else English.
function selectVerses(enVerses, langVerses, language) {
  if (resolveLanguage(language, SUPPORTED_LANGUAGES) !== DEFAULT_LANGUAGE &&
      Array.isArray(langVerses) && langVerses.length > 0)
    return langVerses
  return Array.isArray(enVerses) ? enVerses : []
}

// Language actually in effect for the given lists (falls back to English
// when the requested list is missing or empty).
function activeLanguage(enVerses, langVerses, language) {
  if (resolveLanguage(language, SUPPORTED_LANGUAGES) !== DEFAULT_LANGUAGE &&
      Array.isArray(langVerses) && langVerses.length > 0)
    return resolveLanguage(language, SUPPORTED_LANGUAGES)
  return DEFAULT_LANGUAGE
}

function licenseText(language, languages) {
  return translationLabel(language, languages) + " · CC BY-SA 4.0"
}

function attributionText(language) {
  return "OTB " + resolveLanguage(language, SUPPORTED_LANGUAGES) + " · openbible.uk"
}

function askPrompt(verse, language, languages) {
  if (!verse) return ""
  var label = translationLabel(language, languages)
  var prompt = "Please provide common and established interpretations and explanations of the following Bible verse:\n\n" +
    verse.reference + " (" + label + "):\n" +
    "\"" + verse.text + "\"\n\n" +
    "What are the key themes, historical context, and scholarly interpretations of this verse?"
  var entry = languageEntry(languages, language)
  if (entry && entry.english &&
      resolveLanguage(language, SUPPORTED_LANGUAGES) !== DEFAULT_LANGUAGE)
    prompt += "\n\nPlease answer in " + entry.english + "."
  return prompt
}

function copyPayload(verse, language, languages) {
  if (!verse || !verse.text) return ""
  return '"' + verse.text + '" — ' + verse.reference + " (" + translationLabel(language, languages) + ")"
}

// Read plugin version from manifest.json so UI and packaging stay in sync.
function parseManifestVersion(raw) {
  try {
    var data = JSON.parse(String(raw || ""))
    var version = data && data.version != null ? String(data.version).trim() : ""
    return version
  } catch (e) {
    return ""
  }
}

function versionFromRegistry(bar, pluginId) {
  try {
    var plugins = bar && bar.shell && bar.shell.pluginRegistry && bar.shell.pluginRegistry.installedPlugins
    var manifest = plugins && plugins[pluginId]
    var version = manifest && manifest.version != null ? String(manifest.version).trim() : ""
    return version
  } catch (e) {
    return ""
  }
}

function displayVersion(version) {
  var value = String(version || "").trim()
  if (!value) return ""
  return value.charAt(0) === "v" || value.charAt(0) === "V" ? value : "v" + value
}

if (typeof module !== "undefined") {
  module.exports = {
    parseVerses: parseVerses,
    fileUrlToPath: fileUrlToPath,
    dateKey: dateKey,
    hashString: hashString,
    normalizeUserId: normalizeUserId,
    verseForDate: verseForDate,
    barLabel: barLabel,
    verticalLines: verticalLines,
    copyPayload: copyPayload,
    parseManifestVersion: parseManifestVersion,
    versionFromRegistry: versionFromRegistry,
    displayVersion: displayVersion,
    DEFAULT_LANGUAGE: DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES: SUPPORTED_LANGUAGES,
    LANGUAGE_ALIASES: LANGUAGE_ALIASES,
    normalizeLanguage: normalizeLanguage,
    resolveLanguage: resolveLanguage,
    versesFileForLanguage: versesFileForLanguage,
    languageEntry: languageEntry,
    languageOptions: languageOptions,
    translationLabel: translationLabel,
    dailyVerseLabel: dailyVerseLabel,
    selectVerses: selectVerses,
    activeLanguage: activeLanguage,
    licenseText: licenseText,
    attributionText: attributionText,
    askPrompt: askPrompt
  }
}
