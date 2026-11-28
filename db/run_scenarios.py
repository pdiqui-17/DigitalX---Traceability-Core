"""
run_scenarios.py — Demo K1–K6 cho câu hỏi đề bài và câu hỏi đổi cây trồng
Traceability Core v0.5 · Đề tài #6

Đây là bản CHÍNH cho kịch bản K1–K6 (minh chứng E3, E4). Bộ hồi quy 87 kiểm tra
nằm ở smoke_test.py.

Cách chạy:
    cd db
    python run_scenarios.py lac                       # SQLite, mè + lạc (K1–K6)
    python run_scenarios.py lac --pg                  # PostgreSQL (cấu hình ở db/.env)
    python run_scenarios.py lac --raw                 # kèm câu SQL và dữ liệu thô DB trả về
    python run_scenarios.py lac --log logs/k1_k6_sqlite.txt   # ghi log UTF-8
    python run_scenarios.py                           # chỉ mè (K1–K5)

Kịch bản:
    K1 — Truy ngược QR-80 về đúng 3 hộ nguồn + tỷ trọng
    K2 — Truy ngược QR-250 (cùng nguồn, cùng tỷ trọng vì cùng lô ép)
    K3 — Phát hiện chu kỳ thiếu minh chứng / chưa ghi / không xác định
    K4 — Hoạt động bị từ chối tính là rejected, không nhầm thành verified
    K5 — Sửa bản ghi giữ bản cũ + lý do (append-only)
    K6 — Đổi mè → lạc: chỉ INSERT, 0 DDL, truy xuất đúng
"""

import pathlib, sys
from datetime import datetime

from dbtools import DBError, connect, setup_output

HERE     = pathlib.Path(__file__).parent
ARGS     = set(setup_output(sys.argv)[1:])
WITH_LAC = "lac" in ARGS
RAW_MODE = "--raw" in ARGS or "-v" in ARGS
DIALECT  = "postgres" if ("--pg" in ARGS or "postgres" in ARGS) else "sqlite"

SEP    = "─" * 60
PASS   = "✅ ĐẠT"
FAIL   = "❌ LỖI"

# ─────────────────────────── kết nối CSDL ───────────────────────────
db = connect(DIALECT, convert_numbers=True)
print(f"Hệ CSDL: {DIALECT} · bộ dữ liệu: seed_me.sql" + (" + seed_lac.sql" if WITH_LAC else "")
      + f" · chạy lúc {datetime.now():%Y-%m-%d %H:%M}")

# nạp dữ liệu mè
db.load(HERE / "seed_me.sql")

# nạp dữ liệu lạc nếu yêu cầu
if WITH_LAC:
    db.load(HERE / "seed_lac.sql")


def q(sql):
    """Truy vấn trả danh sách tuple; nếu --raw thì in câu SQL + raw DB rows."""
    cols, rows = db.query(sql)
    if RAW_MODE:
        print("\n  [SQL]")
        for line in sql.strip().splitlines():
            print(f"    {line}")
        print(f"  [DB RAW OUTPUT: {len(rows)} row(s)]")
        print(f"    columns: {cols}")
        for r in rows:
            print(f"    {r}")
    return rows


def pct(v):
    if v is None:
        return "N/A"
    return f"{float(v)*100:.1f}%"


def header(code, title):
    print(f"\n{SEP}")
    print(f"  {code} — {title}")
    print(SEP)


def result(ok, detail=""):
    mark = PASS if ok else FAIL
    print(f"  → {mark}" + (f"  ({detail})" if detail else ""))


# ══════════════════════════════════════════════════════════════════════
# K1 · Truy ngược QR-80 về đúng 3 hộ nguồn + tỷ trọng
# ══════════════════════════════════════════════════════════════════════
header("K1", "Truy ngược QR-80 → 3 hộ nguồn + tỷ trọng")

rows = q("""
    SELECT l.public_code, s.share, s.source_status
    FROM   v_lot_sources s
    JOIN   lot l ON l.lot_id = s.source_lot_id
    JOIN   lot b ON b.lot_id = s.root_lot_id
    WHERE  b.public_code = 'QR-80'
    ORDER  BY s.share DESC
""")

print(f"\n  {'Lô nguồn':<12} {'Tỷ trọng':>9}  Trạng thái")
print(f"  {'─'*12} {'─'*9}  {'─'*10}")
for code, share, status in rows:
    print(f"  {code:<12} {pct(share):>9}  {status}")

