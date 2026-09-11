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

function copyPayload(verse) {
  if (!verse || !verse.text) return ""
  return '"' + verse.text + '" — ' + verse.reference + " (WEB)"
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
    displayVersion: displayVersion
  }
}
