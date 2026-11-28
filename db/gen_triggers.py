"""Sinh triggers_sqlite.sql và triggers_postgres.sql (v0.5) từ một nguồn để hai hệ không lệch nhau.
Chạy: python3 gen_triggers.py
"""
import pathlib

HERE = pathlib.Path(__file__).parent

# Bảng chỉ ghi thêm: khóa chính và các khóa duy nhất (để chặn INSERT OR REPLACE của SQLite).
# Mỗi khóa: (danh sách cột, cột bắt buộc khác NULL để khóa có hiệu lực — cho UNIQUE một phần)
APPEND_ONLY = {
    "activity":          [(["activity_id"], None), (["source_channel", "external_ref"], "external_ref")],
    "activity_revision": [(["revision_id"], None), (["activity_id", "revision_no"], None)],
    "activity_input":    [(["revision_id", "material_id"], None)],
    "observation":       [(["observation_id"], None), (["source_channel", "external_ref"], "external_ref")],
    "lot":               [(["lot_id"], None), (["public_code"], None), (["harvest_activity_id"], "harvest_activity_id"),
                          (["source_channel", "external_ref"], "external_ref")],
    "lot_revision":      [(["lot_revision_id"], None), (["lot_id", "revision_no"], None)],
    "lot_event":         [(["event_id"], None), (["output_lot_id"], "output_lot_id"),
                          (["source_channel", "external_ref"], "external_ref")],
    "lot_input":         [(["event_id", "input_lot_id"], None)],
    "evidence":          [(["evidence_id"], None), (["source_channel", "external_ref"], "external_ref")],
    "evidence_link":     [(["link_id"], None)] + [(["evidence_id", c], c) for c in
                          ("activity_revision_id", "lot_revision_id", "lot_event_id", "plot_id", "certification_id")],
    "verification":      [(["verification_id"], None), (["supersedes_verification_id"], "supersedes_verification_id")],
    "cycle_anchor":      [(["cycle_anchor_id"], None), (["cycle_id", "revision_no"], None)],
    # cấu hình: đổi quy trình = phiên bản crop_profile mới, không sửa đè
    "crop_profile":      [(["crop_profile_id"], None), (["crop_code", "version"], None)],
    "stage":             [(["stage_id"], None), (["crop_profile_id", "seq"], None)],
    "activity_type":     [(["activity_type_id"], None), (["stage_id", "code"], None)],
    "evidence_requirement": [(["requirement_id"], None), (["activity_type_id", "evidence_kind"], "activity_type_id"),
                             (["lot_event_type", "evidence_kind"], "lot_event_type")],
    "material_crop_rule": [(["material_id", "crop_code"], None)],
}
REVISIONED = {"activity_revision": "activity_id", "lot_revision": "lot_id", "cycle_anchor": "cycle_id"}
OUTPUT_TYPE = "CASE NEW.event_type WHEN 'aggregation' THEN 'aggregated' WHEN 'transformation' THEN 'processed' WHEN 'packaging' THEN 'packaged' END"

# ============================== SQLite ==============================
L = ["-- Trigger cho SQLite (nạp sau schema.sql) — v0.5.1. SINH TỰ ĐỘNG bởi gen_triggers.py, đừng sửa tay.", "",
     "-- T1 · Chỉ ghi thêm: chặn UPDATE/DELETE (chặn INSERT OR REPLACE: xem T0 ở cuối file)"]
REPLACE_GUARDS = []
for t, keys in APPEND_ONLY.items():
    L.append(f"CREATE TRIGGER trg_{t}_no_update BEFORE UPDATE ON {t} BEGIN SELECT RAISE(ABORT, 'append-only: {t} không cho UPDATE'); END;")
    L.append(f"CREATE TRIGGER trg_{t}_no_delete BEFORE DELETE ON {t} BEGIN SELECT RAISE(ABORT, 'append-only: {t} không cho DELETE'); END;")
    conds = []
    for cols, notnull in keys:
        m = " AND ".join(f"x.{c} = NEW.{c}" for c in cols)
        conds.append((f"(NEW.{notnull} IS NOT NULL AND " if notnull else "(") + f"EXISTS (SELECT 1 FROM {t} x WHERE {m}))")
    REPLACE_GUARDS.append(f"CREATE TRIGGER trg_{t}_no_replace BEFORE INSERT ON {t} WHEN " + "\n  OR ".join(conds) +
             f"\nBEGIN SELECT RAISE(ABORT, 'append-only: {t} trùng khóa (không ghi đè)'); END;")