expected = {("H-A", 0.4, "harvest"), ("H-B", 0.35, "harvest"), ("H-C", 0.25, "harvest")}
actual   = {(r[0], round(float(r[1]), 2), r[2]) for r in rows}
ok_k1    = actual == expected and abs(sum(float(r[1]) for r in rows) - 1.0) < 0.001

# đọc thêm trạng thái lô
ls = q("SELECT traced_share, trace_state FROM v_lot_status WHERE public_code = 'QR-80'")
if ls:
    traced, state = ls[0]
    print(f"\n  Trạng thái lô : {state}  (traced={pct(traced)})")
result(ok_k1, "3 hộ, tổng 100%" if ok_k1 else f"nhận được {actual}")


# ══════════════════════════════════════════════════════════════════════
# K2 · Truy ngược QR-250
# ══════════════════════════════════════════════════════════════════════
header("K2", "Truy ngược QR-250 → cùng nguồn với QR-80")

rows2 = q("""
    SELECT l.public_code, s.share, s.source_status
    FROM   v_lot_sources s
    JOIN   lot l ON l.lot_id = s.source_lot_id
    JOIN   lot b ON b.lot_id = s.root_lot_id
    WHERE  b.public_code = 'QR-250'
    ORDER  BY s.share DESC
""")

print(f"\n  {'Lô nguồn':<12} {'Tỷ trọng':>9}  Trạng thái")
print(f"  {'─'*12} {'─'*9}  {'─'*10}")
for code, share, status in rows2:
    print(f"  {code:<12} {pct(share):>9}  {status}")

actual2 = {(r[0], round(float(r[1]), 2), r[2]) for r in rows2}
ok_k2   = actual2 == expected   # cùng nguồn vì cùng lô ép PROC-01
result(ok_k2, "nguồn khớp QR-80 (cùng lô ép)" if ok_k2 else f"nhận được {actual2}")


# ══════════════════════════════════════════════════════════════════════
# K3 · Phát hiện đúng trạng thái chu kỳ
# ══════════════════════════════════════════════════════════════════════
header("K3", "Trạng thái chu kỳ: thiếu minh chứng / chưa ghi / undetermined")

cc = q("""
    SELECT c.cycle_id, cc.cycle_state, cc.n_not_recorded, cc.n_other_problem,
           COALESCE(cc.on_schedule_ratio, -1)
    FROM   v_cycle_completeness cc
    JOIN   cultivation_cycle c ON c.cycle_id = cc.cycle_id
    WHERE  c.crop_profile_id = 'cp_me'
    ORDER  BY c.cycle_id
""")

mô_tả = {
    "cy_a":  ("complete",     "Đầy đủ minh chứng, đã xác minh"),
    "cy_b":  ("incomplete",   "Hộ B sửa liều → bản r2 thiếu ảnh"),
    "cy_c":  ("incomplete",   "Hộ C không ghi bón thúc bắt buộc"),
    "cy_c2": ("undetermined", "Chưa có mốc gieo (cycle_anchor)"),
}

print(f"\n  {'Chu kỳ':<8} {'cycle_state':<14} {'not_rec':>7}  Ghi chú")
print(f"  {'─'*8} {'─'*14} {'─'*7}  {'─'*35}")
ok_k3 = True
for cid, state, not_rec, other, sched in cc:
    exp_state, note = mô_tả.get(cid, ("?", ""))
    ok_row = (state == exp_state)
    if not ok_row:
        ok_k3 = False
    flag = "✓" if ok_row else "✗"
    print(f"  {cid:<8} {state:<14} {not_rec:>7}  {flag} {note}")

result(ok_k3)


# ══════════════════════════════════════════════════════════════════════
# K4 · Hoạt động bị từ chối tính là rejected, không nhầm thành verified
# ══════════════════════════════════════════════════════════════════════
header("K4", "Hoạt động bị từ chối → rejected (không nhầm verified)")

# Thêm 1 xác minh rejected cho ph_a_r1 (phun thuốc hộ A)
# (ph_a chưa có xác minh nào trong seed_me → thêm trực tiếp)
try:
    db.run("""
        INSERT INTO verification
          (verification_id, activity_revision_id, lot_revision_id, lot_event_id,
           verifier_id, result, method, note,
           supersedes_verification_id, supersede_reason,
           verified_at, recorded_at)
        VALUES
          ('ver_ph_a_rej', 'ph_a_r1', NULL, NULL,
           'u_ktv', 'rejected', 'field_visit', 'Ảnh không rõ, không xác định đúng thuốc',
           NULL, NULL,
           '2027-02-20T09:00:00', '2027-02-20T09:00:00')
    """)
