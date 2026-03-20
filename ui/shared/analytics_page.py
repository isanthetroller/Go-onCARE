# Analytics page - charts, revenue, performance data

import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QTableWidgetItem,
    QPushButton, QDateEdit, QComboBox,
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor
from ui.styles import (
    make_page_layout, finish_page, make_banner,
    make_card, make_read_only_table, busy_cursor, fmt_peso,
)
from ui.shared.chart_widgets import (
    PieChartWidget, HBarChartWidget,
    CONDITION_COLORS, STATUS_COLORS, DEPT_COLORS, DEMO_COLORS, RETENTION_COLORS,
)


# ══════════════════════════════════════════════════════════════════════
#  Analytics Page
# ══════════════════════════════════════════════════════════════════════
class AnalyticsPage(QWidget):
    def __init__(self, backend=None, role: str = "Admin", user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._build()
        # Auto-refresh data every 15 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._on_refresh)
        self._refresh_timer.start(300_000)

    def _load_data(self):
        if not self._backend:
            return {}
        with busy_cursor():
            return {
                "stats":          self._backend.get_summary_stats(),
                "monthly_rev":    self._backend.get_monthly_revenue(6),
                "doctors":        self._backend.get_doctor_performance(),
                "services":       self._backend.get_top_services(),
                "appt_status":    self._backend.get_appointment_status_counts(),
                "conditions":     self._backend.get_patient_condition_counts(),
                "demographics":   self._backend.get_patient_demographics(),
                "dept_revenue":   self._backend.get_revenue_by_department(),
                "active_doctors": self._backend.get_active_doctor_count(),
                "monthly_appts":  self._backend.get_monthly_appointment_stats(6),
                "retention":      self._backend.get_patient_retention(6),
                "cancel_trend":   self._backend.get_cancellation_rate_trend(6),
                "period_cmp":     self._backend.get_period_comparison(),
                "attendance":     self._backend.get_employee_attendance_stats() if hasattr(self._backend, 'get_employee_attendance_stats') else {},
            }

    # ── Build ─────────────────────────────────────────────────────
    def _build(self):
        # Doctor role: skip loading all-system data, build doctor-only view
        if self._role == "Doctor":
            scroll, lay = make_page_layout()
            lay.addWidget(make_banner(
                "Data Analytics & Reports",
                "Hospital performance, revenue, trends, and insights"))
            self._build_doctor_view(lay)
            lay.addStretch()
            finish_page(self, scroll)
            return

        data = self._load_data()
        stats = data.get("stats", {})

        scroll, lay = make_page_layout()

        lay.addWidget(make_banner(
            "Data Analytics & Reports",
            "Hospital performance, revenue, trends, and insights"))

        if self._role == "Admin":
            # ── Period Comparison KPIs ────────────────────────────
            cmp = data.get("period_cmp", {})
            kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)
            self._build_kpi_cards(kpi_row, stats, data, cmp)
            lay.addLayout(kpi_row)

            # ── 2x2 Grid Layout for Main Charts ────────────
            grid = QGridLayout()
            grid.setSpacing(24)
            
            raw_conds = data.get("conditions", [])
            total_cases = sum(c["cnt"] for c in raw_conds)
            others_cnt = sum(c["cnt"] for c in raw_conds if c["condition_name"] == "Others")
                
            cond_data = [(c["condition_name"], c["cnt"],
                          CONDITION_COLORS[i % len(CONDITION_COLORS)] if c["condition_name"] != "Others" else "#BDC3C7")
                         for i, c in enumerate(raw_conds)]
            
            if total_cases > 0 and (others_cnt / total_cases) > 0.4:
                grid.addWidget(self._hbar_card("Patient Conditions",
                                               "Top conditions (Others >40%)",
                                               cond_data or [("No data", 1, "#CCC")]), 0, 0)
            else:
                grid.addWidget(self._pie_card("Patient Conditions",
                                              "Distribution of diagnosed conditions",
                                              cond_data or [("No data", 1, "#CCC")]), 0, 0)
            status_data = [(s["status"], s["cnt"],
                            STATUS_COLORS.get(s["status"], "#7F8C8D"))
                           for s in data.get("appt_status", [])]
            grid.addWidget(self._pie_card("Appointment Status",
                                          "Current appointment outcomes",
                                          status_data or [("No data", 1, "#CCC")]), 0, 1)

            dept_data = [(d["department_name"], int(d["total_revenue"]),
                          DEPT_COLORS[i % len(DEPT_COLORS)])
                         for i, d in enumerate(data.get("dept_revenue", []))]
            grid.addWidget(self._pie_card("Revenue by Department",
                                          "Revenue distribution by doctor department",
                                          dept_data or [("No data", 1, "#CCC")]), 1, 0)
            demo_data = [(d["age_group"], d["cnt"],
                          DEMO_COLORS.get(d["age_group"], "#7F8C8D"))
                         for d in data.get("demographics", [])]
            grid.addWidget(self._pie_card("Patient Demographics",
                                          "Age group distribution",
                                          demo_data or [("No data", 1, "#CCC")]), 1, 1)
            lay.addLayout(grid)
            
            # ── Row 3: Live Employee Attendance ───────────
            att = data.get("attendance", {})
            row3 = QHBoxLayout(); row3.setSpacing(20)
            
            absent_val = att.get("absent", 0)
            present_val = att.get("present", 0)
            overall_att_data = []
            if absent_val or present_val:
                overall_att_data = [
                    ("Present", present_val, "#2ECC71"),
                    ("Absent", absent_val, "#E74C3C")
                ]
            row3.addWidget(self._pie_card("Today's Attendance",
                                          "Overall present vs absent employees",
                                          overall_att_data or [("No data", 1, "#CCC")]))
                                          
            dept_att_raw = att.get("dept_attendance", [])
            dept_att_data = []
            for i, d in enumerate(dept_att_raw):
                dept_att_data.append((
                    d["department_name"], 
                    d["present_count"], 
                    DEPT_COLORS[i % len(DEPT_COLORS)]
                ))
            row3.addWidget(self._pie_card("Present by Department",
                                          "Present employees by department",
                                          dept_att_data or [("No data", 1, "#CCC")]))
            lay.addLayout(row3)

            # ── Patient Retention ─────────────────────────────────
            lay.addWidget(self._retention_card(data.get("retention", [])))

            # ── Cancellation Rate Trend ───────────────────────────
            lay.addWidget(self._cancellation_card(data.get("cancel_trend", [])))

        # ── Doctor Performance (all roles) ────────────────────────
        lay.addWidget(self._doctor_perf_card(data.get("doctors", [])))

        if self._role == "Admin":
            # ── Top Services + Monthly Revenue ────────────────────
            row4 = QHBoxLayout(); row4.setSpacing(20)
            row4.addWidget(self._top_services_card(data.get("services", [])))
            row4.addWidget(self._monthly_revenue_card(data.get("monthly_rev", [])))
            lay.addLayout(row4)

            # ── Summary / KPI Table ───────────────────────────────
            lay.addWidget(self._summary_table_card(data))

        lay.addStretch()
        finish_page(self, scroll)

    # ── helpers ───────────────────────────────────────────────────
    @staticmethod
    def _lbl(text, obj_name):
        l = QLabel(text); l.setObjectName(obj_name); return l

    def _build_kpi_cards(self, kpi_row, stats, data, cmp):
        monthly_rev = data.get("monthly_rev", [])
        current_month_rev = float(monthly_rev[-1]["total_revenue"]) if monthly_rev else 0
        total_appts = stats.get("total_appts", 0)
        active_docs = data.get("active_doctors", 0)
        avg_per_day = stats.get("avg_per_day", 0)
        total_patients = stats.get("total_patients", 0)

        kpis = [
            ("Monthly Revenue", fmt_peso(current_month_rev), "#16A085",
             cmp.get("revenue_delta", 0), "file-text"),
            ("Total Patients", f"{total_patients:,}", "#2980B9",
             cmp.get("patients_delta", 0), "users"),
            ("Appointments", f"{total_appts:,}", "#8E44AD",
             cmp.get("appts_delta", 0), "calendar"),
            ("Active Doctors", f"{active_docs}", "#E67E22", None, "activity"),
            ("Avg. Visit / Day", f"{avg_per_day}", "#2E86C1", None, "clock"),
        ]
        for label, value, color, delta, icon_name in kpis:
            kpi_row.addWidget(self._kpi_card(label, value, color, delta, icon_name))

    # ── Doctor-only analytics view ────────────────────────────────
    def _build_doctor_view(self, lay):
        """Build a personalised analytics page for a logged-in Doctor."""
        own = self._backend.get_doctor_own_stats(self._user_email) if self._backend else {}
        perf = own.get("performance", {})
        monthly = own.get("monthly", [])

        doc_name = perf.get("doctor_name", "Doctor")

        # ── KPI cards ─────────────────────────────────────────────
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)
        total_appts = int(perf.get("total_appointments", 0) or 0)
        completed   = int(perf.get("completed", 0) or 0)
        cancelled   = int(perf.get("cancelled", 0) or 0)
        revenue     = float(perf.get("revenue_generated", 0) or 0)
        comp_rate   = (completed / total_appts * 100) if total_appts else 0

        kpis = [
            ("Total Appointments", str(total_appts), "#388087"),
            ("Completed", str(completed), "#5CB85C"),
            ("Cancelled", str(cancelled), "#D9534F"),
            ("Revenue Generated", fmt_peso(revenue), "#6FB3B8"),
            ("Completion Rate", f"{comp_rate:.1f}%", "#C2EDCE"),
        ]
        for label, value, color in kpis:
            kpi_row.addWidget(self._kpi_card(label, value, color))
        lay.addLayout(kpi_row)

        # ── Info card (department, employment type) ───────────────
        info_card = make_card()
        info_vbox = QVBoxLayout(info_card)
        info_vbox.setContentsMargins(20, 18, 20, 14); info_vbox.setSpacing(8)
        info_vbox.addWidget(self._lbl(f"Dr. {doc_name}", "cardTitle"))
        info_vbox.addWidget(self._lbl("Your profile summary", "mutedSubtext"))

        info_grid = QGridLayout(); info_grid.setSpacing(12)
        dept = perf.get("department_name", "—")
        emp_type = perf.get("employment_type", "—")
        for col, (lbl, val) in enumerate([
            ("Department", dept), ("Employment Type", emp_type),
            ("Total Revenue", fmt_peso(revenue)),
        ]):
            v = QLabel(val); v.setStyleSheet("font-size:16px; font-weight:bold; color:#388087;")
            l = QLabel(lbl); l.setStyleSheet("font-size:11px; color:#7F8C8D;")
            info_grid.addWidget(v, 0, col)
            info_grid.addWidget(l, 1, col)
        info_vbox.addLayout(info_grid)
        lay.addWidget(info_card)

        # ── Monthly Revenue Trend (own) ───────────────────────────
        if monthly:
            rev_card = make_card()
            vbox = QVBoxLayout(rev_card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
            vbox.addWidget(self._lbl("Your Monthly Revenue", "cardTitle"))
            vbox.addWidget(self._lbl("Revenue from completed appointments over the last 6 months", "mutedSubtext"))
            bar_data = [(m["month_label"][:3], int(float(m.get("revenue", 0))))
                        for m in monthly]
            colors = ["#388087"] * len(bar_data)
            chart_data = [(lbl, val, c) for (lbl, val), c in zip(bar_data, colors)]
            chart = HBarChartWidget(chart_data)
            vbox.addWidget(chart)
            grand = sum(float(m.get("revenue", 0)) for m in monthly)
            total_row = QHBoxLayout(); total_row.addStretch()
            tl = QLabel(f"Total ({len(monthly)} months):  {fmt_peso(grand)}")
            tl.setObjectName("totalLabelSm")
            total_row.addWidget(tl); vbox.addLayout(total_row)
            lay.addWidget(rev_card)

        # ── Monthly breakdown table ───────────────────────────────
        if monthly:
            tbl_card = make_card()
            vbox2 = QVBoxLayout(tbl_card); vbox2.setContentsMargins(20, 18, 20, 14); vbox2.setSpacing(12)
            vbox2.addWidget(self._lbl("Monthly Breakdown", "cardTitle"))
            vbox2.addWidget(self._lbl("Appointments and revenue per month", "mutedSubtext"))
            cols = ["Month", "Appointments", "Completed", "Revenue"]
            tbl = make_read_only_table(cols, min_h=max(len(monthly), 1) * 48 + 48, row_h=48)
            tbl.setRowCount(len(monthly))
            for r, m in enumerate(monthly):
                tbl.setItem(r, 0, QTableWidgetItem(m.get("month_label", "")))
                tbl.setItem(r, 1, QTableWidgetItem(str(m.get("total_appointments", 0))))
                tbl.setItem(r, 2, QTableWidgetItem(str(m.get("completed", 0))))
                tbl.setItem(r, 3, QTableWidgetItem(fmt_peso(float(m.get("revenue", 0)))))
            vbox2.addWidget(tbl)
            lay.addWidget(tbl_card)

    @staticmethod
    def _kpi_card(label, value, color, delta=None, icon_name="activity") -> QFrame:
        card = make_card(min_height=120)
        card.setObjectName("HoverKpiCard")
        card.setStyleSheet("""
            QFrame#HoverKpiCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E5EBED;
            }
            QFrame#HoverKpiCard:hover {
                border-color: #3498DB;
            }
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(24, 20, 24, 20)
        vbox.setSpacing(8)
        
        # Header: Icon + Title
        hdr = QHBoxLayout()
        hdr.setSpacing(12)
        
        from ui.icons import get_icon
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import Qt
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon(icon_name, color=QColor(color)).pixmap(22, 22))
        icon_bg = QFrame()
        icon_bg.setStyleSheet(f"background-color: {color}15; border-radius: 8px;")
        icon_bg.setFixedSize(36, 36)
        ibox = QVBoxLayout(icon_bg)
        ibox.setContentsMargins(0,0,0,0)
        ibox.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        hdr.addWidget(icon_bg)
        
        l = QLabel(label)
        l.setStyleSheet("color: #7F8C8D; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;")
        hdr.addWidget(l)
        hdr.addStretch()
        vbox.addLayout(hdr)
        
        vbox.addSpacing(4)
        
        # Value
        v = QLabel(value)
        v.setStyleSheet("color: #1A252F; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;")
        vbox.addWidget(v)
        
        # Delta
        if delta is not None:
            arrow = "▲" if delta >= 0 else "▼"
            clr = "#27AE60" if delta >= 0 else "#E74C3C"
            d = QLabel(f"{arrow} {abs(delta):.1f}% vs last month")
            d.setStyleSheet(f"color: {clr}; font-size: 13px; font-weight: bold;")
            vbox.addWidget(d)
        else:
            vbox.addStretch(1)
            
        return card

    # ── Refresh / Export ──────────────────────────────────────────
    def _on_refresh(self):
        if not self.isVisible():
            return
            
        v_scroll = 0
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            v_scrollbar = scroll_area.verticalScrollBar()
            if v_scrollbar:
                v_scroll = v_scrollbar.value()
                
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            from PyQt6.QtWidgets import QWidget as _QW
            _QW().setLayout(old)
            
        self._build()
        
        if v_scroll > 0:
            from PyQt6.QtCore import QTimer
            def restore():
                s_area = self.findChild(QScrollArea)
                if s_area and s_area.verticalScrollBar():
                    s_area.verticalScrollBar().setValue(v_scroll)
            QTimer.singleShot(50, restore)

    # ── Pie card ──────────────────────────────────────────────────
    # ── Pie card ──────────────────────────────────────────────────
    @staticmethod
    def _pie_card(title_text, subtitle_text, data) -> QFrame:
        card = make_card(min_height=340)
        card.setObjectName("HoverKpiCard")
        vbox = QVBoxLayout(card); vbox.setContentsMargins(0, 0, 0, 0); vbox.setSpacing(0)
        
        # Header Region with subtle border
        hdr_widget = QWidget()
        hdr_widget.setStyleSheet("border-bottom: 1px solid #F0F4F7;")
        hdr = QVBoxLayout(hdr_widget)
        hdr.setContentsMargins(24, 20, 24, 16)
        hdr.setSpacing(4)
        t = QLabel(title_text); t.setObjectName("cardTitle")
        t.setStyleSheet("font-size: 16px; font-weight: 800; color: #2C3E50;")
        s = QLabel(subtitle_text); s.setObjectName("mutedSubtext")
        s.setStyleSheet("font-size: 13px; color: #7F8C8D;")
        hdr.addWidget(t); hdr.addWidget(s)
        vbox.addWidget(hdr_widget)

        total = sum(v for _, v, _ in data)
        
        content_wrap = QWidget()
        content = QHBoxLayout(content_wrap)
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(32)
        
        # ── Stat Card override for single-category domains ──
        if len(data) == 1:
            stat_lay = QVBoxLayout()
            stat_lay.setSpacing(0)
            label_text, value, color = data[0]
            
            val_lbl = QLabel(f"{value:,}")
            val_lbl.setStyleSheet("font-size: 76px; font-weight: 900; color: #2E6A70; letter-spacing: -2px;")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            sub_lbl = QLabel(label_text)
            sub_lbl.setStyleSheet("font-size: 16px; color: #34495E; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;")
            sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            content.addStretch()
            stat_lay.addWidget(val_lbl)
            stat_lay.addWidget(sub_lbl)
            
            if "No data" not in label_text:
                pct_lbl = QLabel("100% of Total")
                pct_lbl.setStyleSheet("font-size: 13px; color: #95A5A6; margin-top: 6px;")
                pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                stat_lay.addWidget(pct_lbl)
                
            content.addLayout(stat_lay)
            content.addStretch()
            vbox.addWidget(content_wrap, 1)
            return card

        # ── Normal Pie Layout with Legends ──
        from ui.shared.chart_widgets import PieChartWidget
        chart = PieChartWidget(data); chart.setMinimumSize(220, 220)
        content.addWidget(chart, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        
        legend_widget = QWidget()
        legend = QGridLayout(legend_widget)
        legend.setContentsMargins(0, 0, 0, 0)
        legend.setVerticalSpacing(16)
        legend.setHorizontalSpacing(16)
        
        for i, (label, value, color) in enumerate(data):
            pct = (value / total * 100) if total else 0
            
            dot = QLabel("●"); dot.setStyleSheet(f"color:{color}; font-size:20px;")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lbl = QLabel(label)
            lbl.setStyleSheet("color:#1A252F; font-size:14px; font-weight: 600;")
            lbl.setWordWrap(True)
            
            val = QLabel(f"{value:,}  ({pct:.1f}%)"); val.setStyleSheet("color:#7F8C8D; font-size:14px; font-weight: 700;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            legend.addWidget(dot, i, 0)
            legend.addWidget(lbl, i, 1)
            legend.addWidget(val, i, 2)
            
        content.addWidget(legend_widget, 1, alignment=Qt.AlignmentFlag.AlignVCenter)
        vbox.addWidget(content_wrap, 1)
        return card

    # ── Horizontal Bar Card ───────────────────────────────────────
    @staticmethod
    def _hbar_card(title_text, subtitle_text, data) -> QFrame:
        card = make_card(min_height=340)
        card.setObjectName("HoverKpiCard")
        vbox = QVBoxLayout(card); vbox.setContentsMargins(0, 0, 0, 0); vbox.setSpacing(0)
        
        hdr_widget = QWidget()
        hdr_widget.setStyleSheet("border-bottom: 1px solid #F0F4F7;")
        hdr = QVBoxLayout(hdr_widget)
        hdr.setContentsMargins(24, 20, 24, 16)
        hdr.setSpacing(4)
        t = QLabel(title_text); t.setObjectName("cardTitle")
        t.setStyleSheet("font-size: 16px; font-weight: 800; color: #2C3E50;")
        s = QLabel(subtitle_text); s.setObjectName("mutedSubtext")
        s.setStyleSheet("font-size: 13px; color: #7F8C8D;")
        hdr.addWidget(t); hdr.addWidget(s)
        vbox.addWidget(hdr_widget)
        
        content_wrap = QWidget()
        content = QVBoxLayout(content_wrap)
        content.setContentsMargins(24, 24, 24, 24)
        from ui.shared.chart_widgets import HBarChartWidget
        chart = HBarChartWidget(data)
        content.addWidget(chart)
        content.addStretch()
        
        vbox.addWidget(content_wrap, 1)
        return card

    # ── Patient Retention card ────────────────────────────────────
    def _retention_card(self, retention: list) -> QFrame:
        card = make_card()
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Patient Retention", "cardTitle"))
        vbox.addWidget(self._lbl("New vs returning patients per month", "mutedSubtext"))

        cols = ["Month", "New Patients", "Returning", "Total"]
        tbl = make_read_only_table(cols, min_h=max(len(retention), 1) * 48 + 48, row_h=48)
        tbl.setRowCount(len(retention))
        for r, row in enumerate(retention):
            new_p = int(row.get("new_patients", 0) or 0)
            ret_p = int(row.get("returning_patients", 0) or 0)
            tbl.setItem(r, 0, QTableWidgetItem(row.get("month_label", "")))
            ni = QTableWidgetItem(str(new_p)); ni.setForeground(QColor("#6FB3B8"))
            tbl.setItem(r, 1, ni)
            ri = QTableWidgetItem(str(ret_p)); ri.setForeground(QColor("#388087"))
            tbl.setItem(r, 2, ri)
            tbl.setItem(r, 3, QTableWidgetItem(str(new_p + ret_p)))
        vbox.addWidget(tbl)
        return card

    # ── Cancellation Rate card ────────────────────────────────────
    def _cancellation_card(self, cancel_trend: list) -> QFrame:
        card = make_card()
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Cancellation Rate Trend", "cardTitle"))
        vbox.addWidget(self._lbl("Monthly cancellation rate over time", "mutedSubtext"))

        cols = ["Month", "Total", "Cancelled", "Rate"]
        tbl = make_read_only_table(cols, min_h=max(len(cancel_trend), 1) * 48 + 48, row_h=48)
        tbl.setRowCount(len(cancel_trend))
        for r, row in enumerate(cancel_trend):
            tbl.setItem(r, 0, QTableWidgetItem(row.get("month_label", "")))
            tbl.setItem(r, 1, QTableWidgetItem(str(row.get("total", 0))))
            ci = QTableWidgetItem(str(row.get("cancelled", 0)))
            ci.setForeground(QColor("#D9534F"))
            tbl.setItem(r, 2, ci)
            rate = float(row.get("rate", 0) or 0)
            ri = QTableWidgetItem(f"{rate:.1f}%")
            ri.setForeground(QColor("#D9534F" if rate > 15 else "#E8B931" if rate > 5 else "#5CB85C"))
            tbl.setItem(r, 3, ri)
        vbox.addWidget(tbl)
        return card

    # ── Doctor Performance ────────────────────────────────────────
    def _doctor_perf_card(self, doctors: list) -> QFrame:
        card = make_card()
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Doctor Performance", "cardTitle"))
        vbox.addWidget(self._lbl("Appointments, completions, and revenue generated", "mutedSubtext"))

        cols = ["Doctor", "Total Appts", "Completed", "Revenue Generated"]
        tbl = make_read_only_table(cols, min_h=max(len(doctors), 1) * 48 + 48, row_h=48)
        tbl.setRowCount(len(doctors))
        for r, doc in enumerate(doctors):
            name = doc.get("doctor_name", "")
            tbl.setItem(r, 0, QTableWidgetItem(f"Dr. {name.split()[-1]}" if name else ""))
            tbl.setItem(r, 1, QTableWidgetItem(str(doc.get("total_appointments", 0))))
            tbl.setItem(r, 2, QTableWidgetItem(str(doc.get("completed", 0))))
            tbl.setItem(r, 3, QTableWidgetItem(fmt_peso(float(doc.get("revenue_generated", 0)))))
        vbox.addWidget(tbl)
        return card

    # ── Top Services ──────────────────────────────────────────────
    def _top_services_card(self, services: list) -> QFrame:
        card = make_card()
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Top Services", "cardTitle"))
        vbox.addWidget(self._lbl("Most requested services and revenue contribution", "mutedSubtext"))

        cols = ["Service", "Count", "Revenue"]
        tbl = make_read_only_table(cols, min_h=max(len(services), 1) * 48 + 48, row_h=48)
        tbl.setRowCount(len(services))
        for r, svc in enumerate(services):
            tbl.setItem(r, 0, QTableWidgetItem(svc.get("service_name", "")))
            tbl.setItem(r, 1, QTableWidgetItem(str(svc.get("usage_count", 0))))
            tbl.setItem(r, 2, QTableWidgetItem(fmt_peso(float(svc.get("total_revenue", 0)))))
        vbox.addWidget(tbl)
        return card

    # ── Monthly Revenue ───────────────────────────────────────────
    def _monthly_revenue_card(self, monthly: list) -> QFrame:
        card = make_card()
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Monthly Revenue Trend", "cardTitle"))
        vbox.addWidget(self._lbl("Revenue over the last 6 months", "mutedSubtext"))

        cols = ["Month", "Revenue"]
        tbl = make_read_only_table(cols, min_h=max(len(monthly), 1) * 48 + 48, row_h=48)
        tbl.setRowCount(len(monthly))
        grand = 0.0
        for r, row in enumerate(monthly):
            tbl.setItem(r, 0, QTableWidgetItem(row.get("month_label", "")))
            rev = float(row.get("total_revenue", 0)); grand += rev
            tbl.setItem(r, 1, QTableWidgetItem(fmt_peso(rev)))
        vbox.addWidget(tbl)
        total_row = QHBoxLayout(); total_row.addStretch()
        tl = QLabel(f"Total ({len(monthly)} months):  {fmt_peso(grand)}")
        tl.setObjectName("totalLabelSm")
        total_row.addWidget(tl); vbox.addLayout(total_row)
        return card

    # ── Summary / KPI Table ───────────────────────────────────────
    def _summary_table_card(self, data: dict) -> QFrame:
        card = make_card()
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)

        hdr = QHBoxLayout()
        tc = QVBoxLayout()
        tc.addWidget(self._lbl("Overall Summary", "cardTitle"))
        tc.addWidget(self._lbl("Key metrics at a glance for the selected period", "mutedSubtext"))
        hdr.addLayout(tc); hdr.addStretch()

        hdr.addWidget(QLabel("From:"))
        from ui.shared.modern_calendar import apply_modern_calendar
        self.sum_from = QDateEdit(); apply_modern_calendar(self.sum_from)
        self.sum_from.setDate(QDate.currentDate().addMonths(-6))
        self.sum_from.setObjectName("formCombo"); self.sum_from.setMinimumHeight(36); self.sum_from.setMaximumWidth(140)
        self.sum_from.setDisplayFormat("M/d/yyyy")
        hdr.addWidget(self.sum_from)

        hdr.addWidget(QLabel("To:"))
        self.sum_to = QDateEdit(); apply_modern_calendar(self.sum_to)
        self.sum_to.setDate(QDate.currentDate())
        self.sum_to.setObjectName("formCombo"); self.sum_to.setMinimumHeight(36); self.sum_to.setMaximumWidth(140)
        self.sum_to.setDisplayFormat("M/d/yyyy")
        hdr.addWidget(self.sum_to)
        apply_btn = QPushButton("Apply"); apply_btn.setObjectName("secondaryBtn")
        apply_btn.setMinimumHeight(36); apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._on_refresh)
        hdr.addWidget(apply_btn)
        vbox.addLayout(hdr)

        stats = data.get("stats", {})
        monthly_rev = data.get("monthly_rev", [])
        grand_rev = sum(float(m.get("total_revenue", 0)) for m in monthly_rev)
        completed = stats.get("completed", 0)
        cancelled = stats.get("cancelled", 0)
        total_appts = stats.get("total_appts", 0)
        completion_rate = (completed / total_appts * 100) if total_appts else 0
        services = data.get("services", [])
        top_svc = services[0] if services else {}
        top_svc_text = (f"{top_svc.get('service_name','N/A')} "
                        f"({fmt_peso(float(top_svc.get('total_revenue',0)))})") if top_svc else "N/A"

        summary = [
            ("Total Revenue (period)", fmt_peso(grand_rev)),
            ("Appointments Completed", str(completed)),
            ("Appointments Cancelled", str(cancelled)),
            ("Completion Rate", f"{completion_rate:.1f}%"),
            ("Top Service", top_svc_text),
        ]
        cols = ["Metric", "Value"]
        tbl = make_read_only_table(cols)
        tbl.setRowCount(len(summary))
        for r, (metric, value) in enumerate(summary):
            tbl.setItem(r, 0, QTableWidgetItem(metric))
            vi = QTableWidgetItem(value); vi.setForeground(QColor("#2C3E50"))
            tbl.setItem(r, 1, vi)
        vbox.addWidget(tbl)
        return card
