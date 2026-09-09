import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." // Import Theme.qml

ItemDelegate {
    id: root
    width: ListView.view ? ListView.view.width : implicitWidth
    implicitHeight: 32

    property string fileText: ""
    property bool isInput: true
    property bool isSelected: false
    property bool isEven: false
    property bool hasConflict: false
    property bool isDeleted: fileText.startsWith("[DELETE]")

    signal itemClicked(var mouse)

    // Background State Logic
    background: Rectangle {
        color: {
            if (root.isSelected) return Theme.brandPrimary
            if (root.hovered) return Theme.hoverBackground
            if (root.isEven) return Theme.rowEven
            return Theme.rowOdd
        }
    }

    contentItem: RowLayout {
        spacing: 8
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8

        // DEL Badge Indicator
        Rectangle {
            Layout.preferredWidth: 30
            Layout.preferredHeight: 18
            visible: root.isDeleted
            radius: 3
            color: root.isSelected ? Qt.rgba(1, 1, 1, 0.25) : "#FFEBEE"

            Text {
                anchors.centerIn: parent
                text: "TO DELETE"
                font.pixelSize: 9
                font.bold: true
                color: root.isSelected ? Theme.brandFont : "#E53935"
            }
        }

        // CONFLICT Badge Indicator
        Rectangle {
            Layout.preferredWidth: 60
            Layout.preferredHeight: 18
            visible: root.hasConflict
            radius: 3
            color: root.isSelected ? Qt.rgba(1, 1, 1, 0.25) : "#FFF3E0"

            Text {
                anchors.centerIn: parent
                text: "CONFLICT"
                font.pixelSize: 9
                font.bold: true
                color: root.isSelected ? Theme.brandFont : "#E65100"
            }
        }

        // File Path / Name Label
        Text {
            Layout.fillWidth: true
            text: root.fileText
            font.pixelSize: 12
            font.strikeout: root.isDeleted
            color: root.isSelected ? Theme.brandFont : Theme.defaultFont
            elide: Text.ElideMiddle
            verticalAlignment: Text.AlignVCenter
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: (mouse) => root.itemClicked(mouse)
    }
}
