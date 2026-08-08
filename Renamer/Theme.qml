pragma Singleton
import QtQuick

QtObject {
    // --- System Dark Mode Detection ---
    readonly property bool isDark: Qt.styleHints.colorScheme === Qt.Dark

    // --- Dynamic Semantic Tokens ---
    readonly property color defaultBackground: isDark ? neutral900 : neutral0
    readonly property color columnBackground:  isDark ? neutral800 : neutral100
    readonly property color hoverBackground:   isDark ? "#494949"  : "#cfcfcf"
    readonly property color defaultFont:       isDark ? neutral50  : neutral900
    readonly property color boldFont:          isDark ? neutral0   : neutral800
    readonly property color subtextColor:      isDark ? neutral400 : neutral500
    readonly property color neutralBorder:     isDark ? neutral700 : neutral200
    readonly property color rowOdd:            isDark ? neutral800 : neutral100
    readonly property color rowEven:           isDark ? neutral750 : neutral200
    readonly property color brandFont:         neutral0

    // --- Fixed Brand Palette ---
    readonly property color brandPrimary: "#2563eb"
    readonly property color brand50:      "#eff6ff"
    readonly property color brand100:     "#dbeafe"
    readonly property color brand200:     "#bfdbfe"
    readonly property color brand300:     "#93c5fd"
    readonly property color brand400:     "#60a5fa"
    readonly property color brand500:     "#3b82f6"
    readonly property color brand600:     "#2563eb"
    readonly property color brand700:     "#1d4ed8"
    readonly property color brand800:     "#1e40af"
    readonly property color brand900:     "#1e3a8a"

    // --- Fixed Neutral Palette ---
    readonly property color neutral0:   "#ffffff"
    readonly property color neutral50:  "#fafafa"
    readonly property color neutral100: "#f5f5f5"
    readonly property color neutral150: "#ededed"
    readonly property color neutral200: "#e5e5e5"
    readonly property color neutral300: "#d4d4d4"
    readonly property color neutral400: "#a3a3a3"
    readonly property color neutral500: "#737373"
    readonly property color neutral600: "#525252"
    readonly property color neutral700: "#404040"
    readonly property color neutral750: "#333333"
    readonly property color neutral800: "#262626"
    readonly property color neutral900: "#171717"
    readonly property color neutral950: "#0a0a0a"
}
