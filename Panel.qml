import QtQuick
import Quickshell
import qs.Commons
import qs.Ui
import "Model.js" as Model

Panel {
  id: root
  moduleName: "einarnot.bibleverse"
  ipcTarget: "einarnot.bibleverse"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  property var verses: []
  property var enVerses: []
  property var langVerses: []
  property var languageMeta: []
  property string language: "en-GB"
  property string languageSetting: "auto"
  property var persistLanguage: null
  property date today: new Date()
  property string userId: Quickshell.env("USER") || Quickshell.env("USERNAME") || "local"
  property string pluginVersion: ""

  readonly property var barIdentity: hostWidget || root
  // Prefer the per-language lists; fall back to the legacy `verses` list as English.
  readonly property var englishVerses: enVerses.length > 0 ? enVerses : verses
  readonly property var activeVerses: Model.selectVerses(englishVerses, langVerses, language)
  readonly property string activeLanguage: Model.activeLanguage(englishVerses, langVerses, language)
  readonly property var verse: Model.verseForDate(activeVerses, today, userId)
  readonly property string copyText: Model.copyPayload(verse, activeLanguage, languageMeta)
  readonly property color contentForeground: bar ? bar.barForeground : Color.foreground
  readonly property string contentFontFamily: bar ? bar.fontFamily : Style.font.family
  readonly property string licenseText: Model.licenseText(activeLanguage, languageMeta)
  readonly property string attributionText: Model.attributionText(activeLanguage)
  readonly property string resolvedVersion: Model.versionFromRegistry(root.bar, root.moduleName) || pluginVersion
  readonly property string versionText: Model.displayVersion(resolvedVersion)
  readonly property var languageOptions: Model.languageOptions(languageMeta)
  readonly property var languageTagOptions: {
    var options = [{
      value: "auto",
      label: languageDropdown.popupOpen ? "sys" : root.language + " *"
    }]
    for (var i = 0; i < Model.SUPPORTED_LANGUAGES.length; i++) {
      var code = Model.SUPPORTED_LANGUAGES[i]
      options.push({ value: code, label: code })
    }
    return options
  }
  readonly property real languageDropdownWidth: languageTagMetrics.width + Style.space(60)

  TextMetrics {
    id: languageTagMetrics
    font.family: root.contentFontFamily
    font.pixelSize: Style.font.caption
    text: "en-GB"
  }

  function open() {
    refresh()
    var version = Model.versionFromRegistry(root.bar, root.moduleName)
    if (version) root.pluginVersion = version
    root.controller.show()
    Qt.callLater(function() {
      if (root.opened) setCenterHoverRevealSuppressed(true)
    })
  }

  function close() {
    setCenterHoverRevealSuppressed(false)
    root.controller.hide()
  }

  function toggle() {
    if (root.opened) root.close()
    else root.open()
  }

  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function")
      return root.bar.switchPanelFrom(root.barIdentity, direction)
    return false
  }

  function setCenterHoverRevealSuppressed(value) {
    if (root.bar && typeof root.bar.setCenterHoverRevealSuppressed === "function")
      root.bar.setCenterHoverRevealSuppressed(value)
    else if (root.bar && "centerHoverRevealSuppressed" in root.bar)
      root.bar.centerHoverRevealSuppressed = value
  }

  function refresh() {
    root.today = new Date()
  }

  function copyVerse() {
    if (root.hostWidget && typeof root.hostWidget.copyVerse === "function") {
      root.hostWidget.copyVerse()
      return
    }
    if (!copyText) return
    Quickshell.execDetached(["bash", "-c", "printf %s " + Util.shellQuote(copyText) + " | wl-copy"])
    Quickshell.execDetached(["omarchy-notification-send", "-g", "󰂺", "Copied " + (verse ? verse.reference : "verse")])
  }

  function askAgent() {
    if (!verse) return

    // Localized interpretation prompt (English instruction, answer in the
    // active language when it is not English).
    var prompt = Model.askPrompt(verse, activeLanguage, languageMeta)

    // omarchy-agent ignores stdin; prompts must go through omarchy-agent-prompt
    // (or `omarchy agent prompt …`), which passes --prompt to the launcher.
    Quickshell.execDetached(["omarchy-agent-prompt", prompt])

    Quickshell.execDetached(["omarchy-notification-send", "-g", "🐟", "Sent to agent: " + verse.reference])
  }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.barIdentity
    bar: root.bar
    open: root.opened
    centerOnBar: true
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(420))
    contentHeight: panel.fittedContentHeight(verseColumn.implicitHeight)

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onMoveRequested: function(dx, dy) {
        // PanelKeyCatcher treats lowercase "l" as a vi-style right move
        // before forwarding it as text. The dropdown owns arrow keys once
        // open; use this otherwise-unused move to open it from the panel.
        if (dx === 1 && !languageDropdown.popupOpen) languageDropdown.open()
      }
      onActivateRequested: root.copyVerse()
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      onTextKey: function(t) {
        if (t === "c" || t === "C") root.copyVerse()
        if (t === "a" || t === "A") root.askAgent()
        if (t === "l" || t === "L") languageDropdown.open()
      }

      Flickable {
        id: verseScroll
        anchors.fill: parent
        contentWidth: width
        contentHeight: verseColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: contentHeight > height

        Column {
          id: verseColumn
          width: verseScroll.width
          spacing: Style.space(12)

          Column {
            width: parent.width
            spacing: Style.space(4)

            Item {
              width: parent.width
              height: Math.max(dailyVerseLabel.implicitHeight, dateLabel.implicitHeight, versionHint.implicitHeight)

              Text {
                id: dailyVerseLabel
                text: Model.dailyVerseLabel(root.activeLanguage) + " · "
                color: Qt.darker(root.contentForeground, 1.4)
                font.family: root.contentFontFamily
                font.pixelSize: Style.font.caption
                font.letterSpacing: 1
              }

              Text {
                id: dateLabel
                anchors.left: dailyVerseLabel.right
                anchors.leftMargin: Style.space(4)
                anchors.right: versionHint.visible ? versionHint.left : parent.right
                anchors.rightMargin: versionHint.visible ? Style.space(8) : 0
                textFormat: Text.PlainText
                text: Qt.locale(root.activeLanguage).toString(root.today, "d MMM yyyy")
                color: Qt.darker(root.contentForeground, 1.4)
                font.family: root.contentFontFamily
                font.pixelSize: Style.font.bodySmall
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
              }

              Text {
                id: versionHint
                anchors.right: parent.right
                anchors.top: parent.top
                visible: root.versionText !== ""
                text: root.versionText
                color: Qt.darker(root.contentForeground, 1.5)
                font.family: root.contentFontFamily
                font.pixelSize: Style.font.caption
                font.letterSpacing: 1
              }
            }

          }

          Text {
            width: parent.width
            textFormat: Text.PlainText
            text: root.verse ? root.verse.reference : "Loading…"
            color: root.contentForeground
            font.family: root.contentFontFamily
            font.pixelSize: Style.font.title
            font.bold: true
            wrapMode: Text.WordWrap
          }

          Text {
            width: parent.width
            textFormat: Text.PlainText
            text: root.verse ? root.verse.text : ""
            color: root.contentForeground
            font.family: root.contentFontFamily
            font.pixelSize: Style.font.subtitle
            wrapMode: Text.WordWrap
            lineHeight: 1.35
          }

          Rectangle {
            width: parent.width
            height: Style.spacing.hairline
            color: root.contentForeground
            opacity: 0.12
          }

          Column {
            width: parent.width
            spacing: Style.space(6)

            Item {
              width: parent.width
              height: Math.max(licenseHint.height, buttonsRow.height)

              Text {
                id: licenseHint
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                text: root.licenseText
                color: Qt.darker(root.contentForeground, 1.5)
                font.family: root.contentFontFamily
                font.pixelSize: Style.font.caption
                font.letterSpacing: 1
              }

              Row {
                id: buttonsRow
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: Style.space(8)

                // Copy Button
                Rectangle {
                  id: copyButton
                  width: copyLabel.implicitWidth + Style.space(16)
                  height: copyLabel.implicitHeight + Style.space(8)
                  radius: Math.min(4, Style.cornerRadius)
                  color: copyArea.containsMouse ? Style.hoverFillFor(root.contentForeground, Color.accent) : "transparent"

                  Text {
                    id: copyLabel
                    anchors.centerIn: parent
                    text: "[C]opy"
                    color: copyArea.containsMouse ? Style.hoverStateColor(root.contentForeground, Color.accent) : root.contentForeground
                    font.family: root.contentFontFamily
                    font.pixelSize: Style.font.caption
                    font.letterSpacing: 1
                  }

                  MouseArea {
                    id: copyArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.copyVerse()
                  }
                }

                // Ask Agent Button
                Rectangle {
                  id: agentButton
                  width: agentLabel.implicitWidth + Style.space(16)
                  height: agentLabel.implicitHeight + Style.space(8)
                  radius: Math.min(4, Style.cornerRadius)
                  color: agentArea.containsMouse ? Style.hoverFillFor(root.contentForeground, Color.accent) : "transparent"

                  Text {
                    id: agentLabel
                    anchors.centerIn: parent
                    text: "[A]sk"
                    color: agentArea.containsMouse ? Style.hoverStateColor(root.contentForeground, Color.accent) : root.contentForeground
                    font.family: root.contentFontFamily
                    font.pixelSize: Style.font.caption
                    font.letterSpacing: 1
                  }

                  MouseArea {
                    id: agentArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.askAgent()
                  }

                  PanelToolTip {
                    visible: agentArea.containsMouse
                    text: "Ask your AI agent to explain this verse"
                    fontFamily: root.contentFontFamily
                  }
                }
              }
            }

            Item {
              width: parent.width
              height: Math.max(languageDropdown.implicitHeight, attributionHint.implicitHeight)

              Text {
                id: attributionHint
                anchors.left: parent.left
                anchors.right: languageControls.left
                anchors.rightMargin: Style.space(8)
                anchors.verticalCenter: parent.verticalCenter
                text: root.attributionText
                color: Qt.darker(root.contentForeground, 1.5)
                font.family: root.contentFontFamily
                font.pixelSize: Style.font.caption
                font.letterSpacing: 1
                wrapMode: Text.WordWrap
              }

              Row {
                id: languageControls
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: Style.space(4)

                Dropdown {
                  id: languageDropdown
                  width: root.languageDropdownWidth
                  showLabel: false
                  value: root.languageSetting
                  options: root.languageTagOptions
                  foreground: Qt.darker(root.contentForeground, 1.4)
                  fontFamily: root.contentFontFamily
                  rowHeight: Style.font.caption + Style.space(8)
                  onChanged: function(value) {
                    if (typeof root.persistLanguage === "function") root.persistLanguage(value)
                  }
                }

                Text {
                  id: languageShortcut
                  text: "[L]"
                  color: languageShortcutArea.containsMouse ? Color.accent : Qt.darker(root.contentForeground, 1.4)
                  font.family: root.contentFontFamily
                  font.pixelSize: Style.font.caption
                  font.letterSpacing: 1
                  anchors.verticalCenter: languageDropdown.verticalCenter

                  MouseArea {
                    id: languageShortcutArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: languageDropdown.open()
                  }
                }
              }
            }
          }
        }
      }
    }
  }

}
