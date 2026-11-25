-- Trigger cho PostgreSQL (nạp sau schema.sql) — v0.5. SINH TỰ ĐỘNG bởi gen_triggers.py, đừng sửa tay.

CREATE FUNCTION f_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'append-only: % không cho %', TG_TABLE_NAME, TG_OP; END $$;
-- (INSERT ... ON CONFLICT DO UPDATE kích hoạt trigger UPDATE nên cũng bị chặn)
CREATE TRIGGER trg_activity_append_only BEFORE UPDATE OR DELETE ON activity FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_activity_no_truncate BEFORE TRUNCATE ON activity FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_activity_revision_append_only BEFORE UPDATE OR DELETE ON activity_revision FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_activity_revision_no_truncate BEFORE TRUNCATE ON activity_revision FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_activity_input_append_only BEFORE UPDATE OR DELETE ON activity_input FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_activity_input_no_truncate BEFORE TRUNCATE ON activity_input FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_observation_append_only BEFORE UPDATE OR DELETE ON observation FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_observation_no_truncate BEFORE TRUNCATE ON observation FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_lot_append_only BEFORE UPDATE OR DELETE ON lot FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_lot_no_truncate BEFORE TRUNCATE ON lot FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_lot_revision_append_only BEFORE UPDATE OR DELETE ON lot_revision FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_lot_revision_no_truncate BEFORE TRUNCATE ON lot_revision FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_lot_event_append_only BEFORE UPDATE OR DELETE ON lot_event FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_lot_event_no_truncate BEFORE TRUNCATE ON lot_event FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_lot_input_append_only BEFORE UPDATE OR DELETE ON lot_input FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_lot_input_no_truncate BEFORE TRUNCATE ON lot_input FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_evidence_append_only BEFORE UPDATE OR DELETE ON evidence FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_evidence_no_truncate BEFORE TRUNCATE ON evidence FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_evidence_link_append_only BEFORE UPDATE OR DELETE ON evidence_link FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_evidence_link_no_truncate BEFORE TRUNCATE ON evidence_link FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_verification_append_only BEFORE UPDATE OR DELETE ON verification FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_verification_no_truncate BEFORE TRUNCATE ON verification FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_cycle_anchor_append_only BEFORE UPDATE OR DELETE ON cycle_anchor FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_cycle_anchor_no_truncate BEFORE TRUNCATE ON cycle_anchor FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_crop_profile_append_only BEFORE UPDATE OR DELETE ON crop_profile FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_crop_profile_no_truncate BEFORE TRUNCATE ON crop_profile FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_stage_append_only BEFORE UPDATE OR DELETE ON stage FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_stage_no_truncate BEFORE TRUNCATE ON stage FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_activity_type_append_only BEFORE UPDATE OR DELETE ON activity_type FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_activity_type_no_truncate BEFORE TRUNCATE ON activity_type FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_evidence_requirement_append_only BEFORE UPDATE OR DELETE ON evidence_requirement FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_evidence_requirement_no_truncate BEFORE TRUNCATE ON evidence_requirement FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_material_crop_rule_append_only BEFORE UPDATE OR DELETE ON material_crop_rule FOR EACH ROW EXECUTE FUNCTION f_append_only();
CREATE TRIGGER trg_material_crop_rule_no_truncate BEFORE TRUNCATE ON material_crop_rule FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();

CREATE FUNCTION f_revision_seq() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_max INTEGER; v_parent TEXT := TG_ARGV[0];
BEGIN
  EXECUTE format('SELECT MAX(revision_no) FROM %I WHERE %I = $1', TG_TABLE_NAME, v_parent)
    INTO v_max USING (to_jsonb(NEW) ->> v_parent);
  IF NEW.revision_no <> COALESCE(v_max, 0) + 1 THEN
    RAISE EXCEPTION '%: revision_no phải tăng đúng 1', TG_TABLE_NAME;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_activity_revision_seq BEFORE INSERT ON activity_revision FOR EACH ROW EXECUTE FUNCTION f_revision_seq('activity_id');
