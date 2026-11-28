-- =====================================================================
-- seed_lac.sql — Thêm cây lạc vào cùng DB đã có seed_me.sql
-- Đề tài #6 · Agricultural Digital Thread & Evidence-aware Traceability
--
-- ⚠  Điều kiện: seed_me.sql đã được nạp trước.
--    File này dùng lại agent, facility, vật tư từ seed_me.sql.
--
-- Thứ tự nạp đầy đủ:
--   schema.sql → triggers_<hệ>.sql → views_<hệ>.sql
--   → seed_me.sql → seed_lac.sql
--
-- ════════════════════════════════════════════════════════════════════
-- ★ MỤC ĐÍCH CHÍNH: chứng minh "đổi sang cây mới = chỉ thêm dữ liệu"
--   Toàn bộ file chỉ dùng INSERT, 0 lệnh DDL (CREATE/ALTER/DROP).
--   Điều này tái hiện ca F15 trong smoke_test.py.
-- ════════════════════════════════════════════════════════════════════
--
-- Tình huống được tái hiện:
--   D. Hộ D — vụ Hè Thu 2027 trên cây lạc, cùng vùng Lương Hòa
--             Bón lót đủ minh chứng + xác minh           → complete / verified
--             Phun thuốc Y (có PHI 5 ngày cho LẠC,       → KHÔNG vi phạm
--             khác với mè chưa có rule)
--             Chuỗi: thu hoạch → rang → đóng gói túi zip
--
-- =====================================================================


-- =====================================================================
-- CỤM 1 · Cấu hình cây lạc (PEANUT) — chỉ dữ liệu, không có DDL
-- =====================================================================

-- Hộ D (nông hộ mới, tham gia vụ lạc)
INSERT INTO agent VALUES ('u_d', 'person', 'Hộ D (Phạm Thị Duyên)', 'farmer', 'u_fns', '2027-03-01T08:00:00');

INSERT INTO crop_profile VALUES (
  'cp_lac', 'PEANUT', 'Lạc L14', 1, 'sowing',
  '{"protein_pct":"number","fat_pct":"number"}',
  'Mock — chưa có quy trình canh tác chính thức',
  '2026-01-01'
);
INSERT INTO variety VALUES ('v_lac', 'PEANUT', 'Lạc L14 (nhập khẩu)', '{}', 'Mock — giả định nhóm');

-- Giai đoạn
INSERT INTO stage VALUES ('st_lac_lp', 'cp_lac', 1, 'Làm đất – Gieo');
INSERT INTO stage VALUES ('st_lac_cs', 'cp_lac', 2, 'Chăm sóc');
INSERT INTO stage VALUES ('st_lac_th', 'cp_lac', 3, 'Thu hoạch');

-- Loại hoạt động
-- (id, stage_id, code, name, requirement, offset_days, tolerance_days, produces_lot, uses_inputs, attr_schema, public_level, rule_source, is_assumption)
INSERT INTO activity_type VALUES ('at_lac_bl',   'st_lac_cs', 'BASE_FERT', 'Bón lót',              'mandatory',   10,   3, 0, 1, NULL, 'detail',  'Mock', 1);
INSERT INTO activity_type VALUES ('at_lac_lcoi', 'st_lac_cs', 'WEED',      'Làm cỏ',               'conditional', NULL, 0, 0, 0, NULL, 'detail',  'Mock', 1);
INSERT INTO activity_type VALUES ('at_lac_phun', 'st_lac_cs', 'SPRAY',     'Phun thuốc BVTV',      'conditional', NULL, 0, 0, 1, NULL, 'detail',  'Mock', 1);
INSERT INTO activity_type VALUES ('at_lac_th',   'st_lac_th', 'HARVEST',   'Nhổ, phơi, tách vỏ',  'mandatory',   90,  10, 1, 0, NULL, 'summary', 'Mock', 1);

-- Yêu cầu minh chứng
INSERT INTO evidence_requirement VALUES ('er_lac_bl_photo', 'at_lac_bl',   NULL, 'photo',         1, 'Mock', 1);
INSERT INTO evidence_requirement VALUES ('er_lac_th_weigh', 'at_lac_th',   NULL, 'weighing_slip', 1, 'Mock', 1);
INSERT INTO evidence_requirement VALUES ('er_lac_phun_p',   'at_lac_phun', NULL, 'photo',         1, 'Mock', 1);