L.append("\n-- T1b · Số bản ghi tăng đúng 1 (không nhảy cóc)")
for t, parent in REVISIONED.items():
    L.append(f"""CREATE TRIGGER trg_{t}_seq BEFORE INSERT ON {t}
WHEN NEW.revision_no <> COALESCE((SELECT MAX(revision_no) FROM {t} WHERE {parent} = NEW.{parent}), 0) + 1
BEGIN SELECT RAISE(ABORT, '{t}: revision_no phải tăng đúng 1'); END;""")
L.append("""
-- T1c · Chu kỳ canh tác: chỉ được đóng (closed_at NULL → ngày) một lần, không trước hoạt động cuối; không xóa
CREATE TRIGGER trg_cycle_guard_update BEFORE UPDATE OF cycle_id, plot_id, crop_profile_id, variety_id, season_id, started_at, created_by, created_at ON cultivation_cycle
BEGIN SELECT RAISE(ABORT, 'cultivation_cycle: chỉ được cập nhật closed_at; mốc lịch sửa qua cycle_anchor'); END;
CREATE TRIGGER trg_cycle_close BEFORE UPDATE OF closed_at ON cultivation_cycle
BEGIN
  SELECT RAISE(ABORT, 'cultivation_cycle: chu kỳ đã đóng, không đổi hoặc mở lại closed_at') WHERE OLD.closed_at IS NOT NULL;
  SELECT RAISE(ABORT, 'cultivation_cycle: closed_at không được NULL') WHERE NEW.closed_at IS NULL;
  SELECT RAISE(ABORT, 'cultivation_cycle: closed_at trước ngày hoạt động cuối của chu kỳ')
  WHERE EXISTS (SELECT 1 FROM activity a JOIN v_activity_current r ON r.activity_id = a.activity_id
                WHERE a.cycle_id = OLD.cycle_id AND date(r.performed_at) > NEW.closed_at);
END;
-- (v0.5.1, RV4) chỉ xét bản ghi HIỆN HÀNH: bản cũ đã sửa không chặn việc đóng

-- T1c' · Chu kỳ đã đóng không nhận bản ghi có ngày làm sau closed_at (v0.5.1, RV3). Ghi muộn việc làm trước ngày đóng vẫn được.
CREATE TRIGGER trg_activity_revision_closed_cycle BEFORE INSERT ON activity_revision
WHEN EXISTS (SELECT 1 FROM activity a JOIN cultivation_cycle c ON c.cycle_id = a.cycle_id
             WHERE a.activity_id = NEW.activity_id AND c.closed_at IS NOT NULL AND date(NEW.performed_at) > c.closed_at)
BEGIN SELECT RAISE(ABORT, 'activity_revision: chu kỳ đã đóng, ngày làm sau closed_at'); END;
CREATE TRIGGER trg_cycle_no_delete BEFORE DELETE ON cultivation_cycle
BEGIN SELECT RAISE(ABORT, 'cultivation_cycle: không cho DELETE'); END;

-- T1d · Lô đất và nông hộ: không đổi chủ / chuyển lô đất sang hộ khác / đổi mã; không xóa
CREATE TRIGGER trg_plot_guard BEFORE UPDATE OF plot_id, farm_id, code, created_by, created_at ON plot
BEGIN SELECT RAISE(ABORT, 'plot: không đổi định danh, hộ sở hữu hoặc mã lô đất'); END;
CREATE TRIGGER trg_plot_no_delete BEFORE DELETE ON plot BEGIN SELECT RAISE(ABORT, 'plot: không cho DELETE'); END;
CREATE TRIGGER trg_farm_guard BEFORE UPDATE OF farm_id, owner_agent_id, created_by, created_at ON farm
BEGIN SELECT RAISE(ABORT, 'farm: không đổi định danh hoặc chủ hộ'); END;
CREATE TRIGGER trg_farm_no_delete BEFORE DELETE ON farm BEGIN SELECT RAISE(ABORT, 'farm: không cho DELETE'); END;
-- (v0.5.1, RV12) thông tin hiện trên trang QR bị khóa khi lô đất đã sinh lô thu hoạch; trước đó vẫn sửa được
CREATE TRIGGER trg_plot_public_lock BEFORE UPDATE OF area_m2, growing_area_code, geo_point ON plot
WHEN EXISTS (SELECT 1 FROM cultivation_cycle c JOIN activity a ON a.cycle_id = c.cycle_id JOIN lot l ON l.harvest_activity_id = a.activity_id WHERE c.plot_id = OLD.plot_id)
BEGIN SELECT RAISE(ABORT, 'plot: lô đất đã sinh lô thu hoạch, không sửa thông tin hiển thị trên QR'); END;
CREATE TRIGGER trg_farm_public_lock BEFORE UPDATE OF name, province, commune, address_detail ON farm
WHEN EXISTS (SELECT 1 FROM plot p JOIN cultivation_cycle c ON c.plot_id = p.plot_id JOIN activity a ON a.cycle_id = c.cycle_id JOIN lot l ON l.harvest_activity_id = a.activity_id WHERE p.farm_id = OLD.farm_id)
BEGIN SELECT RAISE(ABORT, 'farm: hộ đã có lô thu hoạch, không sửa thông tin hiển thị trên QR'); END;

-- T1e · Cấu hình đang dùng: crop profile đã có chu kỳ thì không thêm giai đoạn / loại hoạt động / yêu cầu minh chứng
-- (đổi quy trình = phiên bản crop profile mới; v0.5.1, RV1, RV2)
CREATE TRIGGER trg_stage_profile_in_use BEFORE INSERT ON stage
WHEN EXISTS (SELECT 1 FROM cultivation_cycle c WHERE c.crop_profile_id = NEW.crop_profile_id)
BEGIN SELECT RAISE(ABORT, 'cấu hình: crop profile đã có chu kỳ sử dụng, tạo phiên bản mới'); END;
CREATE TRIGGER trg_activity_type_profile_in_use BEFORE INSERT ON activity_type
WHEN EXISTS (SELECT 1 FROM stage s JOIN cultivation_cycle c ON c.crop_profile_id = s.crop_profile_id WHERE s.stage_id = NEW.stage_id)
BEGIN SELECT RAISE(ABORT, 'cấu hình: crop profile đã có chu kỳ sử dụng, tạo phiên bản mới'); END;
CREATE TRIGGER trg_evidence_requirement_profile_in_use BEFORE INSERT ON evidence_requirement
WHEN NEW.activity_type_id IS NOT NULL AND EXISTS (SELECT 1 FROM activity_type t JOIN stage s ON s.stage_id = t.stage_id
     JOIN cultivation_cycle c ON c.crop_profile_id = s.crop_profile_id WHERE t.activity_type_id = NEW.activity_type_id)
BEGIN SELECT RAISE(ABORT, 'cấu hình: crop profile đã có chu kỳ sử dụng, tạo phiên bản mới'); END;

-- T2 · Sự kiện lô: loại lô đầu ra phải khớp loại sự kiện
CREATE TRIGGER trg_lot_event_output_type BEFORE INSERT ON lot_event
WHEN NEW.output_lot_id IS NOT NULL
BEGIN
  SELECT RAISE(ABORT, 'lot_event: loại lô đầu ra không khớp loại sự kiện')
  WHERE (SELECT lot_type FROM lot WHERE lot_id = NEW.output_lot_id) IS NOT """ + OUTPUT_TYPE + """;
END;

-- T3 · Cạnh lô: không cho mốc; không tạo vòng; không thêm đầu vào khi lô ra đã được dùng tiếp hoặc kết luận hiệu lực là 'verified'.
--      Đầu vào ghi cùng ngày ghi sự kiện; bổ sung sau đó chỉ khi kết luận hiệu lực là 'rejected'
--      (luồng từ chối → bổ sung → xác minh lại; lý do nằm ở ghi chú từ chối + supersede_reason) — v0.5.1, RV6, RV7
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
  WHERE EXISTS (SELECT 1 FROM v_verification_effective v WHERE v.lot_event_id = NEW.event_id AND v.result = 'verified');
  SELECT RAISE(ABORT, 'lot_input: ghi bổ sung sau ngày ghi sự kiện chỉ được khi sự kiện đang bị từ chối')
  WHERE date(NEW.recorded_at) > (SELECT date(e.recorded_at) FROM lot_event e WHERE e.event_id = NEW.event_id)
    AND NOT EXISTS (SELECT 1 FROM v_verification_effective v WHERE v.lot_event_id = NEW.event_id AND v.result = 'rejected');
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
""")
L.append("-- T0 · Chặn INSERT OR REPLACE: REPLACE xóa dòng cũ mà KHÔNG chạy trigger DELETE (recursive_triggers tắt).\n"
         "-- Đặt cuối file vì SQLite chạy trigger tạo sau trước → báo đúng lý do 'trùng khóa'.")
