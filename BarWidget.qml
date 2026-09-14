import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Model.js" as Model

BarWidget {
  id: root
  moduleName: "einarnot.bibleverse"

  property var enVerses: []
  property var langVerses: []
  property var languageMeta: []
  property string pluginVersion: ""
  property date today: clock.date
  readonly property string userId: Quickshell.env("USER") || Quickshell.env("USERNAME") || "local"
  readonly property string resolvedVersion: Model.versionFromRegistry(root.bar, root.moduleName) || pluginVersion
  // Language: explicit `language` bar setting wins ("auto" follows the system locale).
  // Anything unsupported falls back to English (see Model.resolveLanguage).
  readonly property string systemLocale: Qt.locale().name || Quickshell.env("LANG") || Quickshell.env("LANGUAGE") || "en-GB"
  readonly property string configuredLanguage: setting("language", "auto")
  readonly property string requestedLanguage: configuredLanguage === "auto" ? systemLocale : configuredLanguage
  readonly property string language: Model.resolveLanguage(requestedLanguage)
  readonly property string versesFileName: Model.versesFileForLanguage(language)
  readonly property var activeVerses: Model.selectVerses(enVerses, langVerses, language)
  readonly property string activeLanguage: Model.activeLanguage(enVerses, langVerses, language)
  readonly property var verse: Model.verseForDate(activeVerses, today, userId)
  readonly property string configuredFormat: setting("format", "short")
  readonly property string displayText: Model.barLabel(verse, configuredFormat) || "Bible"
  readonly property var verticalLines: Model.verticalLines(displayText)
  readonly property string copyText: Model.copyPayload(verse, activeLanguage, languageMeta)

  function refresh() {
    today = new Date()
    versesFileEn.reload()
    versesFileLang.reload()
    languagesFile.reload()
    if (panelLoader.item && panelLoader.item.refresh) panelLoader.item.refresh()
  }

  function copyVerse() {
    if (!copyText) return
    Quickshell.execDetached(["bash", "-c", "printf %s " + Util.shellQuote(copyText) + " | wl-copy"])
    Quickshell.execDetached(["omarchy-notification-send", "-g", "󰂺", "Copied " + (verse ? verse.reference : "verse")])
  }

  function persistLanguage(value) {
    var nextSettings = {}
    var currentSettings = root.settings || {}
    for (var key in currentSettings) nextSettings[key] = currentSettings[key]
    nextSettings.language = String(value || "auto")
    root.settings = nextSettings
    if (root.bar && root.bar.shell && typeof root.bar.shell.updateEntryInline === "function")
      root.bar.shell.updateEntryInline(root.moduleName, nextSettings)
    return true
  }

  readonly property bool opened: panelLoader.item ? panelLoader.item.opened === true : false

  function open() {
    if (panelLoader.item) panelLoader.item.open()
  }

  function close() {
    if (panelLoader.item) panelLoader.item.close()
  }

  function togglePanel() {
    if (panelLoader.item) panelLoader.item.toggle()
  }

  readonly property real openPanelIndicatorWidth: button.labelWidth
  readonly property real openPanelIndicatorHeight: Math.max(Style.space(10), Math.round(Style.bar.iconSlot * 0.55))
  readonly property bool popoutSwitchClosing: panelLoader.item ? panelLoader.item.popoutSwitchClosing === true : false

  function closeForPopoutSwitch() {
    if (panelLoader.item) panelLoader.item.closeForPopoutSwitch()
  }

  function injectPanel() {
    var target = panelLoader.item
    if (!target) return
    if ("bar" in target) target.bar = root.bar
    if ("settings" in target) target.settings = root.settings
    if ("anchorItem" in target) target.anchorItem = button
    if ("hostWidget" in target) target.hostWidget = root
    if ("enVerses" in target) target.enVerses = root.enVerses
    if ("langVerses" in target) target.langVerses = root.langVerses
    if ("languageMeta" in target) target.languageMeta = root.languageMeta
    if ("languageSetting" in target) target.languageSetting = root.configuredLanguage
    if ("persistLanguage" in target) target.persistLanguage = root.persistLanguage
    if ("verses" in target) target.verses = root.activeVerses
    if ("language" in target) target.language = root.language
    if ("today" in target) target.today = root.today
    if ("userId" in target) target.userId = root.userId
    if ("pluginVersion" in target) target.pluginVersion = root.resolvedVersion
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()
  onEnVersesChanged: injectPanel()
  onLangVersesChanged: injectPanel()
  onLanguageMetaChanged: injectPanel()
  onActiveVersesChanged: injectPanel()
  onLanguageChanged: {
    // Drop the previous language until its file loads, so the widget
    // falls back to English instead of showing a stale verse.
    root.langVerses = []
    versesFileLang.reload()
    injectPanel()
  }
  onTodayChanged: injectPanel()
  onPluginVersionChanged: injectPanel()
  onResolvedVersionChanged: injectPanel()

  SystemClock {
    id: clock
    precision: SystemClock.Minutes
    onDateChanged: {
      if (Model.dateKey(date) === Model.dateKey(root.today)) return
      root.today = date
    }
  }

  FileView {
    id: versesFileEn
    path: Model.fileUrlToPath(Qt.resolvedUrl("verses/en-GB.json"))
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.enVerses = Model.parseVerses(text())
    onLoadFailed: root.enVerses = []
  }

  FileView {
    id: versesFileLang
    path: Model.fileUrlToPath(Qt.resolvedUrl(root.versesFileName))
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.langVerses = Model.parseVerses(text())
    onLoadFailed: root.langVerses = []
  }

  FileView {
    id: languagesFile
    path: Model.fileUrlToPath(Qt.resolvedUrl("verses/languages.json"))
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.languageMeta = Model.parseVerses(text())
    onLoadFailed: root.languageMeta = []
  }

  FileView {
    id: manifestFile
    path: Model.fileUrlToPath(Qt.resolvedUrl("manifest.json"))
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.pluginVersion = Model.parseManifestVersion(text())
    onLoadFailed: root.pluginVersion = ""
  }

  Component.onCompleted: Qt.callLater(function() {
    versesFileEn.reload()
    versesFileLang.reload()
    languagesFile.reload()
    manifestFile.reload()
    root.injectPanel()
  })

  Loader {
    id: panelLoader
    active: true
    source: Qt.resolvedUrl("Panel.qml")
    visible: false
    onLoaded: {
      root.injectPanel()
      Qt.callLater(root.injectPanel)
    }
  }

  IpcHandler {
    target: "einarnot.bibleverse"

    function refresh(): void { root.broadcast("refresh") }
    function copy(): void { root.copyVerse() }
    function open(): void { root.open() }
    function close(): void { root.close() }
    function show(): void { root.open() }
    function hide(): void { root.close() }
    function toggle(): void { root.togglePanel() }
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.vertical ? "" : root.displayText
    labelVisible: !root.vertical
    hasVisualContent: root.vertical ? root.verticalLines.length > 0 : text !== ""
    fixedHeight: root.vertical ? root.verticalLines.length * Style.bar.iconSlot : -1
    horizontalMargin: 8.75
    verticalPadding: 8.75
    tooltipText: root.verse ? root.verse.text : "Daily Bible verse"

    onPressed: function(b) {
      if (b === Qt.RightButton) root.copyVerse()
      else if (b === Qt.MiddleButton) root.refresh()
      else root.togglePanel()
    }

    Column {
      visible: root.vertical
      anchors.fill: parent

      Repeater {
        model: root.verticalLines

        OpticalGlyph {
          required property string modelData
          width: button.width
          height: Style.bar.iconSlot
          text: modelData
          fontFamily: button.fontFamily
          fontSize: modelData.length > 3 ? button.fontSize * 0.9 : button.fontSize
          color: button.foreground
        }
      }
    }
  }
}
