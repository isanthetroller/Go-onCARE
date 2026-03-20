import sys
import traceback
from backend import AuthBackend

def test():
    try:
        b = AuthBackend()
        print("Fetching new condition counts:")
        res = b.get_patient_condition_counts()
        print(res)
        
        print("\nFetching full dashboard summary stats:")
        print(b.get_summary_stats())
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    test()