L += REPLACE_GUARDS
(HERE / "triggers_sqlite.sql").write_text("\n".join(L), encoding="utf-8")

# ============================== PostgreSQL ==============================
P = ["-- Trigger cho PostgreSQL (nạp sau schema.sql) — v0.5.1. SINH TỰ ĐỘNG bởi gen_triggers.py, đừng sửa tay.", "",
"""CREATE FUNCTION f_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'append-only: % không cho %', TG_TABLE_NAME, TG_OP; END $$;
-- (INSERT ... ON CONFLICT DO UPDATE kích hoạt trigger UPDATE nên cũng bị chặn)"""]
for t in APPEND_ONLY:
    P.append(f"CREATE TRIGGER trg_{t}_append_only BEFORE UPDATE OR DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION f_append_only();")
    P.append(f"CREATE TRIGGER trg_{t}_no_truncate BEFORE TRUNCATE ON {t} FOR EACH STATEMENT EXECUTE FUNCTION f_append_only();")
P.append("""
CREATE FUNCTION f_revision_seq() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_max INTEGER; v_parent TEXT := TG_ARGV[0];
BEGIN
  EXECUTE format('SELECT MAX(revision_no) FROM %I WHERE %I = $1', TG_TABLE_NAME, v_parent)
    INTO v_max USING (to_jsonb(NEW) ->> v_parent);
  IF NEW.revision_no <> COALESCE(v_max, 0) + 1 THEN
    RAISE EXCEPTION '%: revision_no phải tăng đúng 1', TG_TABLE_NAME;
  END IF;
  RETURN NEW;
END $$;""")
for t, parent in REVISIONED.items():
    P.append(f"CREATE TRIGGER trg_{t}_seq BEFORE INSERT ON {t} FOR EACH ROW EXECUTE FUNCTION f_revision_seq('{parent}');")
