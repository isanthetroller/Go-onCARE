import os
import sys

sys.path.insert(0, os.getcwd())

from backend import AuthBackend

def run():
    b = AuthBackend()
    
    # 1. Insert
    print("Executing insert...")
    res = b.exec('INSERT INTO services (service_name, price, category) VALUES (%s, %s, %s)', ('TestServiceXYZ', 999, 'General'))
    print("Insert result:", res)
    
    # 2. Fetch
    print("Executing fetch...")
    row = b.fetch('SELECT service_id FROM services WHERE service_name=%s', ('TestServiceXYZ',), one=True)
    print("Fetch result:", row)
    
    # 3. Delete
    print("Executing delete...")
    dres = b.exec('DELETE FROM services WHERE service_name=%s', ('TestServiceXYZ',))
    print("Delete result:", dres)
    
    print("Done")

if __name__ == '__main__':
    run()