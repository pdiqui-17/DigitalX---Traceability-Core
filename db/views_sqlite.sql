-- View có phép tính ngày — sqlite (nạp sau schema.sql và triggers_sqlite.sql) — v0.5
-- SINH TỰ ĐỘNG bởi gen_views.py, đừng sửa tay.

-- Mỗi chu kỳ × mỗi hoạt động BẮT BUỘC theo crop profile: có ghi chưa, đúng lịch không
-- schedule_state: undetermined (chưa có mốc) | not_due | not_recorded | off_schedule | on_schedule
-- not_due CHỈ dùng khi chu kỳ còn mở: chu kỳ đã đóng thì việc chưa ghi là thiếu (v0.5, lỗi E1)
CREATE VIEW v_cycle_expected AS
SELECT c.cycle_id, t.activity_type_id, t.code,
       CASE WHEN an.anchor_date IS NULL THEN NULL ELSE date(an.anchor_date, printf('%+d days', t.offset_days - t.tolerance_days)) END AS window_start,
       CASE WHEN an.anchor_date IS NULL THEN NULL ELSE date(an.anchor_date, printf('%+d days', t.offset_days + t.tolerance_days)) END AS window_end,
       s.activity_id, s.performed_at, s.evidence_completeness, s.verification_state,
       CASE
         WHEN an.anchor_date IS NULL THEN 'undetermined'
         WHEN s.activity_id IS NULL AND c.closed_at IS NULL AND date(an.anchor_date, printf('%+d days', t.offset_days + t.tolerance_days)) >= date('now') THEN 'not_due'
         WHEN s.activity_id IS NULL THEN 'not_recorded'
         WHEN date(s.performed_at) < date(an.anchor_date, printf('%+d days', t.offset_days - t.tolerance_days)) OR date(s.performed_at) > date(an.anchor_date, printf('%+d days', t.offset_days + t.tolerance_days)) THEN 'off_schedule'
         ELSE 'on_schedule'
       END AS schedule_state
FROM cultivation_cycle c
LEFT JOIN v_cycle_anchor_current an ON an.cycle_id = c.cycle_id
JOIN stage st        ON st.crop_profile_id = c.crop_profile_id
JOIN activity_type t ON t.stage_id = st.stage_id AND t.requirement = 'mandatory'
LEFT JOIN v_activity_status s ON s.activity_id = (
  SELECT a.activity_id FROM activity a
  WHERE a.cycle_id = c.cycle_id AND a.activity_type_id = t.activity_type_id
  ORDER BY a.created_at, a.activity_id LIMIT 1);

-- Độ đầy đủ theo chu kỳ. "Đến hạn" = không thuộc undetermined / not_due.
-- cycle_state (đủ minh chứng) và on_schedule_ratio (đúng lịch) tách riêng.
-- n_other_problem: hoạt động đã ghi mà thiếu minh chứng / bị từ chối và CHƯA được xét ở v_cycle_expected
--   (loại không bắt buộc — lỗi F1; lần ghi thứ 2 trở đi của loại bắt buộc — RV11) cũng làm chu kỳ chưa đủ
CREATE VIEW v_cycle_completeness AS
SELECT x.*,
       CASE WHEN n_due = 0 THEN NULL ELSE 1.0 * n_evidence_complete / n_due END AS completeness_ratio,
       CASE WHEN n_undetermined > 0 THEN 'undetermined'
            WHEN n_not_recorded = 0 AND n_evidence_complete = n_due AND n_rejected = 0 AND n_other_problem = 0 THEN 'complete'
            ELSE 'incomplete' END AS cycle_state,
       CASE WHEN n_due > 0 AND n_verified = n_due THEN 1 ELSE 0 END AS all_verified,
       CASE WHEN n_on_schedule + n_off_schedule = 0 THEN NULL
            ELSE 1.0 * n_on_schedule / (n_on_schedule + n_off_schedule) END AS on_schedule_ratio
