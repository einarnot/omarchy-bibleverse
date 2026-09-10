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

// Calendar day of year, 1–366. UTC date parts avoid DST making the
// difference a fraction of a day.
function dayOfYear(date) {
  var d = date instanceof Date ? date : new Date(date)
  var start = Date.UTC(d.getFullYear(), 0, 1)
  var now = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())
  return Math.floor((now - start) / 86400000) + 1
}

function verseForDate(verses, date) {
  var list = Array.isArray(verses) ? verses : []
  if (list.length === 0) return null
  var index = (dayOfYear(date) - 1) % list.length
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

if (typeof module !== "undefined") {
  module.exports = {
    parseVerses: parseVerses,
    fileUrlToPath: fileUrlToPath,
    dateKey: dateKey,
    dayOfYear: dayOfYear,
    verseForDate: verseForDate,
    barLabel: barLabel,
    verticalLines: verticalLines,
    copyPayload: copyPayload
  }
}