-- PHI rule: Thuốc Y có 5 ngày cách ly với LẠC (đã có PHI cho PEANUT)
-- So sánh với seed_me.sql: m_y không có rule cho SESAME → missing_phi_rule bên mè
-- Bên lạc: có rule → không vi phạm nếu hộ D tuân thủ
INSERT INTO material_crop_rule VALUES ('m_y', 'PEANUT', 5, 'Giả định nhóm — cần đối chiếu nhãn thuốc', 1);

-- =====================================================================
-- CỤM 2 · Vụ Hè Thu 2027, Nông hộ D, Lô đất, Chu kỳ
-- =====================================================================

INSERT INTO season VALUES (
  'ss_ht2027', 'u_fns', 'Hè Thu 2027', 'PEANUT',
  '2027-04-01', '2027-08-31',
  'u_fns', '2027-03-01T08:00:00'
);

INSERT INTO farm VALUES ('f_d', 'u_d', 'Hộ D', 'Tây Ninh', 'Lương Hòa', NULL, 'u_fns', '2027-03-10T08:00:00');
INSERT INTO plot VALUES ('p_d1', 'f_d', 'L1', 4000, NULL, NULL, 'u_fns', '2027-03-10T08:00:00');

INSERT INTO cultivation_cycle VALUES (
  'cy_d', 'p_d1', 'cp_lac', 'v_lac', 'ss_ht2027',
  '2027-04-10', NULL,
  'u_fns', '2027-04-10T07:00:00'
);
INSERT INTO cycle_anchor VALUES ('an_d1', 'cy_d', 1, '2027-04-15', 'u_d', '2027-04-15T17:00:00', NULL);

-- =====================================================================
-- CỤM 3 · Hoạt động canh tác — Hộ D (lạc)
-- =====================================================================

