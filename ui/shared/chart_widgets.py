"""Reusable chart widgets for CareCRUD analytics & dashboard.

Contains:
    BarChartWidget   – simple horizontal bar chart (used by Dashboard)
    PieChartWidget   – donut / pie chart (used by Analytics)
    HBarChartWidget  – horizontal bar chart with colour per bar (Analytics)
"""

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath


# ── Colour palettes ───────────────────────────────────────────────────
CONDITION_COLORS = ["#388087", "#6FB3B8", "#BADFE7", "#C2EDCE", "#E8B931", "#D9534F", "#7F8C8D"]
STATUS_COLORS    = {"Completed": "#5CB85C", "Confirmed": "#388087", "Pending": "#E8B931", "Cancelled": "#D9534F"}
DEPT_COLORS      = ["#388087", "#6FB3B8", "#BADFE7", "#C2EDCE", "#E8B931", "#7F8C8D", "#D9534F", "#5CB85C"]
DEMO_COLORS      = {"0–17": "#6FB3B8", "18–35": "#388087", "36–50": "#BADFE7", "51–65": "#C2EDCE", "65+": "#E8B931"}
RETENTION_COLORS = {"new_patients": "#6FB3B8", "returning_patients": "#388087"}


# ── Tiny bar-chart widget ─────────────────────────────────────────────
class BarChartWidget(QWidget):
    """Simple horizontal bar chart painted via QPainter."""

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self._max = max(v for _, v in self._data) if self._data else 1
        self.setMinimumHeight(max(len(self._data) * 38 + 10, 50))

    def set_data(self, data):
        self._data = data
        self._max = max(v for _, v in data) if data else 1
        self.setMinimumHeight(max(len(data) * 38 + 10, 50))
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        bar_h, spacing, label_w, padding_r = 22, 38, 80, 40
        for i, (label, value) in enumerate(self._data):
            y = i * spacing + 6
            painter.setPen(QColor("#7F8C8D"))
            painter.setFont(self.font())
            painter.drawText(0, y, label_w, bar_h, Qt.AlignmentFlag.AlignVCenter, label)
            bar_x = label_w + 8
            max_bar_w = w - bar_x - padding_r
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#F6F6F2"))
            painter.drawRoundedRect(bar_x, y + 2, int(max_bar_w), bar_h - 4, 6, 6)
            fill_w = int(max_bar_w * value / self._max) if self._max else 0
            painter.setBrush(QColor("#388087"))
            painter.drawRoundedRect(bar_x, y + 2, fill_w, bar_h - 4, 6, 6)
            painter.setPen(QColor("#2C3E50"))
            painter.drawText(bar_x + int(max_bar_w) + 6, y, 34, bar_h,
                             Qt.AlignmentFlag.AlignVCenter, str(value))
        painter.end()


# ── Pie Chart Widget ──────────────────────────────────────────────────
class PieChartWidget(QWidget):
    def __init__(self, data: list[tuple[str, int, str]], *, donut: bool = True, parent=None):
        super().__init__(parent)
        self._data = data; self._donut = donut
        self._total = sum(v for _, v, _ in data)
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data):
        self._data = data; self._total = sum(v for _, v, _ in data); self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height()) - 20
        x, y = (self.width() - size) / 2, (self.height() - size) / 2
        rect = QRectF(x, y, size, size)
        start = 90 * 16
        for _, value, color in self._data:
            span = int(value / self._total * 360 * 16) if self._total else 0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPie(rect, start, -span)
            start -= span
        if self._donut:
            hole = size * 0.52; hx, hy = (self.width()-hole)/2, (self.height()-hole)/2
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(QRectF(hx, hy, hole, hole))
        painter.end()


# ── Horizontal Bar Chart ──────────────────────────────────────────────
class HBarChartWidget(QWidget):
    def __init__(self, data: list[tuple[str, int, str]], parent=None):
        super().__init__(parent)
        self._data = data
        self._max = max(v for _, v, _ in data) if data else 1
        self.setMinimumHeight(len(data) * 38 + 10)

    def set_data(self, data):
        self._data = data
        self._max = max(v for _, v, _ in data) if data else 1
        self.setMinimumHeight(len(data) * 38 + 10)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bar_h, spacing, label_w, value_w = 22, 38, 130, 60
        bar_area = self.width() - label_w - value_w - 20
        font = QFont(); font.setPointSize(10); painter.setFont(font)
        for i, (label, value, color) in enumerate(self._data):
            y = i * spacing + 8
            painter.setPen(QPen(QColor("#2C3E50")))
            painter.drawText(QRectF(0, y, label_w, bar_h),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)
            bar_w = int((value / self._max) * bar_area) if self._max else 0
            path = QPainterPath()
            path.addRoundedRect(QRectF(label_w, y, bar_w, bar_h), 4, 4)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPath(path)
            painter.setPen(QPen(QColor("#2C3E50")))
            painter.drawText(QRectF(label_w + bar_area + 4, y, value_w, bar_h),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             f"{value:,}")
        painter.end()
