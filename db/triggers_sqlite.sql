-- Trigger cho SQLite (nạp sau schema.sql) — v0.5. SINH TỰ ĐỘNG bởi gen_triggers.py, đừng sửa tay.

-- T1 · Chỉ ghi thêm: chặn UPDATE/DELETE (chặn INSERT OR REPLACE: xem T0 ở cuối file)
CREATE TRIGGER trg_activity_no_update BEFORE UPDATE ON activity BEGIN SELECT RAISE(ABORT, 'append-only: activity không cho UPDATE'); END;
CREATE TRIGGER trg_activity_no_delete BEFORE DELETE ON activity BEGIN SELECT RAISE(ABORT, 'append-only: activity không cho DELETE'); END;
CREATE TRIGGER trg_activity_revision_no_update BEFORE UPDATE ON activity_revision BEGIN SELECT RAISE(ABORT, 'append-only: activity_revision không cho UPDATE'); END;
CREATE TRIGGER trg_activity_revision_no_delete BEFORE DELETE ON activity_revision BEGIN SELECT RAISE(ABORT, 'append-only: activity_revision không cho DELETE'); END;
CREATE TRIGGER trg_activity_input_no_update BEFORE UPDATE ON activity_input BEGIN SELECT RAISE(ABORT, 'append-only: activity_input không cho UPDATE'); END;
CREATE TRIGGER trg_activity_input_no_delete BEFORE DELETE ON activity_input BEGIN SELECT RAISE(ABORT, 'append-only: activity_input không cho DELETE'); END;
CREATE TRIGGER trg_observation_no_update BEFORE UPDATE ON observation BEGIN SELECT RAISE(ABORT, 'append-only: observation không cho UPDATE'); END;
CREATE TRIGGER trg_observation_no_delete BEFORE DELETE ON observation BEGIN SELECT RAISE(ABORT, 'append-only: observation không cho DELETE'); END;
CREATE TRIGGER trg_lot_no_update BEFORE UPDATE ON lot BEGIN SELECT RAISE(ABORT, 'append-only: lot không cho UPDATE'); END;
CREATE TRIGGER trg_lot_no_delete BEFORE DELETE ON lot BEGIN SELECT RAISE(ABORT, 'append-only: lot không cho DELETE'); END;
CREATE TRIGGER trg_lot_revision_no_update BEFORE UPDATE ON lot_revision BEGIN SELECT RAISE(ABORT, 'append-only: lot_revision không cho UPDATE'); END;
CREATE TRIGGER trg_lot_revision_no_delete BEFORE DELETE ON lot_revision BEGIN SELECT RAISE(ABORT, 'append-only: lot_revision không cho DELETE'); END;
CREATE TRIGGER trg_lot_event_no_update BEFORE UPDATE ON lot_event BEGIN SELECT RAISE(ABORT, 'append-only: lot_event không cho UPDATE'); END;
CREATE TRIGGER trg_lot_event_no_delete BEFORE DELETE ON lot_event BEGIN SELECT RAISE(ABORT, 'append-only: lot_event không cho DELETE'); END;
CREATE TRIGGER trg_lot_input_no_update BEFORE UPDATE ON lot_input BEGIN SELECT RAISE(ABORT, 'append-only: lot_input không cho UPDATE'); END;
CREATE TRIGGER trg_lot_input_no_delete BEFORE DELETE ON lot_input BEGIN SELECT RAISE(ABORT, 'append-only: lot_input không cho DELETE'); END;
CREATE TRIGGER trg_evidence_no_update BEFORE UPDATE ON evidence BEGIN SELECT RAISE(ABORT, 'append-only: evidence không cho UPDATE'); END;
CREATE TRIGGER trg_evidence_no_delete BEFORE DELETE ON evidence BEGIN SELECT RAISE(ABORT, 'append-only: evidence không cho DELETE'); END;
CREATE TRIGGER trg_evidence_link_no_update BEFORE UPDATE ON evidence_link BEGIN SELECT RAISE(ABORT, 'append-only: evidence_link không cho UPDATE'); END;
CREATE TRIGGER trg_evidence_link_no_delete BEFORE DELETE ON evidence_link BEGIN SELECT RAISE(ABORT, 'append-only: evidence_link không cho DELETE'); END;
CREATE TRIGGER trg_verification_no_update BEFORE UPDATE ON verification BEGIN SELECT RAISE(ABORT, 'append-only: verification không cho UPDATE'); END;
CREATE TRIGGER trg_verification_no_delete BEFORE DELETE ON verification BEGIN SELECT RAISE(ABORT, 'append-only: verification không cho DELETE'); END;
CREATE TRIGGER trg_cycle_anchor_no_update BEFORE UPDATE ON cycle_anchor BEGIN SELECT RAISE(ABORT, 'append-only: cycle_anchor không cho UPDATE'); END;
CREATE TRIGGER trg_cycle_anchor_no_delete BEFORE DELETE ON cycle_anchor BEGIN SELECT RAISE(ABORT, 'append-only: cycle_anchor không cho DELETE'); END;
CREATE TRIGGER trg_crop_profile_no_update BEFORE UPDATE ON crop_profile BEGIN SELECT RAISE(ABORT, 'append-only: crop_profile không cho UPDATE'); END;
CREATE TRIGGER trg_crop_profile_no_delete BEFORE DELETE ON crop_profile BEGIN SELECT RAISE(ABORT, 'append-only: crop_profile không cho DELETE'); END;
CREATE TRIGGER trg_stage_no_update BEFORE UPDATE ON stage BEGIN SELECT RAISE(ABORT, 'append-only: stage không cho UPDATE'); END;
CREATE TRIGGER trg_stage_no_delete BEFORE DELETE ON stage BEGIN SELECT RAISE(ABORT, 'append-only: stage không cho DELETE'); END;
CREATE TRIGGER trg_activity_type_no_update BEFORE UPDATE ON activity_type BEGIN SELECT RAISE(ABORT, 'append-only: activity_type không cho UPDATE'); END;
CREATE TRIGGER trg_activity_type_no_delete BEFORE DELETE ON activity_type BEGIN SELECT RAISE(ABORT, 'append-only: activity_type không cho DELETE'); END;
CREATE TRIGGER trg_evidence_requirement_no_update BEFORE UPDATE ON evidence_requirement BEGIN SELECT RAISE(ABORT, 'append-only: evidence_requirement không cho UPDATE'); END;
CREATE TRIGGER trg_evidence_requirement_no_delete BEFORE DELETE ON evidence_requirement BEGIN SELECT RAISE(ABORT, 'append-only: evidence_requirement không cho DELETE'); END;
CREATE TRIGGER trg_material_crop_rule_no_update BEFORE UPDATE ON material_crop_rule BEGIN SELECT RAISE(ABORT, 'append-only: material_crop_rule không cho UPDATE'); END;
CREATE TRIGGER trg_material_crop_rule_no_delete BEFORE DELETE ON material_crop_rule BEGIN SELECT RAISE(ABORT, 'append-only: material_crop_rule không cho DELETE'); END;