FROM (
  SELECT e.cycle_id,
         COUNT(*) AS n_expected,
         SUM(CASE WHEN schedule_state = 'undetermined' THEN 1 ELSE 0 END) AS n_undetermined,
         SUM(CASE WHEN schedule_state = 'not_due'      THEN 1 ELSE 0 END) AS n_not_due,
         SUM(CASE WHEN schedule_state IN ('not_recorded','off_schedule','on_schedule') THEN 1 ELSE 0 END) AS n_due,
         SUM(CASE WHEN schedule_state = 'not_recorded' THEN 1 ELSE 0 END) AS n_not_recorded,
         SUM(CASE WHEN schedule_state = 'off_schedule' THEN 1 ELSE 0 END) AS n_off_schedule,
         SUM(CASE WHEN schedule_state = 'on_schedule'  THEN 1 ELSE 0 END) AS n_on_schedule,
         SUM(CASE WHEN schedule_state IN ('off_schedule','on_schedule') AND evidence_completeness = 'complete'
                       AND verification_state <> 'rejected' THEN 1 ELSE 0 END) AS n_evidence_complete,
         SUM(CASE WHEN verification_state = 'verified' THEN 1 ELSE 0 END) AS n_verified,
         SUM(CASE WHEN verification_state = 'rejected' THEN 1 ELSE 0 END) AS n_rejected,
         (SELECT COUNT(*) FROM v_activity_status s
          WHERE s.cycle_id = e.cycle_id
            AND (s.evidence_completeness <> 'complete' OR s.verification_state = 'rejected')
            AND NOT EXISTS (SELECT 1 FROM v_cycle_expected x
                            WHERE x.cycle_id = s.cycle_id AND x.activity_id = s.activity_id)) AS n_other_problem
  FROM v_cycle_expected e GROUP BY e.cycle_id
) x;

-- Trạng thái của một lô (cái người quét QR thấy)
-- trace_state: cycle_detected | unknown_share | share_inconsistent | untraceable | partially_untraceable | fully_traced
--   fully_traced chỉ khi phần truy được về lô thu hoạch = 100% (lỗi B1/B2/C1)
-- chain_evidence_state: rejected | incomplete | no_source_event | no_post_harvest_events | complete
CREATE VIEW v_lot_status AS
WITH agg AS (
  SELECT l.lot_id, l.public_code, l.lot_type,
         SUM(CASE WHEN s.source_status = 'harvest' THEN 1 ELSE 0 END)                         AS n_harvest_sources,
         SUM(CASE WHEN s.source_status = 'harvest' THEN s.share ELSE 0 END)                  AS traced_share,
         SUM(CASE WHEN s.source_status = 'untraceable' THEN s.share ELSE 0 END)              AS untraceable_share,
         SUM(CASE WHEN s.source_status = 'harvest' AND cc.cycle_state = 'complete' THEN s.share ELSE 0 END)     AS complete_share,
         SUM(CASE WHEN s.source_status = 'harvest' AND cc.cycle_state = 'undetermined' THEN s.share ELSE 0 END) AS undetermined_share,
         SUM(CASE WHEN s.source_status = 'harvest' AND cc.all_verified = 1 THEN s.share ELSE 0 END)             AS verified_share,
         SUM(CASE WHEN s.source_status = 'depth_limit_reached' THEN 1 ELSE 0 END) AS n_depth,
         SUM(CASE WHEN s.source_status IN ('harvest','untraceable') AND s.share IS NULL THEN 1 ELSE 0 END) AS n_null_share,
         SUM(CASE WHEN s.source_status = 'untraceable' THEN 1 ELSE 0 END) AS n_untraceable
  FROM lot l
  LEFT JOIN v_lot_sources s         ON s.root_lot_id = l.lot_id
  LEFT JOIN v_cycle_completeness cc ON cc.cycle_id = s.cycle_id
  GROUP BY l.lot_id, l.public_code, l.lot_type
),
chain AS (
  SELECT g.lot_id,
         (SELECT COUNT(*) FROM v_lot_chain_events ce WHERE ce.root_lot_id = g.lot_id) AS n_chain_events,
         (SELECT COUNT(*) FROM v_lot_chain_events ce WHERE ce.root_lot_id = g.lot_id
            AND ce.evidence_completeness = 'missing_evidence') AS n_chain_missing_evidence,
         (SELECT COUNT(*) FROM v_lot_chain_events ce WHERE ce.root_lot_id = g.lot_id AND ce.verification_state = 'rejected')
       + (SELECT COUNT(*) FROM v_lot_ancestors x JOIN v_lot_revision_status rs ON rs.lot_id = x.lot_id
            WHERE x.root_lot_id = g.lot_id AND rs.verification_state = 'rejected') AS n_chain_rejected,
         CASE WHEN g.lot_type <> 'harvest'
               AND NOT EXISTS (SELECT 1 FROM lot_event e WHERE e.output_lot_id = g.lot_id) THEN 1 ELSE 0 END AS no_source_event
  FROM agg g
)
SELECT g.lot_id, g.public_code, g.n_harvest_sources, g.traced_share, g.untraceable_share,
       g.complete_share, g.undetermined_share, g.verified_share,
       CASE
         WHEN g.n_depth > 0 THEN 'cycle_detected'
         WHEN g.n_null_share > 0 THEN 'unknown_share'
         WHEN ABS(g.traced_share + g.untraceable_share - 1) > 0.000001 THEN 'share_inconsistent'
         WHEN g.n_untraceable > 0 AND g.traced_share = 0 THEN 'untraceable'
         WHEN g.n_untraceable > 0 THEN 'partially_untraceable'
         ELSE 'fully_traced'
       END AS trace_state,
       ch.n_chain_events, ch.n_chain_missing_evidence, ch.n_chain_rejected,
       CASE
         WHEN ch.n_chain_rejected > 0 THEN 'rejected'
         WHEN ch.n_chain_missing_evidence > 0 THEN 'incomplete'
         WHEN ch.no_source_event = 1 THEN 'no_source_event'
         WHEN ch.n_chain_events = 0 THEN 'no_post_harvest_events'
         ELSE 'complete'
       END AS chain_evidence_state