CREATE TRIGGER trg_lot_revision_seq BEFORE INSERT ON lot_revision FOR EACH ROW EXECUTE FUNCTION f_revision_seq('lot_id');
CREATE TRIGGER trg_cycle_anchor_seq BEFORE INSERT ON cycle_anchor FOR EACH ROW EXECUTE FUNCTION f_revision_seq('cycle_id');

CREATE FUNCTION f_cycle_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'cultivation_cycle: không cho DELETE'; END IF;
  IF (NEW.cycle_id, NEW.plot_id, NEW.crop_profile_id, NEW.variety_id, NEW.season_id, NEW.started_at, NEW.created_by, NEW.created_at)
     IS DISTINCT FROM (OLD.cycle_id, OLD.plot_id, OLD.crop_profile_id, OLD.variety_id, OLD.season_id, OLD.started_at, OLD.created_by, OLD.created_at) THEN
    RAISE EXCEPTION 'cultivation_cycle: chỉ được cập nhật closed_at; mốc lịch sửa qua cycle_anchor';
  END IF;
  IF NEW.closed_at IS DISTINCT FROM OLD.closed_at THEN
    IF OLD.closed_at IS NOT NULL THEN RAISE EXCEPTION 'cultivation_cycle: chu kỳ đã đóng, không đổi hoặc mở lại closed_at'; END IF;
    IF EXISTS (SELECT 1 FROM activity a JOIN activity_revision r ON r.activity_id = a.activity_id
               WHERE a.cycle_id = OLD.cycle_id AND r.performed_at::date > NEW.closed_at) THEN
      RAISE EXCEPTION 'cultivation_cycle: closed_at trước ngày hoạt động cuối của chu kỳ';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_cycle_guard BEFORE UPDATE OR DELETE ON cultivation_cycle FOR EACH ROW EXECUTE FUNCTION f_cycle_guard();

CREATE FUNCTION f_plot_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'plot: không cho DELETE'; END IF;
  IF (NEW.plot_id, NEW.farm_id, NEW.code, NEW.created_by, NEW.created_at)
     IS DISTINCT FROM (OLD.plot_id, OLD.farm_id, OLD.code, OLD.created_by, OLD.created_at) THEN
    RAISE EXCEPTION 'plot: không đổi định danh, hộ sở hữu hoặc mã lô đất';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_plot_guard BEFORE UPDATE OR DELETE ON plot FOR EACH ROW EXECUTE FUNCTION f_plot_guard();
CREATE FUNCTION f_farm_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'farm: không cho DELETE'; END IF;
  IF (NEW.farm_id, NEW.owner_agent_id, NEW.created_by, NEW.created_at)
     IS DISTINCT FROM (OLD.farm_id, OLD.owner_agent_id, OLD.created_by, OLD.created_at) THEN
    RAISE EXCEPTION 'farm: không đổi định danh hoặc chủ hộ';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_farm_guard BEFORE UPDATE OR DELETE ON farm FOR EACH ROW EXECUTE FUNCTION f_farm_guard();

CREATE FUNCTION f_lot_event_output_type() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.output_lot_id IS NOT NULL AND (SELECT lot_type FROM lot WHERE lot_id = NEW.output_lot_id) IS DISTINCT FROM
     (CASE NEW.event_type WHEN 'aggregation' THEN 'aggregated' WHEN 'transformation' THEN 'processed' WHEN 'packaging' THEN 'packaged' END) THEN
    RAISE EXCEPTION 'lot_event: loại lô đầu ra không khớp loại sự kiện';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_lot_event_output_type BEFORE INSERT ON lot_event FOR EACH ROW EXECUTE FUNCTION f_lot_event_output_type();