-- T1b · Số bản ghi tăng đúng 1 (không nhảy cóc)
CREATE TRIGGER trg_activity_revision_seq BEFORE INSERT ON activity_revision
WHEN NEW.revision_no <> COALESCE((SELECT MAX(revision_no) FROM activity_revision WHERE activity_id = NEW.activity_id), 0) + 1
BEGIN SELECT RAISE(ABORT, 'activity_revision: revision_no phải tăng đúng 1'); END;
CREATE TRIGGER trg_lot_revision_seq BEFORE INSERT ON lot_revision
WHEN NEW.revision_no <> COALESCE((SELECT MAX(revision_no) FROM lot_revision WHERE lot_id = NEW.lot_id), 0) + 1
BEGIN SELECT RAISE(ABORT, 'lot_revision: revision_no phải tăng đúng 1'); END;
CREATE TRIGGER trg_cycle_anchor_seq BEFORE INSERT ON cycle_anchor
WHEN NEW.revision_no <> COALESCE((SELECT MAX(revision_no) FROM cycle_anchor WHERE cycle_id = NEW.cycle_id), 0) + 1
BEGIN SELECT RAISE(ABORT, 'cycle_anchor: revision_no phải tăng đúng 1'); END;

-- T1c · Chu kỳ canh tác: chỉ được đóng (closed_at NULL → ngày) một lần, không trước hoạt động cuối; không xóa
CREATE TRIGGER trg_cycle_guard_update BEFORE UPDATE OF cycle_id, plot_id, crop_profile_id, variety_id, season_id, started_at, created_by, created_at ON cultivation_cycle
BEGIN SELECT RAISE(ABORT, 'cultivation_cycle: chỉ được cập nhật closed_at; mốc lịch sửa qua cycle_anchor'); END;
CREATE TRIGGER trg_cycle_close BEFORE UPDATE OF closed_at ON cultivation_cycle
BEGIN
  SELECT RAISE(ABORT, 'cultivation_cycle: chu kỳ đã đóng, không đổi hoặc mở lại closed_at') WHERE OLD.closed_at IS NOT NULL;
  SELECT RAISE(ABORT, 'cultivation_cycle: closed_at không được NULL') WHERE NEW.closed_at IS NULL;
  SELECT RAISE(ABORT, 'cultivation_cycle: closed_at trước ngày hoạt động cuối của chu kỳ')
  WHERE EXISTS (SELECT 1 FROM activity a JOIN activity_revision r ON r.activity_id = a.activity_id
                WHERE a.cycle_id = OLD.cycle_id AND date(r.performed_at) > NEW.closed_at);