FROM agg g JOIN chain ch ON ch.lot_id = g.lot_id;

-- Vi phạm thời gian cách ly: phun thuốc trong cùng chu kỳ, cách ngày thu hoạch ít hơn phi_days (theo cây trồng)
CREATE VIEW v_phi_violations AS
SELECT h.activity_id AS harvest_activity_id, sp.activity_id AS spray_activity_id, h.cycle_id,
       m.trade_name, mr.phi_days, mr.rule_source, mr.is_assumption,
       (julianday(date(hc.performed_at)) - julianday(date(sc.performed_at))) AS days_between
FROM activity h
JOIN activity_type ht      ON ht.activity_type_id = h.activity_type_id AND ht.produces_lot = 1
JOIN v_activity_current hc ON hc.activity_id = h.activity_id
JOIN cultivation_cycle c   ON c.cycle_id = h.cycle_id
JOIN crop_profile p        ON p.crop_profile_id = c.crop_profile_id
JOIN activity sp           ON sp.cycle_id = h.cycle_id
JOIN v_activity_current sc ON sc.activity_id = sp.activity_id
JOIN activity_input ai     ON ai.revision_id = sc.revision_id
JOIN input_material m      ON m.material_id = ai.material_id AND m.kind = 'pesticide'
JOIN material_crop_rule mr ON mr.material_id = m.material_id AND mr.crop_code = p.crop_code
WHERE (julianday(date(hc.performed_at)) - julianday(date(sc.performed_at))) >= 0
  AND (julianday(date(hc.performed_at)) - julianday(date(sc.performed_at))) < mr.phi_days;

-- Kiểm tra nhất quán liên bảng (không viết được bằng CHECK/trigger, hoặc là cảnh báo mềm)
CREATE VIEW v_integrity_issues AS
SELECT 'orphan_lot' AS issue, l.lot_id AS subject_id, 'Lô không phải thu hoạch nhưng không có sự kiện tạo ra' AS detail
FROM lot l
WHERE l.lot_type <> 'harvest' AND NOT EXISTS (SELECT 1 FROM lot_event e WHERE e.output_lot_id = l.lot_id)
UNION ALL
SELECT 'event_without_inputs', e.event_id, 'Sự kiện gộp/chế biến/đóng gói không có đầu vào'
FROM lot_event e
WHERE e.event_type IN ('aggregation','transformation','packaging')
  AND NOT EXISTS (SELECT 1 FROM lot_input li WHERE li.event_id = e.event_id)
UNION ALL
SELECT 'milestone_with_inputs', e.event_id, 'Mốc thu mua/vận chuyển không được có đầu vào'
FROM lot_event e
WHERE e.event_type IN ('purchase','transport')
  AND EXISTS (SELECT 1 FROM lot_input li WHERE li.event_id = e.event_id)
UNION ALL
SELECT 'lot_type_mismatch', e.event_id, 'Loại lô đầu ra không khớp loại sự kiện (dữ liệu nạp trước khi có trigger)'
FROM lot_event e JOIN lot l ON l.lot_id = e.output_lot_id
WHERE l.lot_type <> CASE e.event_type WHEN 'aggregation' THEN 'aggregated' WHEN 'transformation' THEN 'processed'
                                      WHEN 'packaging' THEN 'packaged' END
