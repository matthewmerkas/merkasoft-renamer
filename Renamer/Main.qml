import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "components"

Window {
    width: 800
    height: 600
    minimumWidth: 800
    minimumHeight: 600
    visible: true
    title: "Merkasoft Renamer v1.0.0"
    color: Theme.defaultBackground

    FileDialog {
        id: fileDialog
        title: "Select files"
        fileMode: FileDialog.OpenFiles
        onAccepted: {
            fileModel.addFiles(selectedFiles)
        }
    }

    Shortcut {
        sequences: [StandardKey.Delete, "Backspace"]
        onActivated: fileModel.deleteSelected()
    }

    Shortcut {
        sequence: StandardKey.SelectAll
        onActivated: fileModel.selectAll()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            // Left Column: File List
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 0
                spacing: 6

                Text {
                    Layout.bottomMargin: 6
                    color: Theme.boldFont
                    text: "Input"
                    font.bold: true
                    font.pixelSize: 16
                }

                RowLayout {
                    id: inputActions
                    spacing: 6

                    Button {
                        text: "+ Add"
                        onClicked: fileDialog.open()
                    }

                    Button {
                        text: "- Remove"
                        enabled: fileList.count > 0 && fileModel.selectedIndices.length > 0
                        onClicked: fileModel.deleteSelected()
                    }

                    Button {
                        text: "✕ Clear All"
                        enabled: fileModel.files.length > 0
                        onClicked: fileModel.clearFiles()
                    }
                }

                Rectangle {
                    id: leftPanel
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Theme.columnBackground
                    clip: true

                    DropArea {
                        id: dropArea
                        anchors.fill: parent

                        onEntered: (drag) => drag.acceptProposedAction()
                        onPositionChanged: (drag) => drag.acceptProposedAction()

                        onDropped: (drop) => {
                            drop.acceptProposedAction()
                            if (drop.hasText && drop.formats.includes("text/uri-list")) {
                                let rawUriList = drop.getDataAsString("text/uri-list")
                                fileModel.addFiles(rawUriList)
                            } else {
                                let urls = drop.urls
                                fileModel.addFiles(urls)
                            }
                        }
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0

                        ListView {
                            id: fileList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            focus: true
                            model: fileModel.inputListModel

                            property int activeIndex: 0
                            property int lastCount: 0
                            readonly property int pageSize: Math.max(1, Math.floor(fileList.height / 32))

                            onCountChanged: {
                                if (count > lastCount) {
                                    Qt.callLater(fileList.positionViewAtEnd)
                                }
                                lastCount = count

                                if (count > 0) {
                                    activeIndex = Math.min(activeIndex, count - 1)
                                } else {
                                    activeIndex = 0
                                }
                            }

                            Keys.onPressed: (event) => {
                                if (count === 0) return
                                let isShift = (event.modifiers & Qt.ShiftModifier) !== 0

                                switch (event.key) {
                                case Qt.Key_Up:
                                    {
                                        let newIndex = Math.max(0, activeIndex - 1)
                                        activeIndex = newIndex
                                        currentIndex = newIndex
                                        fileModel.handleSelection(newIndex, false, isShift)
                                        positionViewAtIndex(newIndex, ListView.Contain)
                                        event.accepted = true
                                        break
                                    }
                                case Qt.Key_Down:
                                    {
                                        let newIndex = Math.min(count - 1, activeIndex + 1)
                                        activeIndex = newIndex
                                        currentIndex = newIndex
                                        fileModel.handleSelection(newIndex, false, isShift)
                                        positionViewAtIndex(newIndex, ListView.Contain)
                                        event.accepted = true
                                        break
                                    }
                                case Qt.Key_Home:
                                    {
                                        activeIndex = 0
                                        currentIndex = 0
                                        fileModel.handleSelection(0, false, isShift)
                                        positionViewAtIndex(0, ListView.Beginning)
                                        event.accepted = true
                                        break
                                    }
                                case Qt.Key_End:
                                    {
                                        let targetIndex = count - 1
                                        activeIndex = targetIndex
                                        currentIndex = targetIndex
                                        fileModel.handleSelection(targetIndex, false, isShift)
                                        positionViewAtIndex(targetIndex, ListView.End)
                                        event.accepted = true
                                        break
                                    }
                                case Qt.Key_PageUp:
                                    {
                                        let targetIndex = Math.max(0, activeIndex - pageSize)
                                        activeIndex = targetIndex
                                        currentIndex = targetIndex
                                        fileModel.handleSelection(targetIndex, false, isShift)
                                        positionViewAtIndex(targetIndex, ListView.Contain)
                                        event.accepted = true
                                        break
                                    }
                                case Qt.Key_PageDown:
                                    {
                                        let targetIndex = Math.min(count - 1, activeIndex + pageSize)
                                        activeIndex = targetIndex
                                        currentIndex = targetIndex
                                        fileModel.handleSelection(targetIndex, false, isShift)
                                        positionViewAtIndex(targetIndex, ListView.Contain)
                                        event.accepted = true
                                        break
                                    }
                                }
                            }

                            footer: Rectangle {
                                id: dropRegion
                                width: fileList.width
                                property int delegateHeight: 32
                                property int itemsTotalHeight: fileList.count * delegateHeight
                                height: Math.max(80, fileList.height - itemsTotalHeight)
                                color: dropMouseArea.containsMouse ? Theme.hoverBackground : "transparent"

                                Rectangle {
                                    anchors.top: parent.top
                                    width: parent.width
                                    height: 1
                                    color: Theme.columnBackground
                                    visible: fileList.count > 0
                                }

                                MouseArea {
                                    id: dropMouseArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        fileList.forceActiveFocus()
                                        fileDialog.open()
                                    }
                                }

                                ColumnLayout {
                                    anchors.centerIn: parent
                                    spacing: 4

                                    Text {
                                        Layout.alignment: Qt.AlignHCenter
                                        text: fileList.count === 0
                                              ? "+ Drag & Drop files here"
                                              : "+ Drag & Drop or click to add more"
                                        font.pixelSize: 13
                                        font.bold: fileList.count === 0
                                        color: dropArea.containsDrag ? "transparent" : Theme.boldFont
                                    }

                                    Text {
                                        Layout.alignment: Qt.AlignHCenter
                                        visible: fileList.count === 0
                                        text: "or click anywhere to browse"
                                        font.pixelSize: 11
                                        color: dropArea.containsDrag ? "transparent" : Theme.defaultFont
                                    }
                                }
                            }

                            delegate: FileItemDelegate {
                                fileText: model.fileName
                                isInput: true
                                isEven: model.isEven
                                isSelected: model.isSelected

                                onItemClicked: (mouse) => {
                                    fileList.forceActiveFocus()
                                    fileList.activeIndex = index
                                    let isCtrl = (mouse.modifiers & Qt.ControlModifier) !== 0
                                    let isShift = (mouse.modifiers & Qt.ShiftModifier) !== 0
                                    fileModel.handleSelection(index, isCtrl, isShift)
                                }
                            }

                            ScrollBar.vertical: ScrollBar {}
                        }
                    }
                }
            }

            // Right Column: Output / Strategy Controls
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 0
                spacing: 6

                Text {
                    Layout.bottomMargin: 6
                    color: Theme.boldFont
                    text: "Output"
                    font.bold: true
                    font.pixelSize: 16
                }

                RowLayout {
                    id: outputActions
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    spacing: 6

                    ComboBox {
                        id: strategyCombo
                        Layout.preferredWidth: 120
                        Layout.alignment: Qt.AlignVCenter
                        model: fileModel.strategies
                        textRole: "label"
                        valueRole: "id"

                        onCurrentValueChanged: {
                            if (currentValue) {
                                fileModel.setStrategyKey(currentValue)
                            }
                        }
                    }

                    StackLayout {
                        id: strategyStack
                        Layout.fillWidth: true
                        Layout.fillHeight: false
                        Layout.alignment: Qt.AlignVCenter

                        property string activeKey: strategyCombo.currentValue || ""
                        property string sharedUtcOffset: "+10:00"

                        currentIndex: {
                            for (var i = 0; i < children.length; i++) {
                                var childId = children[i].strategyId
                                if (childId === activeKey || (childId === "replace" && activeKey.startsWith("replace"))) {
                                    return i
                                }
                            }
                            return 0
                        }

                        // Panel: Date
                        RowLayout {
                            property string strategyId: "date"
                            spacing: 8

                            SpinBox {
                                from: 1
                                to: 9999
                                value: 1
                                editable: true
                                onValueChanged: fileModel.setStartNumber(value)
                            }

                            Text {
                                text: "UTC"
                                color: Theme.defaultFont
                                font.pixelSize: 12
                                leftPadding: 5
                            }

                            TextField {
                                text: strategyStack.sharedUtcOffset
                                Layout.preferredWidth: 70
                                selectByMouse: true
                                onTextChanged: {
                                    if (strategyStack.sharedUtcOffset !== text) {
                                        strategyStack.sharedUtcOffset = text
                                    }
                                    fileModel.setUtcOffset(text)
                                }
                            }
                        }

                        // Panel: Sequential
                        RowLayout {
                            property string strategyId: "sequential"
                            spacing: 8

                            SpinBox {
                                from: 1
                                to: 9999
                                value: 1
                                editable: true
                                onValueChanged: fileModel.setStartNumber(value)
                            }

                            Text {
                                text: "UTC"
                                color: Theme.defaultFont
                                font.pixelSize: 12
                                leftPadding: 5
                            }

                            TextField {
                                text: strategyStack.sharedUtcOffset
                                Layout.preferredWidth: 70
                                selectByMouse: true
                                onTextChanged: {
                                    if (strategyStack.sharedUtcOffset !== text) {
                                        strategyStack.sharedUtcOffset = text
                                    }
                                    fileModel.setUtcOffset(text)
                                }
                            }
                        }

                        // Panel: Replace
                        RowLayout {
                            property string strategyId: "replace"
                            spacing: 6

                            TextField {
                                id: searchField
                                placeholderText: "Find"
                                Layout.preferredWidth: 125
                                selectByMouse: true
                                text: fileModel.searchPattern
                                onTextChanged: fileModel.setSearchPattern(text)
                            }

                            TextField {
                                id: replaceField
                                placeholderText: "Replace"
                                Layout.preferredWidth: 125
                                selectByMouse: true
                                text: fileModel.replacePattern
                                onTextChanged: fileModel.setReplacePattern(text)
                            }

                            // CheckBox {
                            //     id: regexCheckbox
                            //     text: "Regex"
                            //     checked: fileModel.useRegex
                            //     onCheckedChanged: fileModel.setUseRegex(checked)
                            // }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Theme.columnBackground

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8

                        ListView {
                            id: outputList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: fileModel.outputListModel
                            clip: true

                            property int lastCount: 0
                            onCountChanged: {
                                if (count > lastCount) {
                                    Qt.callLater(outputList.positionViewAtEnd)
                                }
                                lastCount = count
                            }

                            delegate: FileItemDelegate {
                                fileText: model.fileName
                                isInput: false
                                isEven: model.isEven
                                isSelected: false
                            }

                            ScrollBar.vertical: ScrollBar {}
                        }
                    }
                }
            }
        }

        // Bottom Action Bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                ProgressBar {
                    id: progressBar
                    Layout.fillWidth: true
                    Layout.preferredHeight: actionButton.implicitHeight
                    value: fileModel.progressValue

                    background: Rectangle {
                        implicitHeight: actionButton.implicitHeight
                        color: Theme.columnBackground
                        clip: true
                    }

                    contentItem: Item {
                        implicitHeight: actionButton.implicitHeight

                        Rectangle {
                            width: progressBar.visualPosition * parent.width
                            height: parent.height
                            color: Theme.brandPrimary
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        text: fileModel.statusMessage
                        font.pixelSize: 12
                        font.weight: Font.Medium
                        color: Theme.brandFont
                        elide: Text.ElideRight
                        width: parent.width - 16
                        horizontalAlignment: Text.AlignHCenter
                        z: 1
                    }
                }
            }

            Button {
                id: actionButton
                text: fileModel.isProcessing ? "Cancel" : "Process Files"
                enabled: fileModel.isProcessing || fileList.count > 0
                onClicked: {
                    if (fileModel.isProcessing) {
                        fileModel.cancelProcessing()
                    } else {
                        fileModel.processFiles()
                    }
                }
            }
        }
    }
}
