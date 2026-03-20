import sys
import re

path = r"c:\Users\ethan\Downloads\Projects\CareCRUDV1\ui\styles\main.qss"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

new_styles = """/* ================================================================
   2. CALENDAR WIDGET POPUP
   ================================================================ */
QCalendarWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #FFFFFF;
    min-height: 48px;
    border-bottom: 1px solid #F1F5F9;
}

QCalendarWidget QToolButton {
    color: #2D3748;
    font-size: 15px;
    font-weight: bold;
    padding: 6px;
    border: none;
    border-radius: 8px;
    background: transparent;
}
QCalendarWidget QToolButton:hover {
    background-color: #F0F7F8;
    color: #388087;
}

QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {
    qproperty-icon: none;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    border-radius: 16px;
    font-weight: bold;
    font-size: 16px;
    margin: 4px 12px;
}
QCalendarWidget QToolButton#qt_calendar_prevmonth { qproperty-text: "◀"; }
QCalendarWidget QToolButton#qt_calendar_nextmonth { qproperty-text: "▶"; }

QCalendarWidget QToolButton#qt_calendar_monthbutton {
    font-weight: bold;
    font-size: 16px;
    padding-right: 4px;
}
QCalendarWidget QToolButton#qt_calendar_yearbutton {
    font-weight: bold;
    font-size: 16px;
    padding-left: 4px;
}

QCalendarWidget QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
}
QCalendarWidget QMenu::item:selected {
    background-color: #388087;
    color: #FFFFFF;
    border-radius: 4px;
}
QCalendarWidget QSpinBox {
    background-color: #F8FAFC;
    color: #2D3748;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px 8px;
}

QCalendarWidget QWidget { alternate-background-color: #FFFFFF; }

QCalendarWidget QTableView {
    background-color: #FFFFFF;
    selection-background-color: transparent;
    outline: 0;
    border: none;
    padding: 8px;
}

QCalendarWidget QTableView QHeaderView::section {
    background-color: #FFFFFF;
    color: #718096;
    font-weight: bold;
    font-size: 13px;
    border: none;
    padding: 6px 0px;
}

QCalendarWidget QAbstractItemView:enabled {
    color: #2D3748;
    font-size: 14px;
    background-color: #FFFFFF;
    selection-background-color: transparent;
    selection-color: #2D3748;
    outline: none;
    border: none;
}
QCalendarWidget QAbstractItemView::item { border-radius: 18px; margin: 4px; }
QCalendarWidget QAbstractItemView::item:hover { background-color: #F0F7F8; color: #2D3748; }
QCalendarWidget QAbstractItemView::item:selected { background-color: transparent; }
"""

pattern = r"/\*\s*={64}\s*2\. CALENDAR WIDGET POPUP\s*={64}\s*\*/.*?/\*\s*={64}\s*SCROLL BARS\s*={64}\s*\*/"
replacement = new_styles + "\n\n/* ================================================================\n   SCROLL BARS\n   ================================================================ */"

new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_text)

print("QSS updated fully.")