END;
CREATE TRIGGER trg_cycle_no_delete BEFORE DELETE ON cultivation_cycle
BEGIN SELECT RAISE(ABORT, 'cultivation_cycle: không cho DELETE'); END;

-- T1d · Lô đất và nông hộ: không đổi chủ / chuyển lô đất sang hộ khác / đổi mã; không xóa
CREATE TRIGGER trg_plot_guard BEFORE UPDATE OF plot_id, farm_id, code, created_by, created_at ON plot
BEGIN SELECT RAISE(ABORT, 'plot: không đổi định danh, hộ sở hữu hoặc mã lô đất'); END;
CREATE TRIGGER trg_plot_no_delete BEFORE DELETE ON plot BEGIN SELECT RAISE(ABORT, 'plot: không cho DELETE'); END;
CREATE TRIGGER trg_farm_guard BEFORE UPDATE OF farm_id, owner_agent_id, created_by, created_at ON farm
BEGIN SELECT RAISE(ABORT, 'farm: không đổi định danh hoặc chủ hộ'); END;
CREATE TRIGGER trg_farm_no_delete BEFORE DELETE ON farm BEGIN SELECT RAISE(ABORT, 'farm: không cho DELETE'); END;

-- T2 · Sự kiện lô: loại lô đầu ra phải khớp loại sự kiện
CREATE TRIGGER trg_lot_event_output_type BEFORE INSERT ON lot_event
WHEN NEW.output_lot_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'lot_event: loại lô đầu ra không khớp loại sự kiện')
  WHERE (SELECT lot_type FROM lot WHERE lot_id = NEW.output_lot_id) IS NOT CASE NEW.event_type WHEN 'aggregation' THEN 'aggregated' WHEN 'transformation' THEN 'processed' WHEN 'packaging' THEN 'packaged' END;
END;

-- T3 · Cạnh lô: không cho mốc; không tạo vòng; không thêm đầu vào khi lô ra đã được dùng tiếp hoặc sự kiện đã được xác minh
CREATE TRIGGER trg_lot_input_check BEFORE INSERT ON lot_input
BEGIN
  SELECT RAISE(ABORT, 'lot_input: mốc thu mua/vận chuyển không có đầu vào')
  WHERE (SELECT event_type FROM lot_event WHERE event_id = NEW.event_id) IN ('purchase','transport');
  SELECT RAISE(ABORT, 'lot_input: tạo vòng trong đồ thị lô')
  WHERE EXISTS (
    WITH RECURSIVE up(x) AS (
      SELECT NEW.input_lot_id
      UNION
      SELECT li.input_lot_id FROM lot_input li
      JOIN lot_event ev ON ev.event_id = li.event_id
      JOIN up ON ev.output_lot_id = up.x
    )
    SELECT 1 FROM up WHERE x = (SELECT output_lot_id FROM lot_event WHERE event_id = NEW.event_id));
  SELECT RAISE(ABORT, 'lot_input: lô đầu ra đã được dùng tiếp, không thêm đầu vào hồi tố')
  WHERE EXISTS (SELECT 1 FROM lot_input li WHERE li.input_lot_id = (SELECT output_lot_id FROM lot_event WHERE event_id = NEW.event_id));
  SELECT RAISE(ABORT, 'lot_input: sự kiện đã được xác minh, không thêm đầu vào')
  WHERE EXISTS (SELECT 1 FROM verification v WHERE v.lot_event_id = NEW.event_id);