CREATE FUNCTION f_lot_input_check() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_type TEXT; v_out TEXT;
BEGIN
  SELECT event_type, output_lot_id INTO v_type, v_out FROM lot_event WHERE event_id = NEW.event_id;
  IF v_type IN ('purchase','transport') THEN
    RAISE EXCEPTION 'lot_input: mốc thu mua/vận chuyển không có đầu vào';
  END IF;
  IF EXISTS (
    WITH RECURSIVE up(x) AS (
      SELECT NEW.input_lot_id
      UNION
      SELECT li.input_lot_id FROM lot_input li
      JOIN lot_event ev ON ev.event_id = li.event_id
      JOIN up ON ev.output_lot_id = up.x)
    SELECT 1 FROM up WHERE x = v_out) THEN
    RAISE EXCEPTION 'lot_input: tạo vòng trong đồ thị lô';
  END IF;
  IF EXISTS (SELECT 1 FROM lot_input li WHERE li.input_lot_id = v_out) THEN
    RAISE EXCEPTION 'lot_input: lô đầu ra đã được dùng tiếp, không thêm đầu vào hồi tố';
  END IF;
  IF EXISTS (SELECT 1 FROM verification v WHERE v.lot_event_id = NEW.event_id) THEN
    RAISE EXCEPTION 'lot_input: sự kiện đã được xác minh, không thêm đầu vào';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_lot_input_check BEFORE INSERT ON lot_input FOR EACH ROW EXECUTE FUNCTION f_lot_input_check();

CREATE FUNCTION f_lot_harvest_check() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.harvest_activity_id IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM activity a JOIN activity_type t ON t.activity_type_id = a.activity_type_id
       WHERE a.activity_id = NEW.harvest_activity_id AND t.produces_lot = 1) THEN
    RAISE EXCEPTION 'lot: hoạt động sinh lô phải là loại thu hoạch (produces_lot = 1)';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_lot_harvest_check BEFORE INSERT ON lot FOR EACH ROW EXECUTE FUNCTION f_lot_harvest_check();

CREATE FUNCTION f_verification_check() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (NEW.activity_revision_id IS NOT NULL AND EXISTS (SELECT 1 FROM activity_revision r
        WHERE r.revision_id = NEW.activity_revision_id AND NEW.verifier_id IN (r.performed_by, r.recorded_by)))
  OR (NEW.lot_event_id IS NOT NULL AND EXISTS (SELECT 1 FROM lot_event e
        WHERE e.event_id = NEW.lot_event_id AND NEW.verifier_id IN (e.performed_by, e.recorded_by)))
  OR (NEW.lot_revision_id IS NOT NULL AND EXISTS (SELECT 1 FROM lot_revision r
        WHERE r.lot_revision_id = NEW.lot_revision_id AND NEW.verifier_id = r.recorded_by)) THEN
    RAISE EXCEPTION 'verification: người xác minh trùng người làm/người ghi';
  END IF;
  IF NEW.supersedes_verification_id IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM verification v WHERE v.verification_id = NEW.supersedes_verification_id
         AND v.activity_revision_id IS NOT DISTINCT FROM NEW.activity_revision_id
         AND v.lot_revision_id      IS NOT DISTINCT FROM NEW.lot_revision_id
         AND v.lot_event_id         IS NOT DISTINCT FROM NEW.lot_event_id) THEN
    RAISE EXCEPTION 'verification: chỉ được thay thế xác minh của cùng đối tượng';
  END IF;
  IF EXISTS (SELECT 1 FROM verification v
             WHERE v.activity_revision_id IS NOT DISTINCT FROM NEW.activity_revision_id
               AND v.lot_revision_id      IS NOT DISTINCT FROM NEW.lot_revision_id
               AND v.lot_event_id         IS NOT DISTINCT FROM NEW.lot_event_id
               AND NOT EXISTS (SELECT 1 FROM verification v2 WHERE v2.supersedes_verification_id = v.verification_id)
               AND (NEW.supersedes_verification_id IS NULL OR NEW.supersedes_verification_id <> v.verification_id)) THEN
    RAISE EXCEPTION 'verification: đã có kết luận hiệu lực, lần mới phải thay thế nó';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_verification_check BEFORE INSERT ON verification FOR EACH ROW EXECUTE FUNCTION f_verification_check();