-- Bón lót: đúng lịch, có ảnh, có vật tư, đã xác minh → complete / verified
INSERT INTO activity          VALUES ('bl_d', 'cy_d', 'at_lac_bl', 'u_d', '2027-04-10T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('bl_d_r1', 'bl_d', 1, '2027-04-25T08:00:00', 'day', 'u_d', NULL, 'u_d', '2027-04-25T17:00:00', NULL);
INSERT INTO activity_input    VALUES ('bl_d_r1', 'm_ure', 20, 'kg');
INSERT INTO evidence          VALUES ('ev_bl_d_1', 'photo', 's3://farm-d/bl_d_1.jpg', 'sha_bl_d_1', NULL, NULL, NULL, 'u_d', '2027-04-25T17:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_bl_d_1', 'ev_bl_d_1', 'bl_d_r1', NULL, NULL, NULL, NULL, 'u_d', '2027-04-25T17:00:00');
INSERT INTO verification      VALUES ('ver_bl_d', 'bl_d_r1', NULL, NULL, 'u_ktv', 'verified', 'field_visit', NULL, NULL, NULL, '2027-05-02T09:00:00', '2027-05-02T09:00:00');

-- Phun thuốc Y — ngày 2027-07-04 (10 ngày trước thu hoạch 14/7)
-- PHI lạc = 5 ngày → 10 >= 5 → KHÔNG vi phạm (đối chiếu với bên mè: vi phạm do không có rule)
INSERT INTO activity          VALUES ('ph_d', 'cy_d', 'at_lac_phun', 'u_d', '2027-04-10T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('ph_d_r1', 'ph_d', 1, '2027-07-04T08:00:00', 'day', 'u_d', NULL, 'u_d', '2027-07-04T17:00:00', NULL);
INSERT INTO activity_input    VALUES ('ph_d_r1', 'm_y', 100, 'ml');
INSERT INTO evidence          VALUES ('ev_ph_d_1', 'photo', 's3://farm-d/ph_d_1.jpg', 'sha_ph_d_1', NULL, NULL, NULL, 'u_d', '2027-07-04T17:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_ph_d_1', 'ev_ph_d_1', 'ph_d_r1', NULL, NULL, NULL, NULL, 'u_d', '2027-07-04T17:00:00');

-- =====================================================================
-- CỤM 4 · Thu hoạch + Lô thu hoạch
-- =====================================================================

-- Hộ D: 450 kg lạc tươi
INSERT INTO activity          VALUES ('th_d', 'cy_d', 'at_lac_th', 'u_d', '2027-07-14T07:00:00', 'app', NULL);
INSERT INTO activity_revision VALUES ('th_d_r1', 'th_d', 1, '2027-07-14T08:00:00', 'day', 'u_d', NULL, 'u_d', '2027-07-14T12:00:00', NULL);
INSERT INTO evidence          VALUES ('ev_th_d_w', 'weighing_slip', 's3://farm-d/th_d_weigh.pdf', 'sha_th_d_w', NULL, NULL, NULL, 'u_d', '2027-07-14T12:00:00', 'app', NULL);
INSERT INTO evidence_link     VALUES ('lk_th_d_w', 'ev_th_d_w', 'th_d_r1', NULL, NULL, NULL, NULL, 'u_d', '2027-07-14T12:00:00');
INSERT INTO lot               VALUES ('lot_hd', 'H-D', 'harvest', 'th_d', 'u_fns', '2027-07-14T12:00:00', 'app', NULL);
INSERT INTO lot_revision      VALUES ('lot_hd_r1', 'lot_hd', 1, 'Lạc tươi', 450, 'kg', NULL, NULL, 'u_fns', '2027-07-14T12:00:00', NULL);

-- =====================================================================
-- CỤM 5 · Chuỗi sau thu hoạch: rang → đóng gói túi zip
-- =====================================================================

-- Lô rang lạc LAC-01 (450 kg → 400 kg sau khi sấy, có hao hụt)
INSERT INTO lot          VALUES ('lot_lac_rang', 'LAC-01', 'processed', NULL, 'u_fns', '2027-07-16T08:00:00', 'app', NULL);
INSERT INTO lot_revision VALUES ('lot_lac_rang_r1', 'lot_lac_rang', 1, 'Lạc rang', 400, 'kg', NULL, NULL, 'u_fns', '2027-07-16T08:00:00', NULL);
INSERT INTO lot_event    VALUES ('ev_rang', 'transformation', 'lot_lac_rang', NULL, '2027-07-16T08:00:00', 'minute', 'fac_nm', 'u_fns', 'u_fns', '2027-07-16T08:00:00', 'app', NULL);
INSERT INTO lot_input    VALUES ('ev_rang', 'lot_hd', 450, 'kg', 'u_fns', '2027-07-16T08:00:00');

-- Vận chuyển LAC-01 → kho đóng gói
INSERT INTO lot_event VALUES ('ev_lac_vc', 'transport', NULL, 'lot_lac_rang', '2027-07-16T18:00:00', 'day', 'fac_nm', 'u_fns', 'u_fns', '2027-07-16T18:00:00', 'app', NULL);

-- Đóng gói: QR-LAC-200 (1200 túi × 200g = 240 kg)
INSERT INTO lot          VALUES ('lot_lac_pkg', 'QR-LAC-200', 'packaged', NULL, 'u_fns', '2027-07-17T10:00:00', 'app', NULL);
INSERT INTO lot_revision VALUES ('lot_lac_pkg_r1', 'lot_lac_pkg', 1, 'Lạc rang', 1200, 'unit', 'Túi zip 200g', NULL, 'u_fns', '2027-07-17T10:00:00', NULL);
INSERT INTO lot_event    VALUES ('ev_lac_pkg', 'packaging', 'lot_lac_pkg', NULL, '2027-07-17T10:00:00', 'minute', 'fac_nm', 'u_fns', 'u_fns', '2027-07-17T10:00:00', 'app', NULL);
INSERT INTO lot_input    VALUES ('ev_lac_pkg', 'lot_lac_rang', 240, 'kg', 'u_fns', '2027-07-17T10:00:00');

-- =====================================================================
-- Kết quả kỳ vọng khi truy vấn (sau khi nạp cả seed_me.sql + seed_lac.sql):
--
--  v_activity_status:
--    bl_d_r1 → (complete, verified)       -- Hộ D bón lót đủ minh chứng
--    ph_d_r1 → (complete, unverified)     -- Phun thuốc có ảnh
--
--  v_cycle_completeness:
--    cy_d → complete
--
--  v_lot_sources WHERE root_lot_id = 'lot_lac_pkg':
--    lot_hd: share=1.0, source_status=harvest  (1 nguồn duy nhất)
--
--  v_integrity_issues:
--    -- KHÔNG có missing_phi_rule cho ph_d
--       (m_y có rule 5 ngày cho PEANUT, hộ D phun ngày 4/7, thu ngày 14/7 → 10 ngày ≥ 5)
--    -- So sánh: ph_b ở seed_me.sql VẪN vi phạm (m_y không có rule cho SESAME)
--
--  Đếm crop_profile: 2 (SESAME + PEANUT) — 0 lệnh DDL, chỉ INSERT
-- =====================================================================
