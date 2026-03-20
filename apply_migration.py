import sys
sys.path.append(r"c:\Users\ethan\Downloads\Projects\CareCRUDV1")
from backend.base import DatabaseBase

class Migrator(DatabaseBase):
    def __init__(self):
        super().__init__()

    def run_migration(self):
        conn = self._get_connection()
        cur = conn.cursor()
        
        # 1. Add column if not exists
        try:
            cur.execute("ALTER TABLE patients ADD COLUMN id_proof_path VARCHAR(255) DEFAULT NULL;")
            print("id_proof_path column added to patients.")
        except Exception as e:
            print("Column maybe exists:", e)
            
        try:
            cur.execute("ALTER TABLE discount_types ADD COLUMN requires_id_proof TINYINT(1) NOT NULL DEFAULT 0;")
            print("requires_id_proof column added to discount_types.")
        except Exception as e:
            print("Column maybe exists in discount_types:", e)
            
        # 3. Update view
        view_sql = """
        CREATE OR REPLACE VIEW vw_patients AS
        SELECT
            p.patient_id,
            CONCAT(p.first_name, ' ', p.last_name) AS full_name,
            p.sex,
            TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
            p.phone,
            p.email,
            p.address,
            p.civil_status,
            p.emergency_contact,
            p.blood_type,
            p.id_proof_path,
            COALESCE(GROUP_CONCAT(pc.condition_name SEPARATOR ', '), 'None') AS conditions,
            p.status,
            p.notes
        FROM patients p
        LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
        GROUP BY p.patient_id;
        """
        try:
            cur.execute(view_sql)
            print("vw_patients view updated.")
        except Exception as e:
            print("Failed to update view:", e)
            
        conn.commit()
        conn.close()

if __name__ == "__main__":
    Migrator().run_migration()