END;

-- T4 · Lô thu hoạch phải sinh ra từ hoạt động loại thu hoạch
CREATE TRIGGER trg_lot_harvest_check BEFORE INSERT ON lot
WHEN NEW.harvest_activity_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'lot: hoạt động sinh lô phải là loại thu hoạch (produces_lot = 1)')
  WHERE NOT EXISTS (SELECT 1 FROM activity a JOIN activity_type t ON t.activity_type_id = a.activity_type_id
                    WHERE a.activity_id = NEW.harvest_activity_id AND t.produces_lot = 1);
END;

-- T5 · Xác minh: không tự xác minh; lần sau phải thay thế đúng kết luận hiệu lực của cùng đối tượng
CREATE TRIGGER trg_verification_check BEFORE INSERT ON verification
BEGIN
  SELECT RAISE(ABORT, 'verification: người xác minh trùng người làm/người ghi')
  WHERE (NEW.activity_revision_id IS NOT NULL AND EXISTS (SELECT 1 FROM activity_revision r
           WHERE r.revision_id = NEW.activity_revision_id AND NEW.verifier_id IN (r.performed_by, r.recorded_by)))
     OR (NEW.lot_event_id IS NOT NULL AND EXISTS (SELECT 1 FROM lot_event e
           WHERE e.event_id = NEW.lot_event_id AND NEW.verifier_id IN (e.performed_by, e.recorded_by)))
     OR (NEW.lot_revision_id IS NOT NULL AND EXISTS (SELECT 1 FROM lot_revision r
           WHERE r.lot_revision_id = NEW.lot_revision_id AND NEW.verifier_id = r.recorded_by));
  SELECT RAISE(ABORT, 'verification: chỉ được thay thế xác minh của cùng đối tượng')
  WHERE NEW.supersedes_verification_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM verification v WHERE v.verification_id = NEW.supersedes_verification_id
                      AND v.activity_revision_id IS NEW.activity_revision_id
                      AND v.lot_revision_id IS NEW.lot_revision_id
                      AND v.lot_event_id IS NEW.lot_event_id);
  SELECT RAISE(ABORT, 'verification: đã có kết luận hiệu lực, lần mới phải thay thế nó')
  WHERE EXISTS (SELECT 1 FROM verification v
                WHERE v.activity_revision_id IS NEW.activity_revision_id
                  AND v.lot_revision_id IS NEW.lot_revision_id
                  AND v.lot_event_id IS NEW.lot_event_id
                  AND NOT EXISTS (SELECT 1 FROM verification v2 WHERE v2.supersedes_verification_id = v.verification_id)
                  AND (NEW.supersedes_verification_id IS NULL OR NEW.supersedes_verification_id <> v.verification_id));
END;

-- T0 · Chặn INSERT OR REPLACE: REPLACE xóa dòng cũ mà KHÔNG chạy trigger DELETE (recursive_triggers tắt).
-- Đặt cuối file vì SQLite chạy trigger tạo sau trước → báo đúng lý do 'trùng khóa'.
CREATE TRIGGER trg_activity_no_replace BEFORE INSERT ON activity WHEN (EXISTS (SELECT 1 FROM activity x WHERE x.activity_id = NEW.activity_id))
  OR (NEW.external_ref IS NOT NULL AND EXISTS (SELECT 1 FROM activity x WHERE x.source_channel = NEW.source_channel AND x.external_ref = NEW.external_ref))
