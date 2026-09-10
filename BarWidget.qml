import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Model.js" as Model

BarWidget {
  id: root
  moduleName: "einarnot.bibleverse"

  property var verses: []
  property date today: clock.date
  readonly property var verse: Model.verseForDate(verses, today)
  readonly property string configuredFormat: setting("format", "short")
  readonly property string displayText: Model.barLabel(verse, configuredFormat) || "Bible"
  readonly property var verticalLines: Model.verticalLines(displayText)
  readonly property string copyText: Model.copyPayload(verse)

  function refresh() {
    today = new Date()
    versesFile.reload()
    if (panelLoader.item && panelLoader.item.refresh) panelLoader.item.refresh()
  }

  function copyVerse() {
    if (!copyText) return
    Quickshell.execDetached(["bash", "-c", "printf %s " + Util.shellQuote(copyText) + " | wl-copy"])
    Quickshell.execDetached(["omarchy-notification-send", "-g", "󰂺", "Copied " + (verse ? verse.reference : "verse")])
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
    if ("verses" in target) target.verses = root.verses
    if ("today" in target) target.today = root.today
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()
  onVersesChanged: injectPanel()
  onTodayChanged: injectPanel()

  SystemClock {
    id: clock
    precision: SystemClock.Minutes
    onDateChanged: {
      if (Model.dateKey(date) === Model.dateKey(root.today)) return
      root.today = date
    }
  }

  FileView {
    id: versesFile
    path: Model.fileUrlToPath(Qt.resolvedUrl("verses.json"))
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.verses = Model.parseVerses(text())
    onLoadFailed: root.verses = []
  }

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
