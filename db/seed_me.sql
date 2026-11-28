-- =====================================================================
-- seed_me.sql — Dữ liệu demo: chuỗi mè đen → dầu mè rang
-- Đề tài #6 · Agricultural Digital Thread & Evidence-aware Traceability
--
-- Thứ tự nạp:
--   schema.sql → triggers_<hệ>.sql → views_<hệ>.sql → seed_me.sql
--
-- SQLite: chạy  PRAGMA foreign_keys = ON;  trước khi nạp.
-- PostgreSQL:   \i seed_me.sql  hoặc  psql -f seed_me.sql
--
-- Tình huống được tái hiện:
--   A. Hộ A — đầy đủ minh chứng, đã xác minh               → complete / verified
--   B. Hộ B — sửa liều sau khi ghi, ảnh chưa gắn lại       → missing_evidence
--             phun thuốc Y chưa có PHI rule cho mè          → missing_phi_rule
--   C. Hộ C — không ghi bón thúc bắt buộc                   → not_recorded (cycle incomplete)
--   C2.      — lô đất chưa có ngày gieo                      → undetermined
--   QR       — scan QR-80 → truy ngược về 3 lô thu hoạch + tỷ trọng
-- =====================================================================

-- =====================================================================
-- CỤM 0 · Agent và địa điểm
-- =====================================================================

INSERT INTO agent VALUES ('u_fns', 'organization', 'F&S Agricultural',          'company',    NULL,    '2026-01-01T00:00:00');
INSERT INTO agent VALUES ('u_a',   'person',       'Hộ A (Nguyễn Văn An)',     'farmer',     'u_fns', '2026-10-01T00:00:00');
INSERT INTO agent VALUES ('u_b',   'person',       'Hộ B (Trần Thị Bình)',     'farmer',     'u_fns', '2026-10-01T00:00:00');
INSERT INTO agent VALUES ('u_c',   'person',       'Hộ C (Lê Văn Cường)',      'farmer',     'u_fns', '2026-10-01T00:00:00');
INSERT INTO agent VALUES ('u_ktv', 'person',       'Kỹ thuật viên F&S',        'technician', 'u_fns', '2026-10-01T00:00:00');
INSERT INTO agent VALUES ('u_qa',  'person',       'QA F&S',                    'company',    'u_fns', '2026-10-01T00:00:00');
INSERT INTO agent VALUES ('u_ver', 'person',       'Kiểm định viên độc lập',   'verifier',   NULL,    '2026-10-01T00:00:00');
INSERT INTO agent VALUES ('u_cert','organization', 'Tổ chức chứng nhận',        'certifier',  NULL,    '2026-10-01T00:00:00');
INSERT INTO agent VALUES ('u_dev', 'device',       'Cảm biến ẩm đất #001',     'system',     'u_fns', '2026-10-01T00:00:00');

INSERT INTO facility VALUES ('fac_tm', 'Điểm thu mua Lương Hòa',  'collection_point', 'u_fns', 'Tây Ninh', 'Lương Hòa', NULL);
INSERT INTO facility VALUES ('fac_nm', 'Nhà máy ép dầu F&S',      'processing_plant', 'u_fns', 'Tây Ninh', 'Lương Hòa', NULL);

-- =====================================================================
-- CỤM 1 · Cấu hình cây mè (SESAME)
-- =====================================================================

INSERT INTO crop_profile VALUES (
  'cp_me', 'SESAME', 'Mè đen 2 vỏ', 1, 'sowing',
  '{"oil_content_pct":"number"}',
  'Quy trình canh tác mè Bình Thuận v2026',
  '2026-01-01'
);
INSERT INTO variety VALUES ('v_me', 'SESAME', 'Mè đen Bình Thuận', '{}', 'Chưa xác minh — giả định nhóm');

-- Các giai đoạn (stage)
INSERT INTO stage VALUES ('st_me_lp', 'cp_me', 1, 'Làm đất – Gieo');
INSERT INTO stage VALUES ('st_me_cs', 'cp_me', 2, 'Chăm sóc');
INSERT INTO stage VALUES ('st_me_th', 'cp_me', 3, 'Thu hoạch');

