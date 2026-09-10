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
  property date today: new Date()

  readonly property var barIdentity: hostWidget || root
  readonly property var verse: Model.verseForDate(verses, today)
  readonly property string copyText: Model.copyPayload(verse)
  readonly property color contentForeground: bar ? bar.barForeground : Color.foreground
  readonly property string contentFontFamily: bar ? bar.fontFamily : Style.font.family

  function open() {
    refresh()
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
    if (root.bar && "centerHoverRevealSuppressed" in root.bar)
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

    // Construct the prompt with the verse text and request for interpretation
    var prompt = "Please provide common and established interpretations and explanations of the following Bible verse:\n\n" +
                 verse.reference + " (WEB):\n" +
                 "\"" + verse.text + "\"\n\n" +
                 "What are the key themes, historical context, and scholarly interpretations of this verse?"

    // Send to the default agent via IPC
    Quickshell.execDetached(["bash", "-c", "echo " + Util.shellQuote(prompt) + " | omarchy-agent"])

    // Show notification
    Quickshell.execDetached(["omarchy-notification-send", "-g", "󰚀", "Sent to agent: " + verse.reference])
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
      onActivateRequested: root.copyVerse()
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      onTextKey: function(t) {
        if (t === "c" || t === "C") root.copyVerse()
        if (t === "a" || t === "A") root.askAgent()
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

            Text {
              width: parent.width
              text: "VERSE OF THE DAY"
              color: Qt.darker(root.contentForeground, 1.4)
              font.family: root.contentFontFamily
              font.pixelSize: Style.font.caption
              font.letterSpacing: 1
            }

            Text {
              width: parent.width
              textFormat: Text.PlainText
              text: Qt.formatDate(root.today, "dddd, d MMMM yyyy")
              color: Qt.darker(root.contentForeground, 1.4)
              font.family: root.contentFontFamily
              font.pixelSize: Style.font.bodySmall
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

          Item {
            width: parent.width
            height: Math.max(copyHint.height, buttonsRow.height)

            Text {
              id: copyHint
              anchors.left: parent.left
              anchors.verticalCenter: parent.verticalCenter
              text: "WEB · public domain"
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
                  text: "ASK"
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
              }

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
                  text: "COPY"
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
            }
          }
        }
      }
    }
  }
}
