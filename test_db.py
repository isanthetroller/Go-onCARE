import sys, os, json
sys.path.append(os.path.dirname(__file__))
from backend import AuthBackend

b = AuthBackend()
out = {}
try:
    out["Tables"] = b.fetch("SHOW TABLES")
except Exception as e:
    out["Tables"] = str(e)

try:
    out["discounts_count"] = b.fetch("SELECT COUNT(*) FROM discounts")
except Exception as e:
    out["discounts_count"] = str(e)
    
try:
    out["discount_types_rows"] = b.fetch("SELECT * FROM discount_types")
except Exception as e:
    out["discount_types_rows"] = str(e)

with open("test_db_json.txt", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=4, default=str)