-- Loại hoạt động
-- (id, stage_id, code, name, requirement, offset_days, tolerance_days, produces_lot, uses_inputs, attr_schema, public_level, rule_source, is_assumption)
INSERT INTO activity_type VALUES ('at_me_bt1',  'st_me_cs', 'TOP_DRESS_1', 'Bón thúc lần 1',  'mandatory',   15,   3, 0, 1, NULL, 'detail',  'Quy trình Bình Thuận mục 6',    0);
INSERT INTO activity_type VALUES ('at_me_phun', 'st_me_cs', 'SPRAY',       'Phun thuốc BVTV', 'conditional', NULL, 0, 0, 1, NULL, 'detail',  'Quy trình Bình Thuận mục 9',    0);
INSERT INTO activity_type VALUES ('at_me_th',   'st_me_th', 'HARVEST',     'Thu hoạch',        'mandatory',   80,   7, 1, 0, NULL, 'summary', 'Giả định nhóm — cần xác minh', 1);

-- Yêu cầu minh chứng
-- (id, activity_type_id, lot_event_type, evidence_kind, min_count, rule_source, is_assumption)
INSERT INTO evidence_requirement VALUES ('er_me_bt1_photo',  'at_me_bt1',  NULL,          'photo',         1, 'Giả định nhóm', 1);
INSERT INTO evidence_requirement VALUES ('er_me_phun_photo', 'at_me_phun', NULL,          'photo',         1, 'Giả định nhóm', 1);
INSERT INTO evidence_requirement VALUES ('er_me_th_weigh',   'at_me_th',   NULL,          'weighing_slip', 1, 'Giả định nhóm', 1);
INSERT INTO evidence_requirement VALUES ('er_gop_weigh',     NULL,         'aggregation', 'weighing_slip', 1, 'Giả định nhóm', 1);

-- Vật tư
INSERT INTO input_material VALUES ('m_ure', 'fertilizer', 'Urê Hà Bắc',  'N',           NULL,    'kg');
INSERT INTO input_material VALUES ('m_x',   'pesticide',  'Thuốc X',      'Hoạt chất X', 'REG-X', 'ml');
INSERT INTO input_material VALUES ('m_y',   'pesticide',  'Thuốc Y',      'Hoạt chất Y', 'REG-Y', 'ml');

-- PHI rule: Thuốc X có 7 ngày cách ly với mè
INSERT INTO material_crop_rule VALUES ('m_x', 'SESAME', 7, 'Giả định nhóm — cần đối chiếu nhãn thuốc', 1);
-- Thuốc Y: CỐ Ý không ghi PHI cho mè → trigger cảnh báo missing_phi_rule

-- =====================================================================
-- CỤM 2 · Vụ, Nông hộ, Lô đất, Chu kỳ canh tác
-- =====================================================================

INSERT INTO season VALUES (
  'ss_dx2627', 'u_fns', 'Đông Xuân 2026–2027', 'SESAME',
  '2026-11-01', '2027-03-31',
  'u_fns', '2026-10-15T08:00:00'
);

-- Nông hộ và lô đất (3 hộ, hộ C có 2 lô)
INSERT INTO farm VALUES ('f_a', 'u_a', 'Hộ A', 'Tây Ninh', 'Lương Hòa', NULL, 'u_fns', '2026-10-20T08:00:00');
INSERT INTO farm VALUES ('f_b', 'u_b', 'Hộ B', 'Tây Ninh', 'Lương Hòa', NULL, 'u_fns', '2026-10-20T08:00:00');
INSERT INTO farm VALUES ('f_c', 'u_c', 'Hộ C', 'Tây Ninh', 'Lương Hòa', NULL, 'u_fns', '2026-10-20T08:00:00');

INSERT INTO plot VALUES ('p_a1', 'f_a', 'L1', 5000, NULL, NULL, 'u_fns', '2026-10-20T08:00:00');
INSERT INTO plot VALUES ('p_b1', 'f_b', 'L1', 4500, NULL, NULL, 'u_fns', '2026-10-20T08:00:00');
INSERT INTO plot VALUES ('p_c1', 'f_c', 'L1', 3000, NULL, NULL, 'u_fns', '2026-10-20T08:00:00');
INSERT INTO plot VALUES ('p_c2', 'f_c', 'L2', 2000, NULL, NULL, 'u_fns', '2026-10-20T08:00:00'); -- lô thứ 2, chưa có ngày gieo