except DBError as e:
    print(f"  (ver_ph_a_rej đã tồn tại hoặc lỗi: {e})")

rows_k4 = q("""
    SELECT a.activity_id, s.evidence_completeness, s.verification_state
    FROM   v_activity_status s
    JOIN   activity a ON a.activity_id = s.activity_id
    WHERE  a.activity_id IN ('ph_a', 'bt_a', 'bt_b', 'th_a')
    ORDER  BY a.activity_id
""")

print(f"\n  {'Hoạt động':<12} {'evidence':<18} {'verification'}")
print(f"  {'─'*12} {'─'*18} {'─'*15}")
ok_k4 = True
for aid, evid, verif in rows_k4:
    if aid == "ph_a" and verif != "rejected":
        ok_k4 = False
    flag = ""
    if aid == "ph_a":
        flag = "← phải là rejected"
    print(f"  {aid:<12} {evid:<18} {verif}  {flag}")

result(ok_k4, "ph_a → rejected đúng" if ok_k4 else "ph_a chưa rejected")


# ══════════════════════════════════════════════════════════════════════
# K5 · Sửa bản ghi giữ bản cũ + lý do (append-only)
# ══════════════════════════════════════════════════════════════════════
header("K5", "Sửa bản ghi: giữ bản cũ + lý do (append-only)")

revs = q("""
    SELECT r.revision_no, ai.quantity, r.reason, r.recorded_at
    FROM   activity_revision r
    LEFT JOIN activity_input ai ON ai.revision_id = r.revision_id
    WHERE  r.activity_id = 'bt_b'
    ORDER  BY r.revision_no
""")

print(f"\n  Bản ghi hoạt động 'bt_b' (Hộ B bón thúc):")
print(f"  {'Rev':>4}  {'Lượng':>7}  {'Lý do':<45}  Ghi lúc")
print(f"  {'─'*4}  {'─'*7}  {'─'*45}  {'─'*22}")
for rev_no, qty, reason, rec_at in revs:
    qty_str    = f"{qty} kg" if qty is not None else "—"
    reason_str = reason if reason else "— (bản gốc)"
    print(f"  {rev_no:>4}  {qty_str:>7}  {reason_str:<45}  {rec_at}")

ok_k5 = (len(revs) == 2
          and revs[0][0] == 1 and float(revs[0][1]) == 30    # bản cũ: 30 kg
          and revs[1][0] == 2 and float(revs[1][1]) == 25    # bản mới: 25 kg
          and revs[1][2] is not None)                         # có lý do

# kiểm thêm: UPDATE bị chặn
blocked_ok = False
try:
    db.run("UPDATE activity_revision SET reason = 'x' WHERE revision_id = 'bt_b_r1'")
    blocked_ok = False
except DBError as e:
    # phải bị chặn bởi trigger chỉ-ghi-thêm, không phải lỗi khác (sai cú pháp, sai tên cột...)
    blocked_ok = "append-only" in str(e) or "chỉ ghi thêm" in str(e)
    if not blocked_ok:
        print(f"  (bị chặn nhưng sai lý do: {str(e).splitlines()[0]})")

print(f"\n  Thử UPDATE bản ghi cũ: {'bị chặn ✓' if blocked_ok else 'KHÔNG bị chặn ✗'}")
result(ok_k5 and blocked_ok,
       "bản cũ 30 kg còn nguyên, bản mới 25 kg có lý do, UPDATE bị chặn")


# ══════════════════════════════════════════════════════════════════════
# K6 · Đổi cây: mè → lạc (chỉ INSERT, 0 DDL)
# ══════════════════════════════════════════════════════════════════════
if WITH_LAC:
    header("K6", "Đổi cây mè → lạc: chỉ INSERT, 0 lệnh DDL")

    # 6a. Đếm crop_profile
    n_cp = q("SELECT COUNT(*) FROM crop_profile")[0][0]
    print(f"\n  Số crop_profile hiện có: {n_cp}  (phải ≥ 2: SESAME + PEANUT)")

    # 6b. Chu kỳ lạc tồn tại và có trạng thái đúng
    cy_lac = q("""
        SELECT cc.cycle_state, cc.completeness_ratio, cc.n_not_recorded, cc.n_other_problem
        FROM   v_cycle_completeness cc WHERE cc.cycle_id = 'cy_d'
    """)
    if cy_lac:
        state, ratio, not_rec, other = cy_lac[0]
        print(f"  Chu kỳ lạc cy_d  : {state}  (completeness={ratio})")
    else:
        state = None
        print("  cy_d không tồn tại ✗")

    # 6c. Truy ngược lô lạc QR-LAC-200
    src_lac = q("""
        SELECT l.public_code, s.share, s.source_status
        FROM   v_lot_sources s
        JOIN   lot l ON l.lot_id = s.source_lot_id
        JOIN   lot b ON b.lot_id = s.root_lot_id
        WHERE  b.public_code = 'QR-LAC-200'
        ORDER  BY s.share DESC
    """)

    print(f"\n  Truy ngược QR-LAC-200:")
    print(f"  {'Lô nguồn':<14} {'Tỷ trọng':>9}  Trạng thái")
    print(f"  {'─'*14} {'─'*9}  {'─'*10}")
    for code, share, status in src_lac:
        print(f"  {code:<14} {pct(share):>9}  {status}")

    # 6d. Kiểm không có vi phạm PHI cho lạc (hộ D phun đúng lịch)
    phi_lac = q("""
        SELECT COUNT(*)
        FROM   v_phi_violations
        WHERE  harvest_activity_id = 'th_d'
    """)
    n_phi = phi_lac[0][0]
    print(f"\n  Vi phạm PHI hộ D (lạc)   : {n_phi}  (phải = 0, PHI 5 ngày, cách 10 ngày)")

    # 6e. Hoạt động bón lót lạc: complete/verified
    act_lac = q("""
        SELECT evidence_completeness, verification_state
        FROM   v_activity_status WHERE activity_id = 'bl_d'
    """)
    evid_l, verif_l = act_lac[0] if act_lac else (None, None)
    print(f"  Bón lót lạc (bl_d)        : {evid_l} / {verif_l}")

    # 6f. Đảm bảo 0 DDL — đếm CREATE TABLE trong session
    # (không có cách trực tiếp, nhưng ta kiểm: tên bảng phải là tập con cố định)
    tables = db.tables()
    base_tables = {
        "agent","facility","crop_profile","variety","stage","activity_type",
        "evidence_requirement","input_material","material_crop_rule",
        "farm","plot","season","cultivation_cycle","cycle_anchor",
        "activity","activity_revision","activity_input",
        "device","observation","evidence","evidence_link",
        "lot","lot_revision","lot_event","lot_input",
        "certification","verification"
    }
    extra_ddl = tables - base_tables
    print(f"\n  Bảng ngoài schema gốc : {extra_ddl if extra_ddl else '(không có) ✓'}")

    ok_k6 = (
        n_cp >= 2
        and state == "complete"
        and len(src_lac) == 1
        and round(float(src_lac[0][1]), 2) == 1.0
        and src_lac[0][2] == "harvest"
        and n_phi == 0
        and evid_l == "complete" and verif_l == "verified"
        and len(extra_ddl) == 0
    )
    result(ok_k6,
           "lạc: crop_profile + chu kỳ + lô + truy ngược + PHI OK, 0 DDL"
           if ok_k6 else "xem chi tiết ở trên")
else:
    print(f"\n{SEP}")
    print("  K6 — Chưa chạy (thêm tham số 'lac' để kiểm)")
    print(f"       python run_scenarios.py lac")
    print(SEP)


# ══════════════════════════════════════════════════════════════════════
# Tổng kết
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'═'*60}")
kq = {
    "K1": ok_k1, "K2": ok_k2, "K3": ok_k3,
    "K4": ok_k4, "K5": ok_k5 and blocked_ok,
}
if WITH_LAC:
    kq["K6"] = ok_k6

dat = sum(1 for v in kq.values() if v)
tong = len(kq)
print(f"  Kết quả ({DIALECT}): {dat}/{tong} kịch bản đạt")
for k, v in kq.items():
    print(f"    {k}  {'✅' if v else '❌'}")
print(f"{'═'*60}\n")

sys.stdout.flush()
sys.exit(0 if dat == tong else 1)
