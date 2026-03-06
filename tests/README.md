# CareCRUD Automated Tests

Self-contained test suite in this `tests/` folder.  
**To remove:** just delete the entire `tests/` folder — nothing else depends on it.

## Prerequisites

- MySQL running locally with `carecrud_db` populated (use `database/carecrud.sql` + `database/sample_data.sql`)
- Python packages: `pip install pytest`

## Run all tests

```bash
cd CareCRUDV1
pytest tests/ -v
```

## Run a specific module

```bash
pytest tests/test_auth.py -v
pytest tests/test_patients.py -v
```

## What's covered

| File | Backend Module | Tests |
|------|---------------|-------|
| `test_auth.py` | Auth (login, passwords, accounts) | 8 |
| `test_patients.py` | Patient CRUD + profiles | 8 |
| `test_appointments.py` | Scheduling, validation, conflicts | 9 |
| `test_employees.py` | Employee list, HR stats, payroll | 7 |
| `test_clinical.py` | Queue, invoices | 6 |
| `test_dashboard.py` | Dashboard summary, upcoming | 3 |
| `test_analytics.py` | Revenue, demographics, performance | 8 |
| `test_settings.py` | Table counts, conditions, discounts | 4 |
| `test_search.py` | Global search | 4 |