UNION ALL
SELECT 'harvest_without_lot', a.activity_id, 'Hoạt động thu hoạch chưa sinh lô'
FROM activity a JOIN activity_type t ON t.activity_type_id = a.activity_type_id AND t.produces_lot = 1
WHERE NOT EXISTS (SELECT 1 FROM lot l WHERE l.harvest_activity_id = a.activity_id)
UNION ALL
SELECT 'missing_phi_rule', ai.revision_id, 'Thuốc BVTV chưa có thời gian cách ly cho cây trồng này'
FROM activity_input ai
JOIN input_material m   ON m.material_id = ai.material_id AND m.kind = 'pesticide'
JOIN activity_revision r ON r.revision_id = ai.revision_id
JOIN activity a          ON a.activity_id = r.activity_id
JOIN cultivation_cycle c ON c.cycle_id = a.cycle_id
JOIN crop_profile p      ON p.crop_profile_id = c.crop_profile_id
WHERE NOT EXISTS (SELECT 1 FROM material_crop_rule mr WHERE mr.material_id = m.material_id AND mr.crop_code = p.crop_code)
UNION ALL
SELECT 'unit_mismatch', li.event_id, 'Các đầu vào của một sự kiện khác đơn vị → tỷ trọng không xác định'
FROM lot_input li WHERE li.unit IS NOT NULL
GROUP BY li.event_id HAVING COUNT(DISTINCT li.unit) > 1
UNION ALL
SELECT 'over_consumption', li.input_lot_id, 'Tổng khối lượng đã dùng vượt khối lượng của lô (cùng đơn vị)'
FROM lot_input li JOIN v_lot_current lc ON lc.lot_id = li.input_lot_id AND lc.unit = li.unit
GROUP BY li.input_lot_id, lc.quantity HAVING SUM(li.quantity_used) > lc.quantity
UNION ALL
SELECT 'event_time_order', li.event_id, 'Sự kiện xảy ra trước khi lô đầu vào được tạo ra'
FROM lot_input li
JOIN lot_event e  ON e.event_id = li.event_id
JOIN lot_event pe ON pe.output_lot_id = li.input_lot_id
WHERE date(e.occurred_at) < date(pe.occurred_at)
UNION ALL
SELECT 'event_time_order', li.event_id, 'Sự kiện xảy ra trước ngày thu hoạch của lô đầu vào'
FROM lot_input li
JOIN lot_event e ON e.event_id = li.event_id
JOIN lot l       ON l.lot_id = li.input_lot_id AND l.lot_type = 'harvest'
JOIN v_activity_current h ON h.activity_id = l.harvest_activity_id
WHERE date(e.occurred_at) < date(h.performed_at)
UNION ALL
SELECT 'activity_before_cycle_start', a.activity_id, 'Hoạt động ghi ngày trước ngày bắt đầu chu kỳ'
FROM activity a
JOIN v_activity_current r ON r.activity_id = a.activity_id
JOIN cultivation_cycle c  ON c.cycle_id = a.cycle_id
WHERE date(r.performed_at) < c.started_at
UNION ALL
SELECT 'share_sum_mismatch', s.root_lot_id, 'Tổng tỷ trọng nguồn khác 100%'
FROM v_lot_sources s WHERE s.source_status IN ('harvest','untraceable')
GROUP BY s.root_lot_id
HAVING COUNT(s.share) = COUNT(*) AND ABS(SUM(s.share) - 1) > 0.000001
UNION ALL
SELECT 'season_crop_mismatch', c.cycle_id, 'Chu kỳ thuộc vụ của cây trồng khác'
FROM cultivation_cycle c
JOIN season se       ON se.season_id = c.season_id AND se.crop_code IS NOT NULL
JOIN crop_profile p  ON p.crop_profile_id = c.crop_profile_id
WHERE se.crop_code <> p.crop_code
UNION ALL
SELECT 'lot_graph_cycle', s.root_lot_id, 'Đồ thị lô có vòng (dữ liệu nạp trước khi có trigger)'
FROM v_lot_sources s WHERE s.source_status = 'depth_limit_reached';

-- Digital timeline của một lô: hợp nhất mốc chu kỳ, hoạt động canh tác của các chu kỳ nguồn,
-- số đo cảm biến tại lô đất nguồn, sự kiện lô trên chuỗi và các lần xác minh.
-- Trang QR, dashboard và AI Story dùng chung view này.
-- So ngày bằng kiểu DATE (không so chuỗi) để không phụ thuộc DateStyle của phiên PostgreSQL (v0.5.1, P8).
-- 'lot_created' lấy thời điểm nghiệp vụ (sự kiện / hoạt động thu hoạch tạo ra lô), không lấy giờ nạp (v0.5.1, RV13).
-- kind_rank: thứ tự khi trùng thời điểm — ORDER BY at, kind_rank (mốc 1, hoạt động 2, số đo 3, sự kiện lô 4, bản ghi lô 5, xác minh 6).
CREATE VIEW v_lot_timeline AS
WITH src_cycle AS (
  SELECT DISTINCT root_lot_id, cycle_id FROM v_lot_sources WHERE source_status = 'harvest'
)
SELECT sc.root_lot_id, ca.anchor_date AS at, 'day' AS time_precision, 'cycle_anchor' AS kind,
       ca.cycle_anchor_id AS ref_id, sc.cycle_id AS detail, ca.recorded_by AS actor_id,
       NULL AS evidence_state, NULL AS verification_state, 'app' AS source_channel, 1 AS kind_rank