P.append("""
CREATE FUNCTION f_cycle_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'cultivation_cycle: không cho DELETE'; END IF;
  IF (NEW.cycle_id, NEW.plot_id, NEW.crop_profile_id, NEW.variety_id, NEW.season_id, NEW.started_at, NEW.created_by, NEW.created_at)
     IS DISTINCT FROM (OLD.cycle_id, OLD.plot_id, OLD.crop_profile_id, OLD.variety_id, OLD.season_id, OLD.started_at, OLD.created_by, OLD.created_at) THEN
    RAISE EXCEPTION 'cultivation_cycle: chỉ được cập nhật closed_at; mốc lịch sửa qua cycle_anchor';
  END IF;
  IF NEW.closed_at IS DISTINCT FROM OLD.closed_at THEN
    IF OLD.closed_at IS NOT NULL THEN RAISE EXCEPTION 'cultivation_cycle: chu kỳ đã đóng, không đổi hoặc mở lại closed_at'; END IF;
    IF EXISTS (SELECT 1 FROM activity a JOIN v_activity_current r ON r.activity_id = a.activity_id
               WHERE a.cycle_id = OLD.cycle_id AND r.performed_at::date > NEW.closed_at) THEN
      RAISE EXCEPTION 'cultivation_cycle: closed_at trước ngày hoạt động cuối của chu kỳ';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_cycle_guard BEFORE UPDATE OR DELETE ON cultivation_cycle FOR EACH ROW EXECUTE FUNCTION f_cycle_guard();

CREATE FUNCTION f_activity_revision_closed_cycle() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM activity a JOIN cultivation_cycle c ON c.cycle_id = a.cycle_id
             WHERE a.activity_id = NEW.activity_id AND c.closed_at IS NOT NULL AND NEW.performed_at::date > c.closed_at) THEN
    RAISE EXCEPTION 'activity_revision: chu kỳ đã đóng, ngày làm sau closed_at';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_activity_revision_closed_cycle BEFORE INSERT ON activity_revision FOR EACH ROW EXECUTE FUNCTION f_activity_revision_closed_cycle();

CREATE FUNCTION f_config_in_use() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_profile TEXT;
BEGIN
  IF TG_TABLE_NAME = 'stage' THEN
    v_profile := NEW.crop_profile_id;
  ELSIF TG_TABLE_NAME = 'activity_type' THEN
    SELECT s.crop_profile_id INTO v_profile FROM stage s WHERE s.stage_id = NEW.stage_id;
  ELSIF NEW.activity_type_id IS NOT NULL THEN
    SELECT s.crop_profile_id INTO v_profile FROM activity_type t JOIN stage s ON s.stage_id = t.stage_id
    WHERE t.activity_type_id = NEW.activity_type_id;
  END IF;
  IF v_profile IS NOT NULL AND EXISTS (SELECT 1 FROM cultivation_cycle c WHERE c.crop_profile_id = v_profile) THEN
    RAISE EXCEPTION 'cấu hình: crop profile đã có chu kỳ sử dụng, tạo phiên bản mới';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_stage_profile_in_use BEFORE INSERT ON stage FOR EACH ROW EXECUTE FUNCTION f_config_in_use();
CREATE TRIGGER trg_activity_type_profile_in_use BEFORE INSERT ON activity_type FOR EACH ROW EXECUTE FUNCTION f_config_in_use();
CREATE TRIGGER trg_evidence_requirement_profile_in_use BEFORE INSERT ON evidence_requirement FOR EACH ROW EXECUTE FUNCTION f_config_in_use();

CREATE FUNCTION f_plot_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'plot: không cho DELETE'; END IF;
  IF (NEW.plot_id, NEW.farm_id, NEW.code, NEW.created_by, NEW.created_at)
     IS DISTINCT FROM (OLD.plot_id, OLD.farm_id, OLD.code, OLD.created_by, OLD.created_at) THEN
    RAISE EXCEPTION 'plot: không đổi định danh, hộ sở hữu hoặc mã lô đất';
  END IF;
  IF (NEW.area_m2, NEW.growing_area_code, NEW.geo_point) IS DISTINCT FROM (OLD.area_m2, OLD.growing_area_code, OLD.geo_point)
     AND EXISTS (SELECT 1 FROM cultivation_cycle c JOIN activity a ON a.cycle_id = c.cycle_id JOIN lot l ON l.harvest_activity_id = a.activity_id WHERE c.plot_id = OLD.plot_id) THEN
    RAISE EXCEPTION 'plot: lô đất đã sinh lô thu hoạch, không sửa thông tin hiển thị trên QR';
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
  IF (NEW.name, NEW.province, NEW.commune, NEW.address_detail) IS DISTINCT FROM (OLD.name, OLD.province, OLD.commune, OLD.address_detail)
     AND EXISTS (SELECT 1 FROM plot p JOIN cultivation_cycle c ON c.plot_id = p.plot_id JOIN activity a ON a.cycle_id = c.cycle_id JOIN lot l ON l.harvest_activity_id = a.activity_id WHERE p.farm_id = OLD.farm_id) THEN
    RAISE EXCEPTION 'farm: hộ đã có lô thu hoạch, không sửa thông tin hiển thị trên QR';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_farm_guard BEFORE UPDATE OR DELETE ON farm FOR EACH ROW EXECUTE FUNCTION f_farm_guard();

CREATE FUNCTION f_lot_event_output_type() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.output_lot_id IS NOT NULL AND (SELECT lot_type FROM lot WHERE lot_id = NEW.output_lot_id) IS DISTINCT FROM
     (""" + OUTPUT_TYPE + """) THEN
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
  IF EXISTS (SELECT 1 FROM v_verification_effective v WHERE v.lot_event_id = NEW.event_id AND v.result = 'verified') THEN
    RAISE EXCEPTION 'lot_input: sự kiện đã được xác minh, không thêm đầu vào';
  END IF;
  IF NEW.recorded_at::date > (SELECT e.recorded_at::date FROM lot_event e WHERE e.event_id = NEW.event_id)
     AND NOT EXISTS (SELECT 1 FROM v_verification_effective v WHERE v.lot_event_id = NEW.event_id AND v.result = 'rejected') THEN
    RAISE EXCEPTION 'lot_input: ghi bổ sung sau ngày ghi sự kiện chỉ được khi sự kiện đang bị từ chối';
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
""")
(HERE / "triggers_postgres.sql").write_text("\n".join(P), encoding="utf-8")
print("triggers ok")