BEGIN SELECT RAISE(ABORT, 'append-only: activity trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_activity_revision_no_replace BEFORE INSERT ON activity_revision WHEN (EXISTS (SELECT 1 FROM activity_revision x WHERE x.revision_id = NEW.revision_id))
  OR (EXISTS (SELECT 1 FROM activity_revision x WHERE x.activity_id = NEW.activity_id AND x.revision_no = NEW.revision_no))
BEGIN SELECT RAISE(ABORT, 'append-only: activity_revision trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_activity_input_no_replace BEFORE INSERT ON activity_input WHEN (EXISTS (SELECT 1 FROM activity_input x WHERE x.revision_id = NEW.revision_id AND x.material_id = NEW.material_id))
BEGIN SELECT RAISE(ABORT, 'append-only: activity_input trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_observation_no_replace BEFORE INSERT ON observation WHEN (EXISTS (SELECT 1 FROM observation x WHERE x.observation_id = NEW.observation_id))
  OR (NEW.external_ref IS NOT NULL AND EXISTS (SELECT 1 FROM observation x WHERE x.source_channel = NEW.source_channel AND x.external_ref = NEW.external_ref))
BEGIN SELECT RAISE(ABORT, 'append-only: observation trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_lot_no_replace BEFORE INSERT ON lot WHEN (EXISTS (SELECT 1 FROM lot x WHERE x.lot_id = NEW.lot_id))
  OR (EXISTS (SELECT 1 FROM lot x WHERE x.public_code = NEW.public_code))
  OR (NEW.harvest_activity_id IS NOT NULL AND EXISTS (SELECT 1 FROM lot x WHERE x.harvest_activity_id = NEW.harvest_activity_id))
  OR (NEW.external_ref IS NOT NULL AND EXISTS (SELECT 1 FROM lot x WHERE x.source_channel = NEW.source_channel AND x.external_ref = NEW.external_ref))
BEGIN SELECT RAISE(ABORT, 'append-only: lot trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_lot_revision_no_replace BEFORE INSERT ON lot_revision WHEN (EXISTS (SELECT 1 FROM lot_revision x WHERE x.lot_revision_id = NEW.lot_revision_id))
  OR (EXISTS (SELECT 1 FROM lot_revision x WHERE x.lot_id = NEW.lot_id AND x.revision_no = NEW.revision_no))
BEGIN SELECT RAISE(ABORT, 'append-only: lot_revision trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_lot_event_no_replace BEFORE INSERT ON lot_event WHEN (EXISTS (SELECT 1 FROM lot_event x WHERE x.event_id = NEW.event_id))
  OR (NEW.output_lot_id IS NOT NULL AND EXISTS (SELECT 1 FROM lot_event x WHERE x.output_lot_id = NEW.output_lot_id))
  OR (NEW.external_ref IS NOT NULL AND EXISTS (SELECT 1 FROM lot_event x WHERE x.source_channel = NEW.source_channel AND x.external_ref = NEW.external_ref))
BEGIN SELECT RAISE(ABORT, 'append-only: lot_event trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_lot_input_no_replace BEFORE INSERT ON lot_input WHEN (EXISTS (SELECT 1 FROM lot_input x WHERE x.event_id = NEW.event_id AND x.input_lot_id = NEW.input_lot_id))
BEGIN SELECT RAISE(ABORT, 'append-only: lot_input trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_evidence_no_replace BEFORE INSERT ON evidence WHEN (EXISTS (SELECT 1 FROM evidence x WHERE x.evidence_id = NEW.evidence_id))
  OR (NEW.external_ref IS NOT NULL AND EXISTS (SELECT 1 FROM evidence x WHERE x.source_channel = NEW.source_channel AND x.external_ref = NEW.external_ref))
BEGIN SELECT RAISE(ABORT, 'append-only: evidence trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_evidence_link_no_replace BEFORE INSERT ON evidence_link WHEN (EXISTS (SELECT 1 FROM evidence_link x WHERE x.link_id = NEW.link_id))
  OR (NEW.activity_revision_id IS NOT NULL AND EXISTS (SELECT 1 FROM evidence_link x WHERE x.evidence_id = NEW.evidence_id AND x.activity_revision_id = NEW.activity_revision_id))
  OR (NEW.lot_revision_id IS NOT NULL AND EXISTS (SELECT 1 FROM evidence_link x WHERE x.evidence_id = NEW.evidence_id AND x.lot_revision_id = NEW.lot_revision_id))
  OR (NEW.lot_event_id IS NOT NULL AND EXISTS (SELECT 1 FROM evidence_link x WHERE x.evidence_id = NEW.evidence_id AND x.lot_event_id = NEW.lot_event_id))
  OR (NEW.plot_id IS NOT NULL AND EXISTS (SELECT 1 FROM evidence_link x WHERE x.evidence_id = NEW.evidence_id AND x.plot_id = NEW.plot_id))
  OR (NEW.certification_id IS NOT NULL AND EXISTS (SELECT 1 FROM evidence_link x WHERE x.evidence_id = NEW.evidence_id AND x.certification_id = NEW.certification_id))
BEGIN SELECT RAISE(ABORT, 'append-only: evidence_link trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_verification_no_replace BEFORE INSERT ON verification WHEN (EXISTS (SELECT 1 FROM verification x WHERE x.verification_id = NEW.verification_id))
  OR (NEW.supersedes_verification_id IS NOT NULL AND EXISTS (SELECT 1 FROM verification x WHERE x.supersedes_verification_id = NEW.supersedes_verification_id))
BEGIN SELECT RAISE(ABORT, 'append-only: verification trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_cycle_anchor_no_replace BEFORE INSERT ON cycle_anchor WHEN (EXISTS (SELECT 1 FROM cycle_anchor x WHERE x.cycle_anchor_id = NEW.cycle_anchor_id))
  OR (EXISTS (SELECT 1 FROM cycle_anchor x WHERE x.cycle_id = NEW.cycle_id AND x.revision_no = NEW.revision_no))
BEGIN SELECT RAISE(ABORT, 'append-only: cycle_anchor trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_crop_profile_no_replace BEFORE INSERT ON crop_profile WHEN (EXISTS (SELECT 1 FROM crop_profile x WHERE x.crop_profile_id = NEW.crop_profile_id))
  OR (EXISTS (SELECT 1 FROM crop_profile x WHERE x.crop_code = NEW.crop_code AND x.version = NEW.version))
BEGIN SELECT RAISE(ABORT, 'append-only: crop_profile trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_stage_no_replace BEFORE INSERT ON stage WHEN (EXISTS (SELECT 1 FROM stage x WHERE x.stage_id = NEW.stage_id))
  OR (EXISTS (SELECT 1 FROM stage x WHERE x.crop_profile_id = NEW.crop_profile_id AND x.seq = NEW.seq))
BEGIN SELECT RAISE(ABORT, 'append-only: stage trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_activity_type_no_replace BEFORE INSERT ON activity_type WHEN (EXISTS (SELECT 1 FROM activity_type x WHERE x.activity_type_id = NEW.activity_type_id))
  OR (EXISTS (SELECT 1 FROM activity_type x WHERE x.stage_id = NEW.stage_id AND x.code = NEW.code))
BEGIN SELECT RAISE(ABORT, 'append-only: activity_type trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_evidence_requirement_no_replace BEFORE INSERT ON evidence_requirement WHEN (EXISTS (SELECT 1 FROM evidence_requirement x WHERE x.requirement_id = NEW.requirement_id))
  OR (NEW.activity_type_id IS NOT NULL AND EXISTS (SELECT 1 FROM evidence_requirement x WHERE x.activity_type_id = NEW.activity_type_id AND x.evidence_kind = NEW.evidence_kind))
  OR (NEW.lot_event_type IS NOT NULL AND EXISTS (SELECT 1 FROM evidence_requirement x WHERE x.lot_event_type = NEW.lot_event_type AND x.evidence_kind = NEW.evidence_kind))
BEGIN SELECT RAISE(ABORT, 'append-only: evidence_requirement trùng khóa (không ghi đè)'); END;
CREATE TRIGGER trg_material_crop_rule_no_replace BEFORE INSERT ON material_crop_rule WHEN (EXISTS (SELECT 1 FROM material_crop_rule x WHERE x.material_id = NEW.material_id AND x.crop_code = NEW.crop_code))
BEGIN SELECT RAISE(ABORT, 'append-only: material_crop_rule trùng khóa (không ghi đè)'); END;