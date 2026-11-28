-- =====================================================================
-- inspect_raw.sql — Xem trực tiếp dữ liệu thô do DB trả về (không qua Python)
-- Chạy bằng sqlite3 CLI:
--   sqlite3 :memory: ".read inspect_raw.sql"
-- Hoặc lưu ra file log:
--   sqlite3 :memory: ".read inspect_raw.sql" > log_raw_db.txt
-- =====================================================================

.headers on
.mode box
PRAGMA foreign_keys = ON;

.read schema.sql
.read triggers_sqlite.sql
.read views_sqlite.sql
.read seed_me.sql
.read seed_lac.sql

SELECT '=== 1. CROP PROFILES (mè + lạc, 0 DDL) ===' AS section;
SELECT crop_profile_id, crop_code, name, version, anchor_event, valid_from FROM crop_profile;

SELECT '=== 2. TRUY NGƯỢC LÔ THÀNH PHẨM (v_lot_sources) ===' AS section;
SELECT b.public_code AS qr_code, l.public_code AS source_lot, s.cycle_id, s.share, s.source_status
FROM v_lot_sources s
JOIN lot b ON b.lot_id = s.root_lot_id
JOIN lot l ON l.lot_id = s.source_lot_id
WHERE b.public_code IN ('QR-80', 'QR-250', 'QR-LAC-200')
ORDER BY b.public_code, s.share DESC;

SELECT '=== 3. TRẠNG THÁI LÔ TỔNG HỢP TRÊN QR (v_lot_status) ===' AS section;
SELECT lot_id, public_code, n_harvest_sources, traced_share, untraceable_share, complete_share, verified_share, trace_state, chain_evidence_state
FROM v_lot_status
WHERE public_code IN ('QR-80', 'QR-250', 'QR-LAC-200', 'RAW-01', 'PROC-01')
ORDER BY public_code;

SELECT '=== 4. ĐỘ ĐẦY ĐỦ THEO CHU KỲ (v_cycle_completeness) ===' AS section;
SELECT c.crop_profile_id, cc.*
FROM v_cycle_completeness cc
JOIN cultivation_cycle c ON c.cycle_id = cc.cycle_id
ORDER BY c.crop_profile_id, cc.cycle_id;

SELECT '=== 5. LỊCH KỲ VỌNG TỪNG HOẠT ĐỘNG BẮT BUỘC (v_cycle_expected) ===' AS section;
SELECT cycle_id, code, window_start, window_end, performed_at, schedule_state, evidence_completeness, verification_state
FROM v_cycle_expected
ORDER BY cycle_id, code;

SELECT '=== 6. TRẠNG THÁI TỪNG HOẠT ĐỘNG (v_activity_status) ===' AS section;
SELECT activity_id, cycle_id, revision_id, revision_no, performed_at, evidence_completeness, verification_state
FROM v_activity_status
ORDER BY cycle_id, activity_id;

SELECT '=== 7. LỊCH SỬ SỬA BẢN GHI (activity_revision + activity_input) ===' AS section;
SELECT r.activity_id, r.revision_no, ai.material_id, ai.quantity, ai.unit, r.reason, r.recorded_at
FROM activity_revision r
LEFT JOIN activity_input ai ON ai.revision_id = r.revision_id
WHERE r.activity_id = 'bt_b'
ORDER BY r.revision_no;

SELECT '=== 8. VI PHẠM THỜI GIAN CÁCH LY (v_phi_violations) ===' AS section;
SELECT * FROM v_phi_violations;

SELECT '=== 9. KIỂM TRA NHẤT QUÁN LIÊN BẢNG (v_integrity_issues) ===' AS section;
SELECT * FROM v_integrity_issues;

SELECT '=== 10. DIGITAL TIMELINE CHO QR-80 (v_lot_timeline) ===' AS section;
SELECT at, time_precision, kind, ref_id, detail, actor_id, evidence_state, verification_state, source_channel
FROM v_lot_timeline
WHERE root_lot_id = 'lot_b80'
ORDER BY at, kind;

SELECT '=== 11. DIGITAL TIMELINE CHO LẠC QR-LAC-200 (v_lot_timeline) ===' AS section;
SELECT at, time_precision, kind, ref_id, detail, actor_id, evidence_state, verification_state, source_channel
FROM v_lot_timeline
WHERE root_lot_id = 'lot_lac_pkg'
ORDER BY at, kind;
