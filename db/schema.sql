-- =====================================================================
-- Traceability Core — canonical schema v0.5 (25/11/2026)
-- Đề tài #6 · ĐACN · chuỗi mè → dầu mè, mở rộng được sang cây khác
--
-- File này: bảng, ràng buộc, index, view dùng chung (SQL chuẩn, chạy trên PostgreSQL và SQLite).
-- Nạp kèm theo hệ CSDL:
--   SQLite     : schema.sql → triggers_sqlite.sql   → views_sqlite.sql
--   PostgreSQL : schema.sql → triggers_postgres.sql → views_postgres.sql
-- (trigger và các view có phép tính ngày khác cú pháp giữa hai hệ)
--
-- Quy ước:
--   [APPEND-ONLY]  trigger chặn UPDATE/DELETE; sửa = thêm bản mới có lý do.
--   Thời gian      lưu UTC, ISO-8601; time_precision cho biết độ chính xác.
--                  So sánh hai mốc: nếu một bên có độ chính xác 'day' thì so ở mức ngày.
--   SQLite         mỗi kết nối phải chạy PRAGMA foreign_keys = ON.
-- =====================================================================

-- ---------------------------------------------------------------------
-- CỤM 0 · Agent và địa điểm
-- ---------------------------------------------------------------------
CREATE TABLE agent (
  agent_id        TEXT PRIMARY KEY,
  kind            TEXT NOT NULL CHECK (kind IN ('person','organization','software','device')),
  name            TEXT NOT NULL,
  role            TEXT NOT NULL CHECK (role IN ('farmer','technician','company','verifier','processor','certifier','system')),
  organization_id TEXT REFERENCES agent(agent_id),
  created_at      TIMESTAMP NOT NULL
);

CREATE TABLE facility (
  facility_id     TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  kind            TEXT NOT NULL CHECK (kind IN ('collection_point','processing_plant','warehouse','farm_site','other')),
  operator_id     TEXT NOT NULL REFERENCES agent(agent_id),
  province        TEXT NOT NULL,
  commune         TEXT NOT NULL,
  address_detail  TEXT                                    -- không công khai
);

-- ---------------------------------------------------------------------
-- CỤM 1 · Cấu hình theo cây — dữ liệu, không phải bảng
-- Mỗi luật có nguồn (rule_source) và cờ "giả định của nhóm" (is_assumption)
-- ---------------------------------------------------------------------
CREATE TABLE crop_profile (
  crop_profile_id          TEXT PRIMARY KEY,
  crop_code                TEXT NOT NULL,
  name                     TEXT NOT NULL,
  version                  INTEGER NOT NULL,
  anchor_event             TEXT NOT NULL,
  variety_attribute_schema TEXT,
  source_document          TEXT,
  valid_from               DATE NOT NULL,
  UNIQUE (crop_code, version)
);

CREATE TABLE variety (
  variety_id      TEXT PRIMARY KEY,
  crop_code       TEXT NOT NULL,
  name            TEXT NOT NULL,
  attributes      TEXT,
  source_note     TEXT
);

CREATE TABLE stage (
  stage_id        TEXT PRIMARY KEY,
  crop_profile_id TEXT NOT NULL REFERENCES crop_profile(crop_profile_id),
  seq             INTEGER NOT NULL,
  name            TEXT NOT NULL,
  UNIQUE (crop_profile_id, seq)
);

CREATE TABLE activity_type (
  activity_type_id TEXT PRIMARY KEY,
  stage_id         TEXT NOT NULL REFERENCES stage(stage_id),
  code             TEXT NOT NULL,
  name             TEXT NOT NULL,
  requirement      TEXT NOT NULL CHECK (requirement IN ('mandatory','conditional','optional')),
  offset_days      INTEGER,
  tolerance_days   INTEGER NOT NULL DEFAULT 0 CHECK (tolerance_days >= 0),
  produces_lot     INTEGER NOT NULL DEFAULT 0 CHECK (produces_lot IN (0,1)),
  uses_inputs      INTEGER NOT NULL DEFAULT 0 CHECK (uses_inputs IN (0,1)),
  attribute_schema TEXT,
  public_level     TEXT NOT NULL DEFAULT 'summary' CHECK (public_level IN ('detail','summary','private')),
  rule_source      TEXT,
  is_assumption    INTEGER NOT NULL DEFAULT 0 CHECK (is_assumption IN (0,1)),
  UNIQUE (stage_id, code),
  CHECK (requirement <> 'mandatory' OR offset_days IS NOT NULL)
);

-- Yêu cầu minh chứng: cho một loại hoạt động HOẶC một loại sự kiện lô
CREATE TABLE evidence_requirement (
  requirement_id   TEXT PRIMARY KEY,
  activity_type_id TEXT REFERENCES activity_type(activity_type_id),
  lot_event_type   TEXT CHECK (lot_event_type IN ('aggregation','transformation','packaging','purchase','transport')),
  evidence_kind    TEXT NOT NULL CHECK (evidence_kind IN ('photo','document','sensor','lab_report','signature','weighing_slip')),
  min_count        INTEGER NOT NULL DEFAULT 1 CHECK (min_count >= 1),
  rule_source      TEXT,
  is_assumption    INTEGER NOT NULL DEFAULT 0 CHECK (is_assumption IN (0,1)),
  CHECK ((CASE WHEN activity_type_id IS NOT NULL THEN 1 ELSE 0 END)
       + (CASE WHEN lot_event_type   IS NOT NULL THEN 1 ELSE 0 END) = 1)
);
CREATE UNIQUE INDEX uq_evreq_activity ON evidence_requirement(activity_type_id, evidence_kind) WHERE activity_type_id IS NOT NULL;
CREATE UNIQUE INDEX uq_evreq_event    ON evidence_requirement(lot_event_type, evidence_kind)   WHERE lot_event_type IS NOT NULL;

CREATE TABLE input_material (
  material_id       TEXT PRIMARY KEY,
  kind              TEXT NOT NULL CHECK (kind IN ('fertilizer','pesticide','seed','other')),
  trade_name        TEXT NOT NULL,
  active_ingredient TEXT,
  registration_no   TEXT,
  default_unit      TEXT NOT NULL CHECK (default_unit IN ('kg','g','l','ml','unit','m3'))
);

-- Thời gian cách ly theo (vật tư, cây trồng) — nhãn thuốc ghi theo từng cây
CREATE TABLE material_crop_rule (
  material_id     TEXT NOT NULL REFERENCES input_material(material_id),
  crop_code       TEXT NOT NULL,
  phi_days        INTEGER NOT NULL CHECK (phi_days >= 0),
  rule_source     TEXT NOT NULL,                          -- nhãn thuốc / văn bản; hoặc 'giả định nhóm'
  is_assumption   INTEGER NOT NULL DEFAULT 0 CHECK (is_assumption IN (0,1)),
  PRIMARY KEY (material_id, crop_code)
);

-- ---------------------------------------------------------------------
-- CỤM 2 · Canh tác
-- ---------------------------------------------------------------------
CREATE TABLE farm (
  farm_id         TEXT PRIMARY KEY,
  owner_agent_id  TEXT NOT NULL REFERENCES agent(agent_id),
  name            TEXT NOT NULL,
  province        TEXT NOT NULL,
  commune         TEXT NOT NULL,
  address_detail  TEXT,
  created_by      TEXT NOT NULL REFERENCES agent(agent_id),
  created_at      TIMESTAMP NOT NULL
);

CREATE TABLE plot (
  plot_id           TEXT PRIMARY KEY,
  farm_id           TEXT NOT NULL REFERENCES farm(farm_id),
  code              TEXT NOT NULL,
  area_m2           NUMERIC NOT NULL CHECK (area_m2 > 0),
  growing_area_code TEXT,
  geo_point         TEXT,
  created_by        TEXT NOT NULL REFERENCES agent(agent_id),
  created_at        TIMESTAMP NOT NULL,
  UNIQUE (farm_id, code)
);

-- Vụ (season): chương trình canh tác của một tổ chức trong một khoảng thời gian, vd "Đông Xuân 2026–2027" của F&S.
-- Chu kỳ canh tác tham chiếu vụ; cây lâu năm có thể không thuộc vụ nào (season_id NULL).
CREATE TABLE season (
  season_id        TEXT PRIMARY KEY,
  organization_id  TEXT NOT NULL REFERENCES agent(agent_id),
  name             TEXT NOT NULL,
  crop_code        TEXT,
  starts_on        DATE NOT NULL,
  ends_on          DATE NOT NULL,
  created_by       TEXT NOT NULL REFERENCES agent(agent_id),
  created_at       TIMESTAMP NOT NULL,
  UNIQUE (organization_id, name),
  CHECK (ends_on >= starts_on)
);

CREATE TABLE cultivation_cycle (
  cycle_id        TEXT PRIMARY KEY,
  plot_id         TEXT NOT NULL REFERENCES plot(plot_id),
  crop_profile_id TEXT NOT NULL REFERENCES crop_profile(crop_profile_id),
  variety_id      TEXT REFERENCES variety(variety_id),
  season_id       TEXT REFERENCES season(season_id),
  started_at      DATE NOT NULL,
  closed_at       DATE,                                   -- chỉ trường này được UPDATE (trigger chặn các trường khác)
  created_by      TEXT NOT NULL REFERENCES agent(agent_id),
  created_at      TIMESTAMP NOT NULL,
  CHECK (closed_at IS NULL OR closed_at >= started_at)
);
CREATE INDEX ix_cycle_season ON cultivation_cycle(season_id);

-- Mốc tính lịch (vd ngày gieo) có LỊCH SỬ: sửa = bản mới có lý do. Chưa có bản nào → lịch "không xác định".
CREATE TABLE cycle_anchor (                               -- [APPEND-ONLY]
  cycle_anchor_id TEXT PRIMARY KEY,
  cycle_id        TEXT NOT NULL REFERENCES cultivation_cycle(cycle_id),
  revision_no     INTEGER NOT NULL CHECK (revision_no >= 1),
  anchor_date     DATE NOT NULL,
  recorded_by     TEXT NOT NULL REFERENCES agent(agent_id),
  recorded_at     TIMESTAMP NOT NULL,
  reason          TEXT,
  UNIQUE (cycle_id, revision_no),
  CHECK (revision_no = 1 OR reason IS NOT NULL)
);

CREATE TABLE activity (                                   -- [APPEND-ONLY]
  activity_id      TEXT PRIMARY KEY,
  cycle_id         TEXT NOT NULL REFERENCES cultivation_cycle(cycle_id),
  activity_type_id TEXT NOT NULL REFERENCES activity_type(activity_type_id),
  created_by       TEXT NOT NULL REFERENCES agent(agent_id),
  created_at       TIMESTAMP NOT NULL,
  source_channel   TEXT NOT NULL DEFAULT 'app' CHECK (source_channel IN ('app','import','iot_gateway','admin','mock')),
  external_ref     TEXT,                                   -- mã bản ghi ở hệ thống nguồn (mapping dữ liệu hiện có)
  CHECK (source_channel <> 'import' OR external_ref IS NOT NULL)
);
CREATE INDEX ix_activity_cycle ON activity(cycle_id, activity_type_id);

CREATE TABLE activity_revision (                          -- [APPEND-ONLY]
  revision_id     TEXT PRIMARY KEY,
  activity_id     TEXT NOT NULL REFERENCES activity(activity_id),
  revision_no     INTEGER NOT NULL CHECK (revision_no >= 1),
  performed_at    TIMESTAMP NOT NULL,                     -- xảy ra lúc nào
  time_precision  TEXT NOT NULL DEFAULT 'day' CHECK (time_precision IN ('day','hour','minute')),
  performed_by    TEXT NOT NULL REFERENCES agent(agent_id),  -- ai làm
  attributes      TEXT,
  recorded_by     TEXT NOT NULL REFERENCES agent(agent_id),  -- ai ghi
  recorded_at     TIMESTAMP NOT NULL,                     -- ghi lúc nào
  reason          TEXT,
  UNIQUE (activity_id, revision_no),
  CHECK (revision_no = 1 OR reason IS NOT NULL)
);

CREATE TABLE activity_input (                             -- [APPEND-ONLY]
  revision_id     TEXT NOT NULL REFERENCES activity_revision(revision_id),
  material_id     TEXT NOT NULL REFERENCES input_material(material_id),
  quantity        NUMERIC NOT NULL CHECK (quantity > 0),
  unit            TEXT NOT NULL CHECK (unit IN ('kg','g','l','ml','unit','m3')),
  PRIMARY KEY (revision_id, material_id)
);

-- ---------------------------------------------------------------------
-- CỤM 3 · Cảm biến
-- ---------------------------------------------------------------------
CREATE TABLE device (
  device_id       TEXT PRIMARY KEY,
  agent_id        TEXT NOT NULL UNIQUE REFERENCES agent(agent_id),
  sensor_type     TEXT NOT NULL,
  unit            TEXT NOT NULL,
  plot_id         TEXT REFERENCES plot(plot_id),          -- vị trí hiện tại; cả hai NULL = chưa lắp
  facility_id     TEXT REFERENCES facility(facility_id),
  created_by      TEXT NOT NULL REFERENCES agent(agent_id),
  created_at      TIMESTAMP NOT NULL,
  CHECK ((CASE WHEN plot_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN facility_id IS NOT NULL THEN 1 ELSE 0 END) <= 1)
);

-- Vị trí được ghi lại tại thời điểm đo → thiết bị chuyển chỗ không làm sai số đo cũ
CREATE TABLE observation (                                -- [APPEND-ONLY]
  observation_id  TEXT PRIMARY KEY,
  device_id       TEXT NOT NULL REFERENCES device(device_id),
  observed_at     TIMESTAMP NOT NULL,
  value           NUMERIC NOT NULL,
  plot_id         TEXT REFERENCES plot(plot_id),
  facility_id     TEXT REFERENCES facility(facility_id),
  recorded_at     TIMESTAMP NOT NULL,
  source_channel  TEXT NOT NULL DEFAULT 'app' CHECK (source_channel IN ('app','import','iot_gateway','admin','mock')),
  external_ref    TEXT,                                   -- mã bản ghi ở hệ thống nguồn (mapping dữ liệu hiện có)
  CHECK (source_channel <> 'import' OR external_ref IS NOT NULL),
  CHECK ((CASE WHEN plot_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN facility_id IS NOT NULL THEN 1 ELSE 0 END) = 1)
);

-- ---------------------------------------------------------------------
-- CỤM 4 · Lô và sự kiện lô
-- Thu mua (purchase) và vận chuyển (transport) chỉ là MỐC THỜI GIAN trên một lô,
-- không mang nghĩa chuyển quyền sở hữu (bên bán/mua, nơi đi/đến: ĐATN).
-- ---------------------------------------------------------------------
CREATE TABLE lot (                                        -- [APPEND-ONLY]
  lot_id              TEXT PRIMARY KEY,
  public_code         TEXT NOT NULL UNIQUE,
  lot_type            TEXT NOT NULL CHECK (lot_type IN ('harvest','aggregated','processed','packaged')),
  harvest_activity_id TEXT UNIQUE REFERENCES activity(activity_id),   -- một hoạt động thu hoạch sinh tối đa một lô
  created_by          TEXT NOT NULL REFERENCES agent(agent_id),
  created_at          TIMESTAMP NOT NULL,
  source_channel      TEXT NOT NULL DEFAULT 'app' CHECK (source_channel IN ('app','import','iot_gateway','admin','mock')),
  external_ref        TEXT,                                   -- mã bản ghi ở hệ thống nguồn (mapping dữ liệu hiện có)
  CHECK (source_channel <> 'import' OR external_ref IS NOT NULL),
  CHECK ((lot_type = 'harvest') = (harvest_activity_id IS NOT NULL))
);

CREATE TABLE lot_revision (                               -- [APPEND-ONLY]
  lot_revision_id TEXT PRIMARY KEY,
  lot_id          TEXT NOT NULL REFERENCES lot(lot_id),
  revision_no     INTEGER NOT NULL CHECK (revision_no >= 1),
  product_name    TEXT NOT NULL,
  quantity        NUMERIC NOT NULL CHECK (quantity > 0),
  unit            TEXT NOT NULL CHECK (unit IN ('kg','g','l','ml','unit','m3')),
  packaging_spec  TEXT,
  attributes      TEXT,
  recorded_by     TEXT NOT NULL REFERENCES agent(agent_id),
  recorded_at     TIMESTAMP NOT NULL,
  reason          TEXT,
  UNIQUE (lot_id, revision_no),
  CHECK (revision_no = 1 OR reason IS NOT NULL)
);

CREATE TABLE lot_event (                                  -- [APPEND-ONLY]
  event_id        TEXT PRIMARY KEY,
  event_type      TEXT NOT NULL CHECK (event_type IN ('aggregation','transformation','packaging','purchase','transport')),
  output_lot_id   TEXT UNIQUE REFERENCES lot(lot_id),     -- mỗi lô được tạo bởi tối đa một sự kiện
  subject_lot_id  TEXT REFERENCES lot(lot_id),
  occurred_at     TIMESTAMP NOT NULL,
  time_precision  TEXT NOT NULL DEFAULT 'day' CHECK (time_precision IN ('day','hour','minute')),
  facility_id     TEXT REFERENCES facility(facility_id),
  performed_by    TEXT NOT NULL REFERENCES agent(agent_id),
  recorded_by     TEXT NOT NULL REFERENCES agent(agent_id),
  recorded_at     TIMESTAMP NOT NULL,
  source_channel  TEXT NOT NULL DEFAULT 'app' CHECK (source_channel IN ('app','import','iot_gateway','admin','mock')),
  external_ref    TEXT,                                   -- mã bản ghi ở hệ thống nguồn (mapping dữ liệu hiện có)
  CHECK (source_channel <> 'import' OR external_ref IS NOT NULL),
  CHECK ((event_type IN ('aggregation','transformation','packaging')) = (output_lot_id IS NOT NULL)),
  CHECK ((event_type IN ('purchase','transport')) = (subject_lot_id IS NOT NULL))
);
CREATE INDEX ix_lot_event_subject ON lot_event(subject_lot_id);

CREATE TABLE lot_input (                                  -- [APPEND-ONLY]
  event_id        TEXT NOT NULL REFERENCES lot_event(event_id),
  input_lot_id    TEXT NOT NULL REFERENCES lot(lot_id),
  quantity_used   NUMERIC CHECK (quantity_used > 0),      -- NULL = không rõ → tỷ trọng "không rõ"
  unit            TEXT CHECK (unit IN ('kg','g','l','ml','unit','m3')),
  recorded_by     TEXT NOT NULL REFERENCES agent(agent_id),
  recorded_at     TIMESTAMP NOT NULL,
  PRIMARY KEY (event_id, input_lot_id),
  CHECK ((quantity_used IS NULL) = (unit IS NULL))
);
CREATE INDEX ix_lot_input_input ON lot_input(input_lot_id);   -- truy xuôi

-- ---------------------------------------------------------------------
-- CỤM 5 · Chứng nhận (đích nhiều đối tượng: ĐATN)
-- ---------------------------------------------------------------------
CREATE TABLE certification (
  certification_id TEXT PRIMARY KEY,
  standard         TEXT NOT NULL,
  cert_number      TEXT NOT NULL,
  issued_by        TEXT NOT NULL REFERENCES agent(agent_id),
  valid_from       DATE NOT NULL,
  valid_to         DATE NOT NULL,
  farm_id          TEXT REFERENCES farm(farm_id),
  plot_id          TEXT REFERENCES plot(plot_id),
  facility_id      TEXT REFERENCES facility(facility_id),
  lot_id           TEXT REFERENCES lot(lot_id),
  created_by       TEXT NOT NULL REFERENCES agent(agent_id),
  created_at       TIMESTAMP NOT NULL,
  CHECK (valid_to >= valid_from),
  CHECK ((CASE WHEN farm_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN plot_id IS NOT NULL THEN 1 ELSE 0 END)
       + (CASE WHEN facility_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN lot_id IS NOT NULL THEN 1 ELSE 0 END) = 1)
);

-- ---------------------------------------------------------------------
-- CỤM 6 · Minh chứng
-- ---------------------------------------------------------------------
CREATE TABLE evidence (                                   -- [APPEND-ONLY]; được phép chưa có liên kết (tải lên trước, gắn sau)
  evidence_id     TEXT PRIMARY KEY,
  evidence_kind   TEXT NOT NULL CHECK (evidence_kind IN ('photo','document','sensor','lab_report','signature','weighing_slip')),
  uri             TEXT,
  sha256          TEXT,
  observation_id  TEXT REFERENCES observation(observation_id),
  captured_at     TIMESTAMP,
  captured_by     TEXT REFERENCES agent(agent_id),
  recorded_by     TEXT NOT NULL REFERENCES agent(agent_id),
  recorded_at     TIMESTAMP NOT NULL,
  source_channel  TEXT NOT NULL DEFAULT 'app' CHECK (source_channel IN ('app','import','iot_gateway','admin','mock')),
  external_ref    TEXT,                                   -- mã bản ghi ở hệ thống nguồn (mapping dữ liệu hiện có)
  CHECK (source_channel <> 'import' OR external_ref IS NOT NULL),
  CHECK ((evidence_kind = 'sensor') = (observation_id IS NOT NULL)),
  CHECK (evidence_kind = 'sensor' OR (uri IS NOT NULL AND sha256 IS NOT NULL))
);

CREATE TABLE evidence_link (                              -- [APPEND-ONLY]
  link_id              TEXT PRIMARY KEY,
  evidence_id          TEXT NOT NULL REFERENCES evidence(evidence_id),
  activity_revision_id TEXT REFERENCES activity_revision(revision_id),
  lot_revision_id      TEXT REFERENCES lot_revision(lot_revision_id),
  lot_event_id         TEXT REFERENCES lot_event(event_id),
  plot_id              TEXT REFERENCES plot(plot_id),
  certification_id     TEXT REFERENCES certification(certification_id),
  linked_by            TEXT NOT NULL REFERENCES agent(agent_id),
  linked_at            TIMESTAMP NOT NULL,
  CHECK ((CASE WHEN activity_revision_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN lot_revision_id IS NOT NULL THEN 1 ELSE 0 END)
       + (CASE WHEN lot_event_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN plot_id IS NOT NULL THEN 1 ELSE 0 END)
       + (CASE WHEN certification_id IS NOT NULL THEN 1 ELSE 0 END) = 1)
);
-- Một file liên kết tối đa một lần với mỗi đối tượng
CREATE UNIQUE INDEX uq_link_actrev ON evidence_link(evidence_id, activity_revision_id) WHERE activity_revision_id IS NOT NULL;
CREATE UNIQUE INDEX uq_link_lotrev ON evidence_link(evidence_id, lot_revision_id)      WHERE lot_revision_id IS NOT NULL;
CREATE UNIQUE INDEX uq_link_event  ON evidence_link(evidence_id, lot_event_id)         WHERE lot_event_id IS NOT NULL;
CREATE UNIQUE INDEX uq_link_plot   ON evidence_link(evidence_id, plot_id)              WHERE plot_id IS NOT NULL;
CREATE UNIQUE INDEX uq_link_cert   ON evidence_link(evidence_id, certification_id)     WHERE certification_id IS NOT NULL;

-- ---------------------------------------------------------------------
-- CỤM 7 · Xác minh — cho bản ghi hoạt động, bản ghi lô, sự kiện lô
-- Mỗi đối tượng có tối đa MỘT kết luận hiệu lực. Lần sau phải thay thế lần trước (trigger kiểm).
-- ---------------------------------------------------------------------
CREATE TABLE verification (                               -- [APPEND-ONLY]
  verification_id            TEXT PRIMARY KEY,
  activity_revision_id       TEXT REFERENCES activity_revision(revision_id),
  lot_revision_id            TEXT REFERENCES lot_revision(lot_revision_id),
  lot_event_id               TEXT REFERENCES lot_event(event_id),
  verifier_id                TEXT NOT NULL REFERENCES agent(agent_id),
  result                     TEXT NOT NULL CHECK (result IN ('verified','rejected')),
  method                     TEXT NOT NULL CHECK (method IN ('field_visit','document_review','sensor_check')),
  note                       TEXT,
  supersedes_verification_id TEXT UNIQUE REFERENCES verification(verification_id),
  supersede_reason           TEXT,
  verified_at                TIMESTAMP NOT NULL,
  recorded_at                TIMESTAMP NOT NULL,
  CHECK ((CASE WHEN activity_revision_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN lot_revision_id IS NOT NULL THEN 1 ELSE 0 END)
       + (CASE WHEN lot_event_id IS NOT NULL THEN 1 ELSE 0 END) = 1),
  CHECK ((supersedes_verification_id IS NULL) = (supersede_reason IS NULL))
);
CREATE INDEX ix_ver_actrev ON verification(activity_revision_id);
CREATE INDEX ix_ver_lotrev ON verification(lot_revision_id);
CREATE INDEX ix_ver_event  ON verification(lot_event_id);

-- Một mã ngoài chỉ được nạp một lần cho mỗi kênh (chống nạp trùng khi import)
CREATE UNIQUE INDEX uq_ext_activity    ON activity(source_channel, external_ref)    WHERE external_ref IS NOT NULL;
CREATE UNIQUE INDEX uq_ext_lot         ON lot(source_channel, external_ref)         WHERE external_ref IS NOT NULL;
CREATE UNIQUE INDEX uq_ext_lot_event   ON lot_event(source_channel, external_ref)   WHERE external_ref IS NOT NULL;
CREATE UNIQUE INDEX uq_ext_evidence    ON evidence(source_channel, external_ref)    WHERE external_ref IS NOT NULL;
CREATE UNIQUE INDEX uq_ext_observation ON observation(source_channel, external_ref) WHERE external_ref IS NOT NULL;

-- =====================================================================
-- VIEW DÙNG CHUNG (không có phép tính ngày)
-- =====================================================================

CREATE VIEW v_activity_current AS
SELECT r.* FROM activity_revision r
WHERE r.revision_no = (SELECT MAX(r2.revision_no) FROM activity_revision r2 WHERE r2.activity_id = r.activity_id);

CREATE VIEW v_lot_current AS
SELECT r.* FROM lot_revision r
WHERE r.revision_no = (SELECT MAX(r2.revision_no) FROM lot_revision r2 WHERE r2.lot_id = r.lot_id);

-- Kết luận hiệu lực = lần xác minh chưa bị lần nào thay thế
CREATE VIEW v_verification_effective AS
SELECT v.* FROM verification v
WHERE NOT EXISTS (SELECT 1 FROM verification v2 WHERE v2.supersedes_verification_id = v.verification_id);

-- Trạng thái hoạt động: HAI chiều độc lập
--   evidence_completeness : complete | missing_evidence | missing_inputs
--   verification_state    : unverified | verified | rejected
CREATE VIEW v_activity_status AS
SELECT a.activity_id, a.cycle_id, a.activity_type_id, c.revision_id, c.revision_no, c.performed_at,
       CASE
         WHEN EXISTS (SELECT 1 FROM evidence_requirement er
                      WHERE er.activity_type_id = a.activity_type_id
                        AND (SELECT COUNT(DISTINCT COALESCE(e.sha256, e.evidence_id))   -- cùng một file tải 2 lần chỉ tính 1
                             FROM evidence_link l JOIN evidence e ON e.evidence_id = l.evidence_id
                             WHERE l.activity_revision_id = c.revision_id AND e.evidence_kind = er.evidence_kind) < er.min_count)
           THEN 'missing_evidence'
         WHEN EXISTS (SELECT 1 FROM activity_type t WHERE t.activity_type_id = a.activity_type_id AND t.uses_inputs = 1)
              AND NOT EXISTS (SELECT 1 FROM activity_input ai WHERE ai.revision_id = c.revision_id)
           THEN 'missing_inputs'
         ELSE 'complete'
       END AS evidence_completeness,
       COALESCE((SELECT v.result FROM v_verification_effective v WHERE v.activity_revision_id = c.revision_id),
                'unverified') AS verification_state
FROM activity a
JOIN v_activity_current c ON c.activity_id = a.activity_id;

CREATE VIEW v_lot_event_status AS
SELECT ev.event_id, ev.event_type, ev.output_lot_id, ev.subject_lot_id, ev.occurred_at,
       CASE
         WHEN EXISTS (SELECT 1 FROM evidence_requirement er
                      WHERE er.lot_event_type = ev.event_type
                        AND (SELECT COUNT(DISTINCT COALESCE(e.sha256, e.evidence_id))
                             FROM evidence_link l JOIN evidence e ON e.evidence_id = l.evidence_id
                             WHERE l.lot_event_id = ev.event_id AND e.evidence_kind = er.evidence_kind) < er.min_count)
           THEN 'missing_evidence'
         WHEN NOT EXISTS (SELECT 1 FROM evidence_requirement er WHERE er.lot_event_type = ev.event_type)
           THEN 'not_required'
         ELSE 'complete'
       END AS evidence_completeness,
       COALESCE((SELECT v.result FROM v_verification_effective v WHERE v.lot_event_id = ev.event_id),
                'unverified') AS verification_state
FROM lot_event ev;

CREATE VIEW v_lot_revision_status AS
SELECT c.lot_id, c.lot_revision_id, c.revision_no,
       COALESCE((SELECT v.result FROM v_verification_effective v WHERE v.lot_revision_id = c.lot_revision_id),
                'unverified') AS verification_state
FROM v_lot_current c;

-- Truy ngược: lô → nguồn. source_status: harvest | untraceable | depth_limit_reached
-- (phiên bản theo đề xuất của bên đánh giá, đã chạy thử trên SQLite và PostgreSQL)
CREATE VIEW v_lot_sources AS
WITH RECURSIVE
edge AS (
  SELECT ev.output_lot_id, li.input_lot_id, li.quantity_used, li.unit
  FROM lot_input li JOIN lot_event ev ON ev.event_id = li.event_id
),
totals AS (
  SELECT output_lot_id,
         CASE WHEN COUNT(quantity_used) < COUNT(*) OR COUNT(DISTINCT unit) > 1 THEN NULL
              ELSE SUM(quantity_used) END AS total
  FROM edge GROUP BY output_lot_id
),
src(root_lot_id, lot_id, share, depth) AS (
  SELECT lot_id, lot_id, 1.0, 0 FROM lot
  UNION ALL
  SELECT s.root_lot_id, e.input_lot_id, s.share * e.quantity_used / t.total, s.depth + 1
  FROM src s
  JOIN edge e   ON e.output_lot_id = s.lot_id
  JOIN totals t ON t.output_lot_id = e.output_lot_id
  WHERE s.depth < 20
)
SELECT s.root_lot_id, s.lot_id AS source_lot_id, a.cycle_id, a.activity_id AS harvest_activity_id,
       CASE WHEN COUNT(s.share) < COUNT(*) THEN NULL ELSE SUM(s.share) END AS share,
       'harvest' AS source_status
FROM src s
JOIN lot l      ON l.lot_id = s.lot_id AND l.lot_type = 'harvest'
JOIN activity a ON a.activity_id = l.harvest_activity_id
GROUP BY s.root_lot_id, s.lot_id, a.cycle_id, a.activity_id
UNION ALL
SELECT s.root_lot_id, s.lot_id, NULL, NULL,
       CASE WHEN COUNT(s.share) < COUNT(*) THEN NULL ELSE SUM(s.share) END, 'untraceable'
FROM src s
JOIN lot l ON l.lot_id = s.lot_id AND l.lot_type <> 'harvest'
WHERE NOT EXISTS (SELECT 1 FROM lot_event e JOIN lot_input li ON li.event_id = e.event_id   -- không có sự kiện tạo ra,
                  WHERE e.output_lot_id = s.lot_id)                                         -- hoặc sự kiện không có đầu vào
GROUP BY s.root_lot_id, s.lot_id
UNION ALL
SELECT s.root_lot_id, s.lot_id, NULL, NULL, NULL, 'depth_limit_reached'
FROM src s WHERE s.depth >= 20
GROUP BY s.root_lot_id, s.lot_id;

-- Truy xuôi: lô → mọi lô chứa nguyên liệu từ nó (vd lô thu hoạch có vấn đề → các lô chai cần thu hồi)
CREATE VIEW v_lot_destinations AS
WITH RECURSIVE
dst(root_lot_id, lot_id, depth) AS (
  SELECT lot_id, lot_id, 0 FROM lot
  UNION ALL
  SELECT d.root_lot_id, ev.output_lot_id, d.depth + 1
  FROM dst d
  JOIN lot_input li ON li.input_lot_id = d.lot_id
  JOIN lot_event ev ON ev.event_id = li.event_id
  WHERE d.depth < 20
)
SELECT root_lot_id, lot_id AS destination_lot_id, MIN(depth) AS depth,
       CASE WHEN MAX(depth) >= 20 THEN 'depth_limit_reached' ELSE 'ok' END AS dest_status
FROM dst WHERE depth > 0
GROUP BY root_lot_id, lot_id;

-- Mốc tính lịch hiện hành của mỗi chu kỳ (bản mới nhất của cycle_anchor)
CREATE VIEW v_cycle_anchor_current AS
SELECT a.* FROM cycle_anchor a
WHERE a.revision_no = (SELECT MAX(a2.revision_no) FROM cycle_anchor a2 WHERE a2.cycle_id = a.cycle_id);

-- Mọi lô nằm trên đường truy ngược của một lô (kể cả chính nó)
CREATE VIEW v_lot_ancestors AS
WITH RECURSIVE anc(root_lot_id, lot_id, depth) AS (
  SELECT lot_id, lot_id, 0 FROM lot
  UNION ALL
  SELECT a.root_lot_id, li.input_lot_id, a.depth + 1
  FROM anc a
  JOIN lot_event ev ON ev.output_lot_id = a.lot_id
  JOIN lot_input li ON li.event_id = ev.event_id
  WHERE a.depth < 20
)
SELECT root_lot_id, lot_id, MIN(depth) AS depth FROM anc GROUP BY root_lot_id, lot_id;

-- Mọi sự kiện lô trên chuỗi của một lô: sự kiện tạo ra lô tổ tiên + mốc thu mua/vận chuyển của lô tổ tiên
CREATE VIEW v_lot_chain_events AS
SELECT DISTINCT x.root_lot_id, s.event_id, s.event_type, s.occurred_at, s.evidence_completeness, s.verification_state
FROM v_lot_ancestors x
JOIN v_lot_event_status s ON s.output_lot_id = x.lot_id OR s.subject_lot_id = x.lot_id;

-- Digital timeline của một lô: hợp nhất mốc chu kỳ, hoạt động canh tác của các chu kỳ nguồn,
-- số đo cảm biến tại lô đất nguồn, sự kiện lô trên chuỗi và các lần xác minh.
-- Trang QR, dashboard và AI Story dùng chung view này.
CREATE VIEW v_lot_timeline AS
WITH src_cycle AS (
  SELECT DISTINCT root_lot_id, cycle_id FROM v_lot_sources WHERE source_status = 'harvest'
)
SELECT sc.root_lot_id, ca.anchor_date AS at, 'day' AS time_precision, 'cycle_anchor' AS kind,
       ca.cycle_anchor_id AS ref_id, sc.cycle_id AS detail, ca.recorded_by AS actor_id,
       NULL AS evidence_state, NULL AS verification_state, 'app' AS source_channel
FROM src_cycle sc JOIN v_cycle_anchor_current ca ON ca.cycle_id = sc.cycle_id
UNION ALL
SELECT sc.root_lot_id, r.performed_at, r.time_precision, 'activity',
       a.activity_id, t.code, r.performed_by,
       st.evidence_completeness, st.verification_state, a.source_channel
FROM src_cycle sc
JOIN activity a            ON a.cycle_id = sc.cycle_id
JOIN v_activity_status st  ON st.activity_id = a.activity_id
JOIN activity_revision r   ON r.revision_id = st.revision_id
JOIN activity_type t       ON t.activity_type_id = a.activity_type_id
UNION ALL
SELECT sc.root_lot_id, o.observed_at, 'minute', 'observation',
       o.observation_id, d.sensor_type, d.agent_id,
       NULL, NULL, o.source_channel
FROM src_cycle sc
JOIN cultivation_cycle c ON c.cycle_id = sc.cycle_id
JOIN observation o       ON o.plot_id = c.plot_id
                        AND SUBSTR(CAST(o.observed_at AS TEXT), 1, 10) >= CAST(c.started_at AS TEXT)
                        AND (c.closed_at IS NULL OR SUBSTR(CAST(o.observed_at AS TEXT), 1, 10) <= CAST(c.closed_at AS TEXT))
JOIN device d            ON d.device_id = o.device_id
UNION ALL
SELECT ce.root_lot_id, e.occurred_at, e.time_precision, 'lot_event',
       e.event_id, e.event_type, e.performed_by,
       ce.evidence_completeness, ce.verification_state, e.source_channel
FROM v_lot_chain_events ce JOIN lot_event e ON e.event_id = ce.event_id
UNION ALL
SELECT sc.root_lot_id, v.verified_at, 'minute', 'verification',
       v.verification_id,
       CASE WHEN r.revision_id <> st.revision_id THEN 'activity (bản ghi cũ)'
            WHEN v.supersedes_verification_id IS NULL THEN 'activity' ELSE 'activity (thay thế lần trước)' END,
       v.verifier_id, NULL, v.result, 'app'
FROM src_cycle sc
JOIN activity a          ON a.cycle_id = sc.cycle_id
JOIN activity_revision r ON r.activity_id = a.activity_id
JOIN v_activity_status st ON st.activity_id = a.activity_id
JOIN verification v      ON v.activity_revision_id = r.revision_id
UNION ALL
SELECT ce.root_lot_id, v.verified_at, 'minute', 'verification',
       v.verification_id,
       CASE WHEN v.supersedes_verification_id IS NULL THEN 'lot_event' ELSE 'lot_event (thay thế lần trước)' END,
       v.verifier_id, NULL, v.result, 'app'
FROM v_lot_chain_events ce JOIN verification v ON v.lot_event_id = ce.event_id
UNION ALL
SELECT x.root_lot_id, r.recorded_at, 'minute', 'lot_revision',
       r.lot_revision_id, CASE WHEN r.revision_no = 1 THEN 'lot_created' ELSE 'lot_corrected' END,
       r.recorded_by, NULL, NULL, 'app'
FROM v_lot_ancestors x JOIN lot_revision r ON r.lot_id = x.lot_id
UNION ALL
SELECT x.root_lot_id, v.verified_at, 'minute', 'verification',
       v.verification_id, 'lot_revision', v.verifier_id, NULL, v.result, 'app'
FROM v_lot_ancestors x JOIN lot_revision r ON r.lot_id = x.lot_id
JOIN verification v ON v.lot_revision_id = r.lot_revision_id;

-- v_integrity_issues: định nghĩa trong views_<hệ>.sql (cần phép so ngày)
