import sys
from PyQt6.QtWidgets import QApplication
import ui.shared.analytics_page as ap

app = QApplication(sys.argv)

print("Starting pie card test...")

# Test 1: Donut with lots of slices
test_data_multi = [
    ("Cardiology", 15, "#123456"),
    ("Pediatrics", 12, "#234567"),
    ("Oncology", 40, "#345678"),
    ("Neurology", 18, "#456789"),
    ("Dermatology", 22, "#567890"),
]
try:
    card1 = ap.AnalyticsPage._pie_card("Test Multi", "multi val chart", test_data_multi)
    print("Multi-value Donut: Build OK")
except Exception as e:
    print(f"Multi-value error: {e}")

# Test 2: Single value donut
test_data_single = [
    ("Cardiology", 500, "#112233"),
]
try:
    card2 = ap.AnalyticsPage._pie_card("Test Single", "single val chart", test_data_single)
    print("Single-value Donut: Build OK")
except Exception as e:
    print(f"Single-value error: {e}")

print("Testing condition sorting...")
# Test the data building simulation
data = {
    "conditions": [
        {"condition_name": "Asthma", "cnt": 15},
        {"condition_name": "Flu", "cnt": 4},
        {"condition_name": "Cancer", "cnt": 1},
        {"condition_name": "Diabetes", "cnt": 12},
        {"condition_name": "Hypertension", "cnt": 30},
        {"condition_name": "Arthritis", "cnt": 6},
    ]
}
from ui.shared.chart_widgets import CONDITION_COLORS
raw_conds = data.get("conditions", [])
sorted_conds = sorted(raw_conds, key=lambda c: c["cnt"], reverse=True)
if len(sorted_conds) > 5:
    top_5 = sorted_conds[:5]
    others_cnt = sum(c["cnt"] for c in sorted_conds[5:])
    top_5.append({"condition_name": "Others", "cnt": others_cnt})
    sorted_conds = top_5

cond_data = [(c["condition_name"], c["cnt"],
              CONDITION_COLORS[i % len(CONDITION_COLORS)] if c["condition_name"] != "Others" else "#95A5A6")
             for i, c in enumerate(sorted_conds)]
print(cond_data)
print("All Tests Complete.")
