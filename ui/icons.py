# Centralized icon provider using QPainter-drawn vector icons
# No external files needed — all icons rendered at runtime

from PyQt6.QtWidgets import QApplication, QStyle
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont, QPainterPath, QBrush
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF

_ICON_CACHE: dict[str, QIcon] = {}

# Default palette
_TEAL = QColor("#388087")
_WHITE = QColor("#FFFFFF")
_DARK = QColor("#2C3E50")
_MUTED = QColor("#7F8C8D")
_DANGER = QColor("#D9534F")
_GREEN = QColor("#5CB85C")
_YELLOW = QColor("#E8B931")


def _make_pixmap(size: int = 20) -> tuple[QPixmap, QPainter]:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    return pm, p


def _icon_search(color=_MUTED, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.8)
    p.setPen(pen)
    p.drawEllipse(QRectF(3, 3, 10, 10))
    p.drawLine(QPointF(11.5, 11.5), QPointF(16, 16))
    p.end()
    return QIcon(pm)


def _icon_plus(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 2.2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    cx, cy = sz // 2, sz // 2
    p.drawLine(QPointF(cx, 4), QPointF(cx, sz - 4))
    p.drawLine(QPointF(4, cy), QPointF(sz - 4, cy))
    p.end()
    return QIcon(pm)


def _icon_megaphone(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(color))
    # Speaker cone
    path = QPainterPath()
    path.moveTo(4, 7)
    path.lineTo(8, 7)
    path.lineTo(14, 3)
    path.lineTo(14, 17)
    path.lineTo(8, 13)
    path.lineTo(4, 13)
    path.closeSubpath()
    p.drawPath(path)
    # Sound waves
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRect(14, 6, 4, 8), -60 * 16, 120 * 16)
    p.end()
    return QIcon(pm)