-- Chu kỳ canh tác
-- (id, plot_id, crop_profile_id, variety_id, season_id, started_at, closed_at, created_by, created_at)
-- cy_a, cy_b, cy_c: đã đóng (closed_at đã qua) → v_cycle_expected không dùng not_due, dùng not_recorded
INSERT INTO cultivation_cycle VALUES ('cy_a',  'p_a1', 'cp_me', 'v_me', 'ss_dx2627', '2026-11-15', '2027-02-28', 'u_fns', '2026-11-15T07:00:00');
INSERT INTO cultivation_cycle VALUES ('cy_b',  'p_b1', 'cp_me', 'v_me', 'ss_dx2627', '2026-11-15', '2027-02-28', 'u_fns', '2026-11-15T07:00:00');
INSERT INTO cultivation_cycle VALUES ('cy_c',  'p_c1', 'cp_me', 'v_me', 'ss_dx2627', '2026-11-15', '2027-02-28', 'u_fns', '2026-11-15T07:00:00');
INSERT INTO cultivation_cycle VALUES ('cy_c2', 'p_c2', 'cp_me', 'v_me', 'ss_dx2627', '2026-11-15', NULL,         'u_fns', '2026-11-15T07:00:00'); -- cy_c2 cố ý chưa có cycle_anchor; mở để undetermined

-- Mốc gieo (cycle_anchor) — cy_c2 không có → schedule trả undetermined
INSERT INTO cycle_anchor VALUES ('an_a1', 'cy_a', 1, '2026-11-20', 'u_a', '2026-11-20T16:00:00', NULL);
INSERT INTO cycle_anchor VALUES ('an_b1', 'cy_b', 1, '2026-11-20', 'u_b', '2026-11-20T16:00:00', NULL);
INSERT INTO cycle_anchor VALUES ('an_c1', 'cy_c', 1, '2026-11-20', 'u_c', '2026-11-20T16:00:00', NULL);

-- =====================================================================
-- CỤM 3 · Hoạt động canh tác
-- =====================================================================