FROM src_cycle sc JOIN v_cycle_anchor_current ca ON ca.cycle_id = sc.cycle_id
UNION ALL
SELECT sc.root_lot_id, r.performed_at, r.time_precision, 'activity',
       a.activity_id, t.code, r.performed_by,
       st.evidence_completeness, st.verification_state, a.source_channel, 2
FROM src_cycle sc
JOIN activity a            ON a.cycle_id = sc.cycle_id
JOIN v_activity_status st  ON st.activity_id = a.activity_id
JOIN activity_revision r   ON r.revision_id = st.revision_id
JOIN activity_type t       ON t.activity_type_id = a.activity_type_id
UNION ALL
SELECT sc.root_lot_id, o.observed_at, 'minute', 'observation',
       o.observation_id, d.sensor_type, d.agent_id,
       NULL, NULL, o.source_channel, 3
FROM src_cycle sc
JOIN cultivation_cycle c ON c.cycle_id = sc.cycle_id
JOIN observation o       ON o.plot_id = c.plot_id
                        AND date(o.observed_at) >= c.started_at
                        AND (c.closed_at IS NULL OR date(o.observed_at) <= c.closed_at)
JOIN device d            ON d.device_id = o.device_id
UNION ALL
SELECT ce.root_lot_id, e.occurred_at, e.time_precision, 'lot_event',
       e.event_id, e.event_type, e.performed_by,
       ce.evidence_completeness, ce.verification_state, e.source_channel, 4
FROM v_lot_chain_events ce JOIN lot_event e ON e.event_id = ce.event_id
UNION ALL
SELECT sc.root_lot_id, v.verified_at, 'minute', 'verification',
       v.verification_id,
       CASE WHEN r.revision_id <> st.revision_id THEN 'activity (bản ghi cũ)'
            WHEN v.supersedes_verification_id IS NULL THEN 'activity' ELSE 'activity (thay thế lần trước)' END,
       v.verifier_id, NULL, v.result, 'app', 6
FROM src_cycle sc
JOIN activity a          ON a.cycle_id = sc.cycle_id
JOIN activity_revision r ON r.activity_id = a.activity_id
JOIN v_activity_status st ON st.activity_id = a.activity_id
JOIN verification v      ON v.activity_revision_id = r.revision_id
UNION ALL
SELECT ce.root_lot_id, v.verified_at, 'minute', 'verification',
       v.verification_id,
       CASE WHEN v.supersedes_verification_id IS NULL THEN 'lot_event' ELSE 'lot_event (thay thế lần trước)' END,
       v.verifier_id, NULL, v.result, 'app', 6
FROM v_lot_chain_events ce JOIN verification v ON v.lot_event_id = ce.event_id
UNION ALL
SELECT x.root_lot_id,
       CASE WHEN r.revision_no = 1 THEN COALESCE(ce.occurred_at, ha.performed_at, r.recorded_at) ELSE r.recorded_at END,
       CASE WHEN r.revision_no = 1 AND ce.event_id IS NOT NULL THEN ce.time_precision
            WHEN r.revision_no = 1 AND ha.revision_id IS NOT NULL THEN ha.time_precision ELSE 'minute' END,
       'lot_revision',
       r.lot_revision_id, CASE WHEN r.revision_no = 1 THEN 'lot_created' ELSE 'lot_corrected' END,
       r.recorded_by, NULL, NULL, 'app', 5
FROM v_lot_ancestors x JOIN lot_revision r ON r.lot_id = x.lot_id
JOIN lot l                     ON l.lot_id = r.lot_id
LEFT JOIN lot_event ce         ON ce.output_lot_id = r.lot_id
LEFT JOIN v_activity_current ha ON ha.activity_id = l.harvest_activity_id
UNION ALL
SELECT x.root_lot_id, v.verified_at, 'minute', 'verification',
       v.verification_id, 'lot_revision', v.verifier_id, NULL, v.result, 'app', 6
FROM v_lot_ancestors x JOIN lot_revision r ON r.lot_id = x.lot_id
JOIN verification v ON v.lot_revision_id = r.lot_revision_id;