def _icon_dollar(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    # S shape
    p.drawArc(QRect(5, 4, 10, 6), 0 * 16, 180 * 16)
    p.drawArc(QRect(5, 10, 10, 6), 180 * 16, 180 * 16)
    # Vertical line
    p.drawLine(QPointF(10, 2), QPointF(10, 18))
    p.end()
    return QIcon(pm)


def _icon_link(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.drawArc(QRect(2, 5, 10, 10), 90 * 16, 180 * 16)
    p.drawArc(QRect(8, 5, 10, 10), -90 * 16, 180 * 16)
    p.end()
    return QIcon(pm)


def _icon_lock(color=_DARK, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # Lock body
    p.drawRoundedRect(QRectF(4, 9, 12, 9), 2, 2)
    # Shackle
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRect(6, 2, 8, 10), 0, 180 * 16)
    p.end()
    return QIcon(pm)


def _icon_fire(color=_DANGER, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    path = QPainterPath()
    path.moveTo(10, 2)
    path.cubicTo(10, 6, 15, 8, 14, 13)
    path.cubicTo(13, 17, 7, 17, 6, 13)
    path.cubicTo(5, 8, 10, 6, 10, 2)
    p.drawPath(path)
    p.end()
    return QIcon(pm)


def _icon_bolt(color=_YELLOW, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    path = QPainterPath()
    path.moveTo(11, 2)
    path.lineTo(5, 11)
    path.lineTo(9, 11)
    path.lineTo(8, 18)
    path.lineTo(15, 9)
    path.lineTo(11, 9)
    path.closeSubpath()
    p.drawPath(path)
    p.end()
    return QIcon(pm)


def _icon_edit(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # Pencil body
    p.drawLine(QPointF(13, 3), QPointF(17, 7))
    p.drawLine(QPointF(17, 7), QPointF(7, 17))
    p.drawLine(QPointF(7, 17), QPointF(3, 13))
    p.drawLine(QPointF(3, 13), QPointF(13, 3))
    # Pencil tip
    p.drawLine(QPointF(7, 17), QPointF(3, 18))
    p.drawLine(QPointF(3, 18), QPointF(3, 13))
    p.end()
    return QIcon(pm)


# ── Sidebar nav icons ────────────────────────────────────────────────

def _icon_dashboard(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.drawRect(QRect(3, 3, 6, 6))
    p.drawRect(QRect(11, 3, 6, 6))
    p.drawRect(QRect(3, 11, 6, 6))
    p.drawRect(QRect(11, 11, 6, 6))
    p.end()
    return QIcon(pm)


def _icon_patients(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    p.setPen(pen)
    # Head
    p.drawEllipse(QRectF(6, 2, 8, 8))
    # Body
    path = QPainterPath()
    path.moveTo(3, 18)
    path.cubicTo(3, 12, 7, 11, 10, 11)
    path.cubicTo(13, 11, 17, 12, 17, 18)
    p.drawPath(path)
    p.end()
    return QIcon(pm)


def _icon_appointments(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # Calendar
    p.drawRoundedRect(QRectF(3, 4, 14, 14), 2, 2)
    p.drawLine(QPointF(3, 9), QPointF(17, 9))
    p.drawLine(QPointF(7, 2), QPointF(7, 6))
    p.drawLine(QPointF(13, 2), QPointF(13, 6))
    p.end()
    return QIcon(pm)


def _icon_clinical(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    # Medical cross
    cx, cy = sz // 2, sz // 2
    p.drawLine(QPointF(cx, 4), QPointF(cx, 16))
    p.drawLine(QPointF(4, cy), QPointF(16, cy))
    # Outline circle
    pen2 = QPen(color, 1.2)
    p.setPen(pen2)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(2, 2, 16, 16))
    p.end()
    return QIcon(pm)


def _icon_analytics(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    # Bar chart bars
    p.drawLine(QPointF(5, 16), QPointF(5, 10))
    p.drawLine(QPointF(10, 16), QPointF(10, 5))
    p.drawLine(QPointF(15, 16), QPointF(15, 8))
    # Baseline
    pen2 = QPen(color, 1.2)
    p.setPen(pen2)
    p.drawLine(QPointF(2, 17), QPointF(18, 17))
    p.end()
    return QIcon(pm)


def _icon_employees(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    p.setPen(pen)
    # Person 1
    p.drawEllipse(QRectF(3, 2, 6, 6))
    path = QPainterPath()
    path.moveTo(1, 18)
    path.cubicTo(1, 13, 3, 11, 6, 11)
    path.cubicTo(9, 11, 11, 13, 11, 18)
    p.drawPath(path)
    # Person 2
    p.drawEllipse(QRectF(11, 2, 6, 6))
    path2 = QPainterPath()
    path2.moveTo(9, 18)
    path2.cubicTo(9, 13, 11, 11, 14, 11)
    path2.cubicTo(17, 11, 19, 13, 19, 18)
    p.drawPath(path2)
    p.end()
    return QIcon(pm)


def _icon_activity_log(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # Clipboard
    p.drawRoundedRect(QRectF(4, 3, 12, 15), 2, 2)
    # Clip
    p.drawRoundedRect(QRectF(7, 1, 6, 4), 1, 1)
    # Lines
    p.drawLine(QPointF(7, 9), QPointF(13, 9))
    p.drawLine(QPointF(7, 12), QPointF(13, 12))
    p.drawLine(QPointF(7, 15), QPointF(11, 15))
    p.end()
    return QIcon(pm)


def _icon_settings(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Gear outer
    p.drawEllipse(QRectF(4, 4, 12, 12))
    # Gear inner
    p.drawEllipse(QRectF(7, 7, 6, 6))
    # Gear teeth (4 lines)
    pen2 = QPen(color, 2.0)
    pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen2)
    cx, cy = sz // 2, sz // 2
    p.drawLine(QPointF(cx, 1), QPointF(cx, 4))
    p.drawLine(QPointF(cx, 16), QPointF(cx, 19))
    p.drawLine(QPointF(1, cy), QPointF(4, cy))
    p.drawLine(QPointF(16, cy), QPointF(19, cy))
    p.end()
    return QIcon(pm)


def _icon_logout(color=_DANGER, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # Door frame
    p.drawLine(QPointF(9, 3), QPointF(4, 3))
    p.drawLine(QPointF(4, 3), QPointF(4, 17))
    p.drawLine(QPointF(4, 17), QPointF(9, 17))
    # Arrow
    p.drawLine(QPointF(8, 10), QPointF(17, 10))
    p.drawLine(QPointF(14, 7), QPointF(17, 10))
    p.drawLine(QPointF(14, 13), QPointF(17, 10))
    p.end()
    return QIcon(pm)


def _icon_key(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(3, 3, 8, 8))
    p.drawLine(QPointF(10, 8), QPointF(17, 15))
    p.drawLine(QPointF(17, 15), QPointF(14, 15))
    p.drawLine(QPointF(15, 12), QPointF(15, 15))
    p.end()
    return QIcon(pm)


def _icon_trash(color=_DANGER, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # Lid
    p.drawLine(QPointF(3, 5), QPointF(17, 5))
    p.drawLine(QPointF(7, 5), QPointF(7, 3))
    p.drawLine(QPointF(7, 3), QPointF(13, 3))
    p.drawLine(QPointF(13, 3), QPointF(13, 5))
    # Can body
    p.drawLine(QPointF(5, 5), QPointF(6, 17))
    p.drawLine(QPointF(6, 17), QPointF(14, 17))
    p.drawLine(QPointF(14, 17), QPointF(15, 5))
    # Lines inside
    p.drawLine(QPointF(8, 8), QPointF(8, 14))
    p.drawLine(QPointF(12, 8), QPointF(12, 14))
    p.end()
    return QIcon(pm)


def _icon_people(color=_TEAL, sz=20) -> QIcon:
    return _icon_employees(color, sz)


def _icon_clipboard(color=_TEAL, sz=20) -> QIcon:
    return _icon_activity_log(color, sz)


def _icon_money(color=_TEAL, sz=20) -> QIcon:
    return _icon_dollar(color, sz)


def _icon_shield(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.6)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    path = QPainterPath()
    path.moveTo(10, 2)
    path.lineTo(3, 5)
    path.lineTo(3, 11)
    path.cubicTo(3, 15, 10, 18, 10, 18)
    path.cubicTo(10, 18, 17, 15, 17, 11)
    path.lineTo(17, 5)
    path.closeSubpath()
    p.drawPath(path)
    p.end()
    return QIcon(pm)


def _icon_new_patient(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    # Person
    p.drawEllipse(QRectF(4, 2, 7, 7))
    path = QPainterPath()
    path.moveTo(1, 18)
    path.cubicTo(1, 13, 4, 11, 7, 11)
    path.cubicTo(10, 11, 12, 12, 13, 14)
    p.drawPath(path)
    # Plus
    p.drawLine(QPointF(15, 11), QPointF(15, 18))
    p.drawLine(QPointF(12, 14.5), QPointF(18, 14.5))
    p.end()
    return QIcon(pm)


def _icon_calendar_plus(color=_TEAL, sz=20) -> QIcon:
    pm, p = _make_pixmap(sz)
    pen = QPen(color, 1.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.drawRoundedRect(QRectF(2, 4, 12, 14), 2, 2)
    p.drawLine(QPointF(2, 9), QPointF(14, 9))
    p.drawLine(QPointF(5, 2), QPointF(5, 6))
    p.drawLine(QPointF(11, 2), QPointF(11, 6))
    # Plus
    p.drawLine(QPointF(15, 12), QPointF(15, 18))
    p.drawLine(QPointF(12, 15), QPointF(18, 15))
    p.end()
    return QIcon(pm)


# ══════════════════════════════════════════════════════════════════════
#  Public API
# ══════════════════════════════════════════════════════════════════════

_ICON_MAP = {
    # Sidebar navigation
    "nav_dashboard":    _icon_dashboard,
    "nav_patients":     _icon_patients,
    "nav_appointments": _icon_appointments,
    "nav_clinical":     _icon_clinical,
    "nav_analytics":    _icon_analytics,
    "nav_employees":    _icon_employees,
    "nav_activity_log": _icon_activity_log,
    "nav_settings":     _icon_settings,
    "nav_logout":       _icon_logout,
    # Actions
    "search":       _icon_search,
    "plus":         _icon_plus,
    "megaphone":    _icon_megaphone,
    "dollar":       _icon_dollar,
    "link":         _icon_link,
    "lock":         _icon_lock,
    "fire":         _icon_fire,
    "bolt":         _icon_bolt,
    "edit":         _icon_edit,
    "key":          _icon_key,
    "trash":        _icon_trash,
    "people":       _icon_people,
    "clipboard":    _icon_clipboard,
    "money":        _icon_money,
    "shield":       _icon_shield,
    "new_patient":  _icon_new_patient,
    "calendar_plus": _icon_calendar_plus,
}

# Map sidebar label → icon key
NAV_ICON_MAP = {
    "Dashboard":      "nav_dashboard",
    "Patients":       "nav_patients",
    "Appointments":   "nav_appointments",
    "Clinical & POS": "nav_clinical",
    "Data Analytics": "nav_analytics",
    "Employees":      "nav_employees",
    "Activity Log":   "nav_activity_log",
    "Settings":       "nav_settings",
}


def get_icon(name: str) -> QIcon:
    """Retrieve a named icon. Returns empty QIcon if not found."""
    if name not in _ICON_CACHE:
        factory = _ICON_MAP.get(name)
        if factory:
            _ICON_CACHE[name] = factory()
        else:
            _ICON_CACHE[name] = QIcon()
    return _ICON_CACHE[name]
