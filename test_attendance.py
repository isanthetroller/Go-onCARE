import sys
import traceback
from backend import AuthBackend

def test():
    try:
        b = AuthBackend()
        print("Initial Attendance Stats:")
        print(b.get_employee_attendance_stats())

        emps = b.fetch("SELECT employee_id FROM employees WHERE status='Active' LIMIT 1")
        if emps:
            emp_id = emps[0]["employee_id"]
            print(f"\\nAttempting to clock in Employee #{emp_id}...")
            res = b.clock_in(emp_id)
            print(f"Result: {res}")
        else:
            print("No active employees found to test.")

        print("\\nAttendance Stats After Clock In:")
        print(b.get_employee_attendance_stats())
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    test()
