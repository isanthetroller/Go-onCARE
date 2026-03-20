from PyQt6.QtWidgets import QCalendarWidget
from PyQt6.QtCore import Qt, QDate, QRect
from PyQt6.QtGui import QColor, QPainter, QPen

class ModernCalendarWidget(QCalendarWidget):
    """
    Subclassed to provide perfect control over cell painting,
    specifically for hovering, selection, and 'today' states
    with a clean, minimalist rounded look.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.LongDayNames)
        # We do NOT setNavigationBarVisible(False) because QDateEdit popup relies on the native bar.

    def paintCell(self, painter, rect, date):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_today = (date == QDate.currentDate())
        is_selected = (date == self.selectedDate())
        is_out_of_month = (date.month() != self.monthShown())

        painter.save()

        size = min(rect.width(), rect.height()) - 8
        highlight_rect = QRect(
            rect.center().x() - size // 2,
            rect.center().y() - size // 2,
            size, size
        )

        if is_selected:
            painter.setBrush(QColor("#388087")) # Modern Teal
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(highlight_rect, size // 2, size // 2)

        if is_selected:
            text_color = QColor("#FFFFFF")
        elif is_out_of_month:
            text_color = QColor("#CBD5E0") # Light grey, dimmed out-of-month dates
        elif is_today:
            text_color = QColor("#D9534F") # Red text for today
        else:
            text_color = QColor("#2D3748") # Dark grey for normal dates

        painter.setPen(text_color)
        font = painter.font()
        font.setPixelSize(14)
        if is_today or is_selected:
            font.setBold(True)
        else:
            font.setBold(False)
            
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(date.day()))
        painter.restore()

def apply_modern_calendar(date_edit):
    """Utility to inject the modern calendar into a QDateEdit."""
    date_edit.setCalendarPopup(True)
    calendar = ModernCalendarWidget()
    date_edit.setCalendarWidget(calendar)

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
                             QScrollArea, QGridLayout, QSizePolicy, QWidget, QLabel)
from PyQt6.QtCore import pyqtSignal

class DayButton(QPushButton):
    def __init__(self, date: QDate, parent=None):
        super().__init__(str(date.day()), parent)
        self.date = date
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: transparent;
                border: none;
                color: #2D3748;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F0F7F8;
            }
            QPushButton:checked {
                background-color: #388087;
                color: white;
                font-weight: bold;
            }
            QPushButton:disabled {
                color: #CBD5E0;
            }
        """)
        self.setCheckable(True)

class ContinuousCalendarWidget(QWidget):
    clicked = pyqtSignal(QDate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_date = None
        self._day_buttons = []
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sticky Header perfectly aligned with the grid
        header_container = QWidget()
        header_container.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E0E0E0;")
        header_layout = QHBoxLayout(header_container)
        # 16 margin on left, 16 on right + 12px for scrollbar area to match perfectly
        header_layout.setContentsMargins(16, 12, 28, 12) 
        header_layout.setSpacing(4)
        
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for d in day_names:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #718096; font-weight: bold; font-size: 13px;")
            lbl.setFixedSize(40, 30)
            header_layout.addWidget(lbl)
            
        main_layout.addWidget(header_container)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: #FFFFFF; }
            QScrollBar:vertical { width: 12px; background: transparent; }
            QScrollBar::handle:vertical { background: #CBD5E0; border-radius: 6px; min-height: 40px; margin: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        self.scroll_content = QFrame()
        self.scroll_content.setStyleSheet("background: #FFFFFF;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 10, 16, 20)
        self.scroll_layout.setSpacing(20)
        
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)
        
        self.populate_calendar()
        
    def populate_calendar(self):
        today = QDate.currentDate()
        start_date = QDate(today.year(), today.month(), 1).addMonths(-1) # 1 month ago
        
        for i in range(12): # show 12 months ahead
            m_date = start_date.addMonths(i)
            
            m_lbl = QLabel(m_date.toString("MMMM yyyy"))
            m_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D3748; padding-top: 10px; padding-left: 4px;")
            self.scroll_layout.addWidget(m_lbl)
            
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(4)
            grid.setContentsMargins(0, 0, 0, 0)
            
            days_in_month = m_date.daysInMonth()
            first_day_of_week = QDate(m_date.year(), m_date.month(), 1).dayOfWeek()
            start_col = (first_day_of_week % 7)
            
            row = 0
            col = start_col
            
            for day in range(1, days_in_month + 1):
                d = QDate(m_date.year(), m_date.month(), day)
                btn = DayButton(d)
                
                if d == QDate.currentDate():
                    btn.setStyleSheet(btn.styleSheet() + "QPushButton { color: #D9534F; font-weight: bold; font-size: 15px; }")
                
                btn.clicked.connect(lambda checked, bd=d, b=btn: self.on_day_clicked(bd, b))
                self._day_buttons.append(btn)
                
                grid.addWidget(btn, row, col)
                col += 1
                if col > 6:
                    col = 0
                    row += 1
                    
            # Add spacer to fill empty trailing grid cells for perfect layout
            for c in range(7):
                grid.setColumnMinimumWidth(c, 40)
            
            self.scroll_layout.addWidget(grid_widget)
            
        self.scroll_layout.addStretch()
        
    def on_day_clicked(self, date, btn):
        for b in self._day_buttons:
            if b.isChecked() and b != btn:
                b.setChecked(False)
        btn.setChecked(True)
        self.selected_date = date
        self.clicked.emit(date)
        
    def setMinimumDate(self, date):
        for btn in self._day_buttons:
            if btn.date < date:
                btn.setEnabled(False)
                
    def setMaximumDate(self, date):
        for btn in self._day_buttons:
            if btn.date > date:
                btn.setEnabled(False)
                
    def setSelectedDate(self, date):
        for btn in self._day_buttons:
            if btn.date == date:
                btn.setChecked(True)
                self.selected_date = date

class CenteredCalendarDialog(QDialog):
    def __init__(self, current_date=None, min_date=None, max_date=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        self.setFixedSize(380, 500)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        container = QFrame()
        container.setObjectName("CenteredCalendarContainer")
        container.setStyleSheet("""
            QFrame#CenteredCalendarContainer {
                background-color: #FFFFFF;
                border: 2px solid #BADFE7;
                border-radius: 12px;
            }
        """)
        
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(6, 6, 6, 12)
        
        self.calendar = ContinuousCalendarWidget(self)
        if min_date: self.calendar.setMinimumDate(min_date)
        if max_date: self.calendar.setMaximumDate(max_date)
        if current_date: self.calendar.setSelectedDate(current_date)
        
        self.calendar.clicked.connect(self.accept)
        c_layout.addWidget(self.calendar)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(80)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-weight: bold; color: #7F8C8D; font-size: 14px; } QPushButton:hover { color: #388087; }")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        c_layout.addLayout(btn_layout)
        main_layout.addWidget(container)
        
    @property
    def selected_date(self):
        return self.calendar.selected_date
