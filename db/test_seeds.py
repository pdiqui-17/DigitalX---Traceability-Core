import sqlite3, sys, os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

db = sqlite3.connect(':memory:')
db.execute('PRAGMA foreign_keys = ON')

def run_file(path):
    sql = open(path, encoding='utf-8').read()
    try:
        db.executescript(sql)
        print(f'OK   {path}')
    except Exception as e:
        print(f'ERR  {path}: {e}')
        sys.exit(1)

run_file('db/schema.sql')
run_file('db/triggers_sqlite.sql')
run_file('db/views_sqlite.sql')
run_file('db/seed_me.sql')
run_file('db/seed_lac.sql')

checks = [
    ('Me: bt_a complete+verified',
     "SELECT evidence_completeness, verification_state FROM v_activity_status WHERE activity_id='bt_a'",
     lambda r: r[0] == ('complete','verified')),
    ('Me: bt_b ban2 missing_evidence',
     "SELECT evidence_completeness, verification_state FROM v_activity_status WHERE activity_id='bt_b'",
     lambda r: r[0] == ('missing_evidence','unverified')),
    ('Me: cy_c incomplete',
     "SELECT cycle_state FROM v_cycle_completeness WHERE cycle_id='cy_c'",
     lambda r: r[0][0] == 'incomplete'),
    ('Me: cy_c2 undetermined',
     "SELECT cycle_state FROM v_cycle_completeness WHERE cycle_id='cy_c2'",
     lambda r: r[0][0] == 'undetermined'),
    ('Me: QR-80 -> 3 harvest lots',
     "SELECT COUNT(*) FROM v_lot_sources s JOIN lot r ON r.lot_id=s.root_lot_id WHERE r.public_code='QR-80' AND s.source_status='harvest'",
     lambda r: r[0][0] == 3),
    ('Me: share QR-80 sum = 1.0',
     "SELECT SUM(s.share) FROM v_lot_sources s JOIN lot r ON r.lot_id=s.root_lot_id WHERE r.public_code='QR-80' AND s.source_status='harvest'",
     lambda r: abs(r[0][0] - 1.0) < 0.001),
    ('Lac: bl_d complete+verified',
     "SELECT evidence_completeness, verification_state FROM v_activity_status WHERE activity_id='bl_d'",
     lambda r: r[0] == ('complete','verified')),
    ('Lac: QR-LAC-200 -> 1 harvest lot',
     "SELECT COUNT(*) FROM v_lot_sources s JOIN lot r ON r.lot_id=s.root_lot_id WHERE r.public_code='QR-LAC-200' AND s.source_status='harvest'",
     lambda r: r[0][0] == 1),
    ('Lac: share QR-LAC-200 = 1.0',
     "SELECT SUM(s.share) FROM v_lot_sources s JOIN lot r ON r.lot_id=s.root_lot_id WHERE r.public_code='QR-LAC-200' AND s.source_status='harvest'",
     lambda r: abs(r[0][0] - 1.0) < 0.001),
    ('Chung: 2 crop_profile (0 DDL)',
     'SELECT COUNT(*) FROM crop_profile',
     lambda r: r[0][0] == 2),
    ('Chung: 2 season (Dong Xuan + He Thu)',
     'SELECT COUNT(*) FROM season',
     lambda r: r[0][0] == 2),
]

passed = 0
for name, sql, test in checks:
    rows = db.execute(sql).fetchall()
    ok = test(rows)
    status = 'PASS' if ok else 'FAIL'
    print(f'  {status}  {name}  -> {rows}')
    if ok:
        passed += 1

print(f'\n{passed}/{len(checks)} checks passed')
sys.exit(0 if passed == len(checks) else 1)
