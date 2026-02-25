"""Search backend – Global cross-entity search."""


class SearchMixin:

    def global_search(self, query, include_employees=True):
        results = {"patients": [], "appointments": [], "employees": []}
        if not query or len(query) < 2:
            return results
        like = f"%{query}%"
        results["patients"] = self.fetch("""
            SELECT patient_id, CONCAT(first_name,' ',last_name) AS name, phone, status
            FROM patients WHERE CONCAT(first_name,' ',last_name) LIKE %s OR phone LIKE %s OR email LIKE %s LIMIT 10
        """, (like, like, like))
        results["appointments"] = self.fetch("""
            SELECT a.appointment_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   a.appointment_date, a.status
            FROM appointments a INNER JOIN patients p ON a.patient_id=p.patient_id
            WHERE CONCAT(p.first_name,' ',p.last_name) LIKE %s LIMIT 10
        """, (like,))
        if include_employees:
            results["employees"] = self.fetch("""
                SELECT employee_id, CONCAT(first_name,' ',last_name) AS name, email
                FROM employees WHERE CONCAT(first_name,' ',last_name) LIKE %s OR email LIKE %s LIMIT 10
            """, (like, like))
        return results