-- ── Hộ A: bón thúc đúng lịch, có ảnh, có vật tư, KTV xác minh ──────
INSERT INTO activity          VALUES ('bt_a', 'cy_a', 'at_me_bt1', 'u_a', '2026-11-15T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('bt_a_r1', 'bt_a', 1, '2026-12-05T08:00:00', 'day', 'u_a', NULL, 'u_a', '2026-12-05T18:00:00', NULL);
INSERT INTO activity_input    VALUES ('bt_a_r1', 'm_ure', 30, 'kg');
INSERT INTO evidence          VALUES ('ev_bt_a_1', 'photo', 's3://farm-a/bt_a_1.jpg', 'sha_bt_a_1', NULL, NULL, NULL, 'u_a', '2026-12-05T18:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_bt_a_1', 'ev_bt_a_1', 'bt_a_r1', NULL, NULL, NULL, NULL, 'u_a', '2026-12-05T18:00:00');
INSERT INTO verification      VALUES ('ver_bt_a', 'bt_a_r1', NULL, NULL, 'u_ktv', 'verified', 'field_visit', NULL, NULL, NULL, '2026-12-10T09:00:00', '2026-12-10T09:00:00');

-- Hộ A: phun thuốc X — 5 ngày trước thu hoạch (vi phạm PHI 7 ngày → v_phi_violations sẽ cảnh báo)
INSERT INTO activity          VALUES ('ph_a', 'cy_a', 'at_me_phun', 'u_a', '2026-12-05T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('ph_a_r1', 'ph_a', 1, '2027-02-05T08:00:00', 'day', 'u_a', NULL, 'u_a', '2027-02-05T17:00:00', NULL);
INSERT INTO activity_input    VALUES ('ph_a_r1', 'm_x', 200, 'ml');
INSERT INTO evidence          VALUES ('ev_ph_a_1', 'photo', 's3://farm-a/ph_a_1.jpg', 'sha_ph_a_1', NULL, NULL, NULL, 'u_a', '2027-02-05T17:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_ph_a_1', 'ev_ph_a_1', 'ph_a_r1', NULL, NULL, NULL, NULL, 'u_a', '2027-02-05T17:00:00');

-- ── Hộ B: bón thúc → sửa liều (bản 2) nhưng KHÔNG gắn lại ảnh ──────
-- → evidence_completeness của bản hiện hành (r2) = missing_evidence
INSERT INTO activity          VALUES ('bt_b', 'cy_b', 'at_me_bt1', 'u_b', '2026-11-15T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('bt_b_r1', 'bt_b', 1, '2026-12-05T08:00:00', 'day', 'u_b', NULL, 'u_b', '2026-12-05T18:00:00', NULL);
INSERT INTO activity_input    VALUES ('bt_b_r1', 'm_ure', 30, 'kg');
INSERT INTO evidence          VALUES ('ev_bt_b_1', 'photo', 's3://farm-b/bt_b_1.jpg', 'sha_bt_b_1', NULL, NULL, NULL, 'u_b', '2026-12-05T18:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_bt_b_1', 'ev_bt_b_1', 'bt_b_r1', NULL, NULL, NULL, NULL, 'u_b', '2026-12-05T18:00:00');
-- sửa liều: bản 2 (không gắn ảnh lại → bản 2 thiếu minh chứng)
INSERT INTO activity_revision VALUES ('bt_b_r2', 'bt_b', 2, '2026-12-05T08:00:00', 'day', 'u_b', NULL, 'u_b', '2026-12-07T10:00:00', 'Ghi nhầm liều: thực tế 25 kg, không phải 30 kg');
INSERT INTO activity_input    VALUES ('bt_b_r2', 'm_ure', 25, 'kg');

-- Hộ B: phun thuốc Y — KHÔNG có PHI rule cho SESAME → missing_phi_rule
INSERT INTO activity          VALUES ('ph_b', 'cy_b', 'at_me_phun', 'u_b', '2026-12-05T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('ph_b_r1', 'ph_b', 1, '2027-01-20T08:00:00', 'day', 'u_b', NULL, 'u_b', '2027-01-20T17:00:00', NULL);
INSERT INTO activity_input    VALUES ('ph_b_r1', 'm_y', 150, 'ml');
INSERT INTO evidence          VALUES ('ev_ph_b_1', 'photo', 's3://farm-b/ph_b_1.jpg', 'sha_ph_b_1', NULL, NULL, NULL, 'u_b', '2027-01-20T17:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_ph_b_1', 'ev_ph_b_1', 'ph_b_r1', NULL, NULL, NULL, NULL, 'u_b', '2027-01-20T17:00:00');

-- ── Hộ C: CỐ Ý KHÔNG ghi bón thúc → not_recorded ───────────────────

-- =====================================================================
-- CỤM 4 · Thu hoạch + Lô thu hoạch
-- =====================================================================

-- Hộ A: 400 kg, có phiếu cân
INSERT INTO activity          VALUES ('th_a', 'cy_a', 'at_me_th', 'u_a', '2027-02-10T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('th_a_r1', 'th_a', 1, '2027-02-10T08:00:00', 'day', 'u_a', NULL, 'u_a', '2027-02-10T12:00:00', NULL);
INSERT INTO evidence          VALUES ('ev_th_a_w', 'weighing_slip', 's3://farm-a/th_a_weigh.pdf', 'sha_th_a_w', NULL, NULL, NULL, 'u_a', '2027-02-10T12:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_th_a_w', 'ev_th_a_w', 'th_a_r1', NULL, NULL, NULL, NULL, 'u_a', '2027-02-10T12:00:00');
INSERT INTO lot               VALUES ('lot_ha', 'H-A', 'harvest', 'th_a', 'u_fns', '2027-02-10T12:00:00', 'app', NULL);
INSERT INTO lot_revision      VALUES ('lot_ha_r1', 'lot_ha', 1, 'Hạt mè thu hoạch', 400, 'kg', NULL, NULL, 'u_fns', '2027-02-10T12:00:00', NULL);

-- Hộ B: 350 kg, có phiếu cân
INSERT INTO activity          VALUES ('th_b', 'cy_b', 'at_me_th', 'u_b', '2027-02-10T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('th_b_r1', 'th_b', 1, '2027-02-10T08:00:00', 'day', 'u_b', NULL, 'u_b', '2027-02-10T12:00:00', NULL);
INSERT INTO evidence          VALUES ('ev_th_b_w', 'weighing_slip', 's3://farm-b/th_b_weigh.pdf', 'sha_th_b_w', NULL, NULL, NULL, 'u_b', '2027-02-10T12:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_th_b_w', 'ev_th_b_w', 'th_b_r1', NULL, NULL, NULL, NULL, 'u_b', '2027-02-10T12:00:00');
INSERT INTO lot               VALUES ('lot_hb', 'H-B', 'harvest', 'th_b', 'u_fns', '2027-02-10T12:00:00', 'app', NULL);
INSERT INTO lot_revision      VALUES ('lot_hb_r1', 'lot_hb', 1, 'Hạt mè thu hoạch', 350, 'kg', NULL, NULL, 'u_fns', '2027-02-10T12:00:00', NULL);

-- Hộ C: 250 kg, có phiếu cân
INSERT INTO activity          VALUES ('th_c', 'cy_c', 'at_me_th', 'u_c', '2027-02-10T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('th_c_r1', 'th_c', 1, '2027-02-10T08:00:00', 'day', 'u_c', NULL, 'u_c', '2027-02-10T12:00:00', NULL);
INSERT INTO evidence          VALUES ('ev_th_c_w', 'weighing_slip', 's3://farm-c/th_c_weigh.pdf', 'sha_th_c_w', NULL, NULL, NULL, 'u_c', '2027-02-10T12:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_th_c_w', 'ev_th_c_w', 'th_c_r1', NULL, NULL, NULL, NULL, 'u_c', '2027-02-10T12:00:00');
INSERT INTO lot               VALUES ('lot_hc', 'H-C', 'harvest', 'th_c', 'u_fns', '2027-02-10T12:00:00', 'app', NULL);
INSERT INTO lot_revision      VALUES ('lot_hc_r1', 'lot_hc', 1, 'Hạt mè thu hoạch', 250, 'kg', NULL, NULL, 'u_fns', '2027-02-10T12:00:00', NULL);

-- =====================================================================
-- CỤM 5 · Chuỗi sau thu hoạch: gộp → chế biến → đóng gói
-- =====================================================================

-- Lô gộp RAW-01 (1000 kg từ 3 hộ)
INSERT INTO lot          VALUES ('lot_raw', 'RAW-01', 'aggregated', NULL, 'u_fns', '2027-02-12T09:00:00', 'app', NULL);
INSERT INTO lot_revision VALUES ('lot_raw_r1', 'lot_raw', 1, 'Hạt mè thô', 1000, 'kg', NULL, NULL, 'u_fns', '2027-02-12T09:00:00', NULL);

INSERT INTO lot_event VALUES ('ev_gop', 'aggregation', 'lot_raw', NULL, '2027-02-12T09:00:00', 'minute', 'fac_tm', 'u_fns', 'u_fns', '2027-02-12T09:00:00', 'app', NULL);
INSERT INTO lot_input VALUES ('ev_gop', 'lot_ha', 400, 'kg', 'u_fns', '2027-02-12T09:00:00');
INSERT INTO lot_input VALUES ('ev_gop', 'lot_hb', 350, 'kg', 'u_fns', '2027-02-12T09:00:00');
INSERT INTO lot_input VALUES ('ev_gop', 'lot_hc', 250, 'kg', 'u_fns', '2027-02-12T09:00:00');
INSERT INTO evidence  VALUES ('ev_gop_w', 'weighing_slip', 's3://fac-tm/gop_weigh.pdf', 'sha_gop_w', NULL, NULL, NULL, 'u_fns', '2027-02-12T09:00:00', 'app', NULL);
INSERT INTO evidence_link VALUES ('lk_gop_w', 'ev_gop_w', NULL, NULL, 'ev_gop', NULL, NULL, 'u_fns', '2027-02-12T09:00:00');
INSERT INTO verification VALUES ('ver_gop', NULL, NULL, 'ev_gop', 'u_qa', 'verified', 'document_review', NULL, NULL, NULL, '2027-02-12T10:00:00', '2027-02-12T10:00:00');

-- Sửa khối lượng RAW-01 sau khi sàng (995 kg thực tế)
INSERT INTO lot_revision VALUES ('lot_raw_r2', 'lot_raw', 2, 'Hạt mè thô', 995, 'kg', NULL, NULL, 'u_fns', '2027-02-13T10:00:00', 'Cân lại sau khi sàng lần cuối');

-- Vận chuyển RAW-01 → nhà máy
INSERT INTO lot_event VALUES ('ev_vc', 'transport', NULL, 'lot_raw', '2027-02-13T14:00:00', 'day', 'fac_nm', 'u_fns', 'u_fns', '2027-02-13T14:00:00', 'app', NULL);

-- Lô ép dầu PROC-01 (400 lít dầu mè rang từ 1000 kg hạt)
INSERT INTO lot          VALUES ('lot_proc', 'PROC-01', 'processed', NULL, 'u_fns', '2027-02-20T08:00:00', 'app', NULL);
INSERT INTO lot_revision VALUES ('lot_proc_r1', 'lot_proc', 1, 'Dầu mè rang', 400, 'l', NULL, NULL, 'u_fns', '2027-02-20T08:00:00', NULL);
INSERT INTO lot_event    VALUES ('ev_ep', 'transformation', 'lot_proc', NULL, '2027-02-20T08:00:00', 'minute', 'fac_nm', 'u_fns', 'u_fns', '2027-02-20T08:00:00', 'app', NULL);
INSERT INTO lot_input    VALUES ('ev_ep', 'lot_raw', 1000, 'kg', 'u_fns', '2027-02-20T08:00:00');
INSERT INTO evidence     VALUES ('ev_proc_lab', 'lab_report', 's3://fac-nm/proc_lab.pdf', 'sha_proc_lab', NULL, NULL, NULL, 'u_fns', '2027-02-20T18:00:00', 'app', NULL);
INSERT INTO evidence_link VALUES ('lk_proc_lab', 'ev_proc_lab', NULL, 'lot_proc_r1', NULL, NULL, NULL, 'u_fns', '2027-02-20T18:00:00');

-- Đóng gói: QR-80 (2500 chai × 80ml = 200 lít)
INSERT INTO lot          VALUES ('lot_b80',  'QR-80',  'packaged', NULL, 'u_fns', '2027-02-22T10:00:00', 'app', NULL);
INSERT INTO lot_revision VALUES ('lot_b80_r1',  'lot_b80',  1, 'Dầu mè rang', 2500, 'unit', 'Chai thủy tinh 80ml',  NULL, 'u_fns', '2027-02-22T10:00:00', NULL);
INSERT INTO lot_event    VALUES ('ev_b80',   'packaging', 'lot_b80',  NULL, '2027-02-22T10:00:00', 'minute', 'fac_nm', 'u_fns', 'u_fns', '2027-02-22T10:00:00', 'app', NULL);
INSERT INTO lot_input    VALUES ('ev_b80',   'lot_proc', 200, 'l', 'u_fns', '2027-02-22T10:00:00');

-- Đóng gói: QR-250 (800 chai × 250ml = 200 lít)
INSERT INTO lot          VALUES ('lot_b250', 'QR-250', 'packaged', NULL, 'u_fns', '2027-02-22T10:00:00', 'app', NULL);
INSERT INTO lot_revision VALUES ('lot_b250_r1', 'lot_b250', 1, 'Dầu mè rang', 800,  'unit', 'Chai thủy tinh 250ml', NULL, 'u_fns', '2027-02-22T10:00:00', NULL);
INSERT INTO lot_event    VALUES ('ev_b250',  'packaging', 'lot_b250', NULL, '2027-02-22T10:00:00', 'minute', 'fac_nm', 'u_fns', 'u_fns', '2027-02-22T10:00:00', 'app', NULL);
INSERT INTO lot_input    VALUES ('ev_b250',  'lot_proc', 200, 'l', 'u_fns', '2027-02-22T10:00:00');

-- =====================================================================
-- CỤM 6 · Cảm biến
-- =====================================================================

INSERT INTO device      VALUES ('dev_sm1', 'u_dev', 'soil_moisture', '%', 'p_a1', NULL, 'u_fns', '2026-11-15T07:00:00');
INSERT INTO observation VALUES ('obs_1', 'dev_sm1', '2026-12-01T06:00:00', 23.5, 'p_a1', NULL, '2026-12-01T06:01:00', 'iot_gateway', 'GW-0001');
INSERT INTO observation VALUES ('obs_2', 'dev_sm1', '2026-12-08T06:00:00', 21.0, 'p_a1', NULL, '2026-12-08T06:01:00', 'iot_gateway', 'GW-0002');
INSERT INTO observation VALUES ('obs_3', 'dev_sm1', '2027-01-05T06:00:00', 18.5, 'p_a1', NULL, '2027-01-05T06:01:00', 'iot_gateway', 'GW-0003');
-- Evidence loại sensor (1-1 với observation)
INSERT INTO evidence VALUES ('ev_obs_1', 'sensor', NULL, NULL, 'obs_1', NULL, NULL, 'u_fns', '2026-12-01T06:01:00', 'iot_gateway', 'GW-EV-0001');
INSERT INTO evidence VALUES ('ev_obs_2', 'sensor', NULL, NULL, 'obs_2', NULL, NULL, 'u_fns', '2026-12-08T06:01:00', 'iot_gateway', 'GW-EV-0002');
INSERT INTO evidence VALUES ('ev_obs_3', 'sensor', NULL, NULL, 'obs_3', NULL, NULL, 'u_fns', '2027-01-05T06:01:00', 'iot_gateway', 'GW-EV-0003');
INSERT INTO evidence_link VALUES ('lk_obs_1', 'ev_obs_1', NULL, NULL, NULL, 'p_a1', NULL, 'u_fns', '2026-12-01T06:01:00');
INSERT INTO evidence_link VALUES ('lk_obs_2', 'ev_obs_2', NULL, NULL, NULL, 'p_a1', NULL, 'u_fns', '2026-12-08T06:01:00');
INSERT INTO evidence_link VALUES ('lk_obs_3', 'ev_obs_3', NULL, NULL, NULL, 'p_a1', NULL, 'u_fns', '2027-01-05T06:01:00');

-- =====================================================================
-- CỤM 7 · Chứng nhận
-- =====================================================================

INSERT INTO certification VALUES (
  'cert_vg_a', 'VietGAP', 'VG-2026-123', 'u_cert',
  '2026-01-01', '2027-01-31',
  'f_a', NULL, NULL, NULL,
  'u_fns', '2026-01-05T08:00:00'
);
INSERT INTO evidence      VALUES ('ev_cert_a', 'document', 's3://certs/VG-2026-123.pdf', 'sha_cert_a', NULL, NULL, NULL, 'u_fns', '2026-01-05T08:00:00', 'app', NULL);
INSERT INTO evidence_link VALUES ('lk_cert_a', 'ev_cert_a', NULL, NULL, NULL, NULL, 'cert_vg_a', 'u_fns', '2026-01-05T08:00:00');

-- =====================================================================
-- Kết quả kỳ vọng khi truy vấn:
--
--  v_activity_status:
--    bt_a_r1 → (complete,   verified)    -- Hộ A bón thúc đủ minh chứng
--    bt_b_r2 → (missing_evidence, unverified) -- Hộ B bản 2 thiếu ảnh
--    th_a_r1 → (complete, unverified)    -- Thu hoạch A đủ phiếu cân
--
--  v_cycle_completeness:
--    cy_a  → complete
--    cy_b  → incomplete  (bt_b bản 2 missing_evidence)
--    cy_c  → incomplete  (not_recorded TOP_DRESS_1)
--    cy_c2 → undetermined (không có cycle_anchor)
--
--  v_lot_sources WHERE root_lot_id = 'lot_b80':
--    lot_ha: share=0.4,  source_status=harvest   (H-A 400/1000)
--    lot_hb: share=0.35, source_status=harvest   (H-B 350/1000)
--    lot_hc: share=0.25, source_status=harvest   (H-C 250/1000)
--
--  v_integrity_issues:
--    missing_phi_rule → ph_b (Thuốc Y dùng trên mè nhưng không có PHI rule)
-- =====================================================================
