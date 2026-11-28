"""Ca thử phản biện schema v0.4 (người đánh giá độc lập).

    cd /tmp/review_v04 && python3 review_tests.py            # SQLite, mọi ca
    python3 review_tests.py pg                               # thêm các ca trigger trên PostgreSQL (cấu hình ở db/.env, qua db/dbtools.py)
    python3 review_tests.py perf [n_farms] [n_lots]          # đo hiệu năng SQLite (mặc định 200 hộ, 2000 lô)

Mỗi ca dựng CSDL mới từ db/schema.sql + triggers + views, nạp bộ dữ liệu nền nhỏ
(3 hộ → gộp lô RAW → ép dầu PROC → chai 80ml/250ml), rồi thử phá.
Dòng 'PHÁT HIỆN' = hành vi khác với mong đợi của đề bài; 'OK' = thiết kế đứng vững.
"""
import sqlite3, sys, time, pathlib, random

DB_DIR = pathlib.Path(__file__).parent.parent / "db"
sys.path.insert(0, str(DB_DIR))
from dbtools import DBError, Postgres, setup_output  # noqa: E402

# Phát hiện nhóm đã chấp nhận và ghi thành giới hạn (docs/D1_D2_schema_design.md mục 8) — vẫn chạy, báo riêng
KNOWN_LIMITS = {
    "G2": "mục 8 dòng 7d — thu hoạch nhiều đợt (ĐATN)",
    "G4": "mục 8 dòng 7d — hai chu kỳ chồng nhau trên một lô đất (ĐATN)",
    "RV5": "mục 8 dòng 7b — đóng chu kỳ nhầm ngày chưa đính chính được",
    "RV8": "mục 8 dòng 16 — SQLite không phân biệt INSERT OR IGNORE với INSERT; nạp lại dùng INSERT … WHERE NOT EXISTS",
    "RV14": "mục 8 dòng 7c — yêu cầu minh chứng theo loại sự kiện lô chưa có hiệu lực theo ngày (sửa cùng đợt trang QR)",
    "RV15": "mục 8 dòng 20 — luật cách ly không ghi thời điểm thêm (sửa cùng đợt trang QR)",
}
T = "2026-11-25T08:00:00"
findings, oks = [], []


def report(code, ok, msg, detail=""):
    (oks if ok else findings).append(code)
    print(f"  [{'OK       ' if ok else 'PHÁT HIỆN'}] {code}: {msg}" + (f"\n              → {detail}" if detail else ""))


def q(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


class Fx:
    """Sinh SQL cho bộ dữ liệu nền."""
    def __init__(self):
        self.sql = []

    def ins(self, table, *vals):
        self.sql.append(f"INSERT INTO {table} VALUES ({', '.join(q(v) for v in vals)});")

    def raw(self, s):
        self.sql.append(s if s.rstrip().endswith(";") else s + ";")

    def text(self):
        return "\n".join(self.sql)


def base_fixture(n_farms=3, extra_plots=False, open_cycles=(), er1_min=1, multi_harvest=False):
    # v0.5: config và closed_at không UPDATE được nữa → tham số hoá ngay khi dựng dữ liệu
    f = Fx()
    for a in ["u_fns:organization:company", "u_qa:person:company", "u_ktv:person:technician", "u_dev:device:system"]:
        i, k, r = a.split(":")
        f.ins("agent", i, k, i, r, None, T)
    f.ins("facility", "fac", "Nhà máy", "processing_plant", "u_fns", "Tây Ninh", "Lương Hòa", None)
    f.ins("crop_profile", "cp", "SESAME", "Mè", 1, "sowing", None, None, "2026-01-01")
    f.ins("stage", "st1", "cp", 1, "Chăm sóc"); f.ins("stage", "st2", "cp", 2, "Thu hoạch")
    f.ins("activity_type", "at_bt", "st1", "TOP_DRESS", "Bón thúc", "mandatory", 15, 3, 0, 1, None, "detail", None, 0)
    f.ins("activity_type", "at_ph", "st1", "SPRAY", "Phun", "conditional", None, 0, 0, 1, None, "detail", None, 0)
    f.ins("activity_type", "at_th", "st2", "HARVEST", "Thu hoạch", "mandatory", 80, 7, 1, 0, None, "summary", None, 0)
    if multi_harvest:   # v0.5.1: cấu hình phải có trước khi crop profile có chu kỳ (RV1/RV2) → tạo cùng lúc dựng dữ liệu
        f.ins("activity_type", "at_th2", "st2", "HARVEST_2", "Thu hoạch đợt 2", "optional", None, 0, 1, 0, None, "summary", None, 0)
    f.ins("evidence_requirement", "er1", "at_bt", None, "photo", er1_min, None, 0)
    f.ins("evidence_requirement", "er2", "at_ph", None, "photo", 1, None, 0)
    f.ins("evidence_requirement", "er3", "at_th", None, "weighing_slip", 1, None, 0)
    f.ins("evidence_requirement", "er4", None, "aggregation", "weighing_slip", 1, None, 0)
    f.ins("evidence_requirement", "er5", None, "transformation", "photo", 1, None, 0)
    f.ins("input_material", "m_ure", "fertilizer", "Urê", None, None, "kg")
    f.ins("season", "ss", "u_fns", "ĐX", "SESAME", "2026-11-01", "2027-03-31", "u_fns", T)
    f.ev_n = 0

    def evid(kind, col, target, sha=None):
        f.ev_n += 1; eid = f"ev{f.ev_n}"
        f.ins("evidence", eid, kind, f"s3://{eid}", sha or f"sha{eid}", None, None, None, "u_fns", T, "app", None)
        f.raw(f"INSERT INTO evidence_link (link_id,evidence_id,{col},linked_by,linked_at) VALUES ('l{eid}','{eid}',{q(target)},'u_fns','{T}')")
        return eid
    f.evid = evid

    def act(aid, cyc, at, who, when, inputs=()):
        f.ins("activity", aid, cyc, at, who, T, "app", None)
        f.ins("activity_revision", aid + "_r1", aid, 1, when, "day", who, None, who, T, None)
        for m, qq, u in inputs:
            f.ins("activity_input", aid + "_r1", m, qq, u)
        return aid + "_r1"
    f.act = act

    def lot(lid, ltype, qty, unit, harvest=None):
        f.ins("lot", lid, "QR-" + lid, ltype, harvest, "u_fns", T, "app", None)
        f.ins("lot_revision", lid + "_r1", lid, 1, "x", qty, unit, None, None, "u_fns", T, None)
    f.lot = lot

    def event(eid, et, out, subj, when, inputs=()):
        f.ins("lot_event", eid, et, out, subj, when, "day", "fac", "u_fns", "u_fns", T, "app", None)
        for lid, qq, u in inputs:
            f.ins("lot_input", eid, lid, qq, u, "u_fns", T)
    f.event = event

    kgs = [400, 350, 250] + [100] * max(0, n_farms - 3)
    for i in range(1, n_farms + 1):
        f.ins("agent", f"u{i}", "person", f"Hộ {i}", "farmer", None, T)
        f.ins("farm", f"f{i}", f"u{i}", f"Hộ {i}", "Tây Ninh", "Lương Hòa", None, "u_fns", T)
        f.ins("plot", f"p{i}", f"f{i}", "L1", 5000, None, None, "u_fns", T)
        f.ins("cultivation_cycle", f"c{i}", f"p{i}", "cp", None, "ss", "2026-11-15", None if f"c{i}" in open_cycles else "2027-02-28", "u_fns", T)
        f.ins("cycle_anchor", f"an{i}", f"c{i}", 1, "2026-11-20", f"u{i}", T, None)
        if i != 3:   # hộ 3 KHÔNG ghi bón thúc
            r = act(f"bt{i}", f"c{i}", "at_bt", f"u{i}", "2026-12-05", [("m_ure", 30, "kg")]); evid("photo", "activity_revision_id", r)
        r = act(f"th{i}", f"c{i}", "at_th", f"u{i}", "2027-02-10"); evid("weighing_slip", "activity_revision_id", r)
        lot(f"h{i}", "harvest", kgs[i - 1], "kg", harvest=f"th{i}")
    if n_farms == 3:
        lot("raw", "aggregated", 1000, "kg")
        event("e_gop", "aggregation", "raw", None, "2027-02-12", [("h1", 400, "kg"), ("h2", 350, "kg"), ("h3", 250, "kg")])
        evid("weighing_slip", "lot_event_id", "e_gop")
        lot("proc", "processed", 400, "l")
        event("e_ep", "transformation", "proc", None, "2027-02-20", [("raw", 1000, "kg")])
        evid("photo", "lot_event_id", "e_ep")
        lot("b80", "packaged", 2500, "unit"); event("e_b80", "packaging", "b80", None, "2027-02-22", [("proc", 200, "l")])
        lot("b250", "packaged", 800, "unit"); event("e_b250", "packaging", "b250", None, "2027-02-22", [("proc", 200, "l")])
    return f


class SQLiteDB:
    def __init__(self, fx=None):
        self.c = sqlite3.connect(":memory:")
        self.c.execute("PRAGMA foreign_keys = ON")
        for fn in ("schema.sql", "triggers_sqlite.sql", "views_sqlite.sql"):
            self.c.executescript((DB_DIR / fn).read_text(encoding="utf-8"))
        if fx:
            self.c.executescript(fx.text())

    def x(self, sql):
        return [tuple(r) for r in self.c.execute(sql).fetchall()]

    def ok(self, sql):
        try:
            self.c.execute(sql); return True, ""
        except sqlite3.Error as e:
            return False, str(e)

    def one(self, sql):
        r = self.x(sql); return r[0] if r else None


def num(v):
    return None if v is None else round(float(v), 4)


# ======================================================================
def run_sqlite():
    print("\n=== Các ca thử mới trên SQLite ===")

    # ---------- A. Đồ thị kim cương ----------
    print("\nA · Đồ thị lô kim cương (RAW tách 2 nhánh rồi hợp lại) + vận chuyển trên RAW")
    f = base_fixture()
    f.event("e_vc", "transport", None, "raw", "2027-02-13")
    f.lot("y", "processed", 240, "l"); f.event("e_y", "transformation", "y", None, "2027-02-21", [("raw", 600, "kg")]); f.evid("photo", "lot_event_id", "e_y")
    f.lot("z", "processed", 160, "l"); f.event("e_z", "transformation", "z", None, "2027-02-21", [("raw", 400, "kg")]); f.evid("photo", "lot_event_id", "e_z")
    f.lot("w", "aggregated", 300, "l"); f.event("e_w", "aggregation", "w", None, "2027-02-23", [("y", 200, "l"), ("z", 100, "l")])
    f.evid("weighing_slip", "lot_event_id", "e_w")
    db = SQLiteDB(f)
    src = {r[0]: num(r[1]) for r in db.x("SELECT source_lot_id, share FROM v_lot_sources WHERE root_lot_id='w'")}
    tot = round(sum(src.values()), 6)
    report("A1", tot == 1.0 and src == {"h1": 0.4, "h2": 0.35, "h3": 0.25}, "tỷ trọng kim cương cộng đủ 1", str(src))
    ce = db.x("SELECT event_id FROM v_lot_chain_events WHERE root_lot_id='w'")
    ids = [r[0] for r in ce]
    report("A2", len(ids) == len(set(ids)) == 5, "v_lot_chain_events không trùng (đúng 5: e_gop, e_vc, e_y, e_z, e_w)", f"{len(ids)} dòng: {sorted(ids)}")
    st = db.one("SELECT n_chain_events, chain_evidence_state, traced_share, n_harvest_sources FROM v_lot_status WHERE lot_id='w'")
    report("A3", (st[0], st[1], round(float(st[2]), 6), st[3]) == (5, "complete", 1.0, 3), "v_lot_status kim cương không đếm trùng", str(st))
    dup = db.x("SELECT kind, ref_id, COUNT(*) FROM v_lot_timeline WHERE root_lot_id='w' GROUP BY kind, ref_id HAVING COUNT(*)>1")
    report("A4", dup == [], "timeline kim cương không trùng dòng", str(dup))

    # ---------- B. Sự kiện không có đầu vào → báo 'fully_traced' ----------
    print("\nB · Lô có sự kiện tạo ra nhưng sự kiện chưa có lot_input")
    f = base_fixture()
    f.lot("b500", "packaged", 100, "unit"); f.event("e_b500", "packaging", "b500", None, "2027-02-25")   # quên ghi đầu vào
    f.lot("mix", "aggregated", 500, "kg"); f.lot("ghost", "aggregated", 200, "kg")
    f.event("e_ghost", "aggregation", "ghost", None, "2027-02-11")                                          # ghost: sự kiện không đầu vào
    f.event("e_mix", "aggregation", "mix", None, "2027-02-12", [("h1", 300, "kg"), ("ghost", 200, "kg")])
    f.evid("weighing_slip", "lot_event_id", "e_mix"); f.evid("weighing_slip", "lot_event_id", "e_ghost")
    db = SQLiteDB(f)
    r = db.one("SELECT trace_state, traced_share, untraceable_share, n_harvest_sources FROM v_lot_status WHERE lot_id='b500'")
    print("    v_integrity_issues:", [i for i in db.x("SELECT issue, subject_id FROM v_integrity_issues") if i[0] == "event_without_inputs"])
    report("B1", r[0] != "fully_traced", "lô đóng gói mà sự kiện chưa có đầu vào", f"v_lot_status = {r} (mong đợi: untraceable/không truy được, không phải fully_traced)")
    r = db.one("SELECT trace_state, traced_share, untraceable_share FROM v_lot_status WHERE lot_id='mix'")
    report("B2", r[0] != "fully_traced", "lô gộp có 40% từ lô 'ghost' (sự kiện không đầu vào)", f"v_lot_status = {r}; nguồn ghost biến mất khỏi v_lot_sources: "
           + str(db.x("SELECT source_lot_id, share, source_status FROM v_lot_sources WHERE root_lot_id='mix'")))

    # ---------- C. Lô thu hoạch làm đầu ra của sự kiện → tỷ trọng > 1 ----------
    print("\nC · Sự kiện gộp ghi đầu ra là một lô THU HOẠCH (loại lô không khớp loại sự kiện)")
    f = base_fixture()
    db = SQLiteDB(base_fixture())   # v0.5: trigger chặn ngay khi ghi → thử chèn sau khi dựng dữ liệu
    ok, err = db.ok("INSERT INTO lot_event VALUES ('e_bad','aggregation','h1',NULL,'2027-02-11','day','fac','u_fns','u_fns','%s','app',NULL)" % T)
    if ok:
        db.ok("INSERT INTO lot_input VALUES ('e_bad','h2',50,'kg','u_fns','%s')" % T)
    r = db.one("SELECT traced_share, n_harvest_sources, trace_state FROM v_lot_status WHERE lot_id='h1'")
    r2 = db.one("SELECT traced_share, trace_state FROM v_lot_status WHERE lot_id='b80'")
    iss = [x for x in db.x("SELECT issue, subject_id FROM v_integrity_issues") if x[1] in ("h1", "e_bad")]
    report("C1", not ok and num(r[0]) <= 1.0, "sự kiện ghi đầu ra là lô thu hoạch bị chặn; tỷ trọng không vượt 1",
           f"INSERT ok={ok} ({err}); H1: {r}; QR-b80: traced_share={num(r2[0])}; v_integrity_issues: {iss}")

    # ---------- D. INSERT OR REPLACE vượt append-only (SQLite) ----------
    print("\nD · Vượt append-only bằng INSERT OR REPLACE (SQLite, recursive_triggers mặc định tắt)")
    f = base_fixture()
    f.ins("verification", "v1", "bt1_r1", None, None, "u_ktv", "rejected", "field_visit", "ảnh mờ", None, None, T, T)
    db = SQLiteDB(f)
    tests = [
        ("D1", "verification rejected → verified", "INSERT OR REPLACE INTO verification VALUES ('v1','bt1_r1',NULL,NULL,'u_ktv','verified','field_visit',NULL,NULL,NULL,'%s','%s')" % (T, T),
         "SELECT result FROM verification WHERE verification_id='v1'"),
        ("D2", "cycle_anchor đổi ngày gieo không để lại lịch sử", "INSERT OR REPLACE INTO cycle_anchor VALUES ('an1','c1',1,'2026-10-01','u1','%s',NULL)" % T,
         "SELECT anchor_date, (SELECT COUNT(*) FROM cycle_anchor WHERE cycle_id='c1') FROM cycle_anchor WHERE cycle_anchor_id='an1'"),
        ("D3", "lot_input đổi khối lượng → đổi tỷ trọng QR", "INSERT OR REPLACE INTO lot_input VALUES ('e_gop','h1',4000,'kg','u_fns','%s')" % T,
         "SELECT share FROM v_lot_sources WHERE root_lot_id='b80' AND source_lot_id='h1'"),
        ("D4", "activity_revision đổi ngày làm", "INSERT OR REPLACE INTO activity_revision VALUES ('th1_r1','th1',1,'2027-01-01','day','u1',NULL,'u1','%s',NULL)" % T,
         "SELECT performed_at FROM activity_revision WHERE revision_id='th1_r1'"),
    ]
    for code, name, sql, chk in tests:
        ok, err = db.ok(sql)
        report(code, not ok, f"INSERT OR REPLACE: {name}", ("bị chặn: " + err) if not ok else f"ĐI QUA, giá trị sau: {db.one(chk)}")
    ok, err = db.ok("INSERT INTO verification VALUES ('v1','bt1_r1',NULL,NULL,'u_ktv','rejected','field_visit',NULL,NULL,NULL,'%s','%s') "
                    "ON CONFLICT(verification_id) DO UPDATE SET result='verified'" % (T, T))
    report("D5", not ok, "UPSERT ON CONFLICT DO UPDATE bị trigger UPDATE chặn", err)

    # ---------- E. closed_at sửa tự do làm đổi kết luận ----------
    print("\nE · closed_at: cột duy nhất được UPDATE, không có lịch sử")
    db = SQLiteDB(base_fixture(open_cycles=("c3",)))   # v0.5: c3 còn mở, thử đóng sớm
    before = db.one("SELECT cycle_state, n_not_recorded, n_not_due FROM v_cycle_completeness WHERE cycle_id='c3'")
    sb = db.one("SELECT complete_share FROM v_lot_status WHERE lot_id='b80'")[0]
    ok0, err0 = db.ok("UPDATE cultivation_cycle SET closed_at='2026-12-01' WHERE cycle_id='c3'")
    ok, err = db.ok("UPDATE cultivation_cycle SET closed_at='2027-02-10' WHERE cycle_id='c3'")   # đóng hợp lệ
    after = db.one("SELECT cycle_state, n_not_recorded, n_not_due FROM v_cycle_completeness WHERE cycle_id='c3'")
    sa = db.one("SELECT complete_share FROM v_lot_status WHERE lot_id='b80'")[0]
    report("E1", after[0] != "complete" and not ok0, "hộ 3 thiếu bón thúc; thử đóng chu kỳ 01/12 (trước ngày thu hoạch 10/02), rồi đóng hợp lệ 10/02",
           f"đóng 01/12: ok={ok0} ({err0}); trước {before}, complete_share={num(sb)} → sau khi đóng 10/02 (ok={ok}): {after}, complete_share={num(sa)}")
    ok, _ = db.ok("UPDATE cultivation_cycle SET closed_at=NULL WHERE cycle_id='c1'")
    report("E2", not ok, "mở lại chu kỳ đã đóng (closed_at → NULL) không cần lý do", f"UPDATE ok={ok}")
    ok, err = db.ok("UPDATE cultivation_cycle SET closed_at='2027-03-01', started_at='2026-11-01' WHERE cycle_id='c2'")
    report("E3", not ok, "UPDATE closed_at kèm started_at bị chặn", err)
    db.c.executescript("INSERT INTO cultivation_cycle VALUES ('c9','p1','cp',NULL,'ss','2027-03-01',NULL,'u_fns','%s');" % T)
    ok, err = db.ok("UPDATE cultivation_cycle SET cycle_id='c9b' WHERE cycle_id='c9'")
    report("E4", not ok, "UPDATE khóa chính cycle_id (không có trong danh sách cột trigger)", f"ok={ok} {err} (chu kỳ chưa có con → đổi được)")

    # ---------- F. Hoạt động 'conditional' thiếu minh chứng không ảnh hưởng ----------
    print("\nF · Phun thuốc (conditional) thiếu ảnh bắt buộc")
    f = base_fixture()
    f.act("ph1", "c1", "at_ph", "u1", "2027-01-15", [("m_ure", 1, "kg")])   # không có ảnh, dù er2 yêu cầu ảnh
    db = SQLiteDB(f)
    a = db.one("SELECT evidence_completeness FROM v_activity_status WHERE activity_id='ph1'")[0]
    c = db.one("SELECT cycle_state FROM v_cycle_completeness WHERE cycle_id='c1'")[0]
    ls = db.one("SELECT complete_share, chain_evidence_state FROM v_lot_status WHERE lot_id='h1'")
    report("F1", c != "complete", "chu kỳ 1 có hoạt động phun 'missing_evidence'", f"activity={a}, cycle_state={c}, QR H1 complete_share={num(ls[0])}")

    # ---------- G. Timeline ----------
    print("\nG · Digital timeline")
    f = base_fixture(open_cycles=("c2",), multi_harvest=True)
    f.ins("verification", "vlr", None, "proc_r1", None, "u_qa", "rejected", "document_review", "lab sai", None, None, "2027-02-21T00:00:00", T)
    # chu kỳ 1 thu hoạch 2 đợt (loại at_th2 tạo trong base_fixture); phun thuốc SAU đợt 1
    f.act("ph_late", "c1", "at_ph", "u1", "2027-02-15"); f.evid("photo", "activity_revision_id", "ph_late_r1")
    f.act("th1b", "c1", "at_th2", "u1", "2027-02-20"); f.lot("h1b", "harvest", 50, "kg", harvest="th1b")
    # cảm biến: số đo trong ngày đóng chu kỳ; số đo trước ngày bắt đầu; chu kỳ mở (c2 đóng NULL) + vụ sau trên cùng lô đất
    f.ins("device", "d1", "u_dev", "soil", "%", "p1", None, "u_fns", T)
    for oid, at, plot in [("o_in", "2026-12-01T06:00:00", "p1"), ("o_close", "2027-02-28T10:00:00", "p1"),
                          ("o_pre", "2026-11-01T06:00:00", "p1"), ("o_next", "2027-08-01T06:00:00", "p2")]:
        f.ins("observation", oid, "d1", at, 20, plot, None, T, "iot_gateway", oid)
    f.ins("cultivation_cycle", "c2n", "p2", "cp", None, None, "2027-07-01", None, "u_fns", T)
    # revision + xác minh bản cũ; xác minh bị thay thế
    f.ins("verification", "v_old", "bt2_r1", None, None, "u_ktv", "verified", "field_visit", None, None, None, "2026-12-06T00:00:00", T)
    f.ins("activity_revision", "bt2_r2", "bt2", 2, "2026-12-05", "day", "u2", None, "u2", T, "sửa liều")
    f.ins("verification", "vg1", None, None, "e_gop", "u_qa", "rejected", "document_review", None, None, None, "2027-02-12T10:00:00", T)
    f.ins("verification", "vg2", None, None, "e_gop", "u_ktv", "verified", "document_review", None, "vg1", "bổ sung phiếu", "2027-02-13T10:00:00", T)
    db = SQLiteDB(f)
    tl = db.x("SELECT kind, ref_id, detail, at FROM v_lot_timeline WHERE root_lot_id='b80' ORDER BY at")
    refs = {r[1] for r in tl}
    lr_rej = db.one("SELECT n_chain_rejected, chain_evidence_state FROM v_lot_status WHERE lot_id='b80'")
    report("G1", "vlr" in refs, "xác minh bản ghi LÔ (lab của PROC bị từ chối) có trong timeline",
           f"v_lot_status đếm nó (n_chain_rejected, state)={lr_rej}, nhưng timeline không có dòng 'vlr'")
    tl_h1 = db.x("SELECT kind, ref_id, at FROM v_lot_timeline WHERE root_lot_id='h1' AND kind='activity' ORDER BY at")
    report("G2", not any(r[1] in ("ph_late", "th1b") for r in tl_h1), "timeline lô thu hoạch đợt 1 chỉ chứa hoạt động trước/đến ngày thu hoạch",
           f"có cả hoạt động SAU thu hoạch: {[r for r in tl_h1 if r[1] in ('ph_late','th1b')]}")
    obs1 = {r[1] for r in db.x("SELECT kind, ref_id FROM v_lot_timeline WHERE root_lot_id='h1' AND kind='observation'")}
    report("G3", obs1 == {"o_in", "o_close"}, "số đo trong ngày đóng chu kỳ (28/02 10:00) được tính", f"observation của H1: {sorted(obs1)} (o_close bị loại do so timestamp với DATE)")
    obs2 = {r[1] for r in db.x("SELECT kind, ref_id FROM v_lot_timeline WHERE root_lot_id='h2' AND kind='observation'")}
    report("G4", "o_next" not in obs2, "chu kỳ chưa đóng không hút số đo của vụ sau trên cùng lô đất", f"observation của H2: {sorted(obs2)}")
    ver = [(r[1], r[2]) for r in tl if r[0] == "verification"]
    report("G5", ("v_old", "activity") not in ver, "xác minh của bản ghi CŨ (bt2_r1) không được trình bày như xác minh hiện hành",
           "timeline: %s; v_activity_status bt2 = %s" % (ver, db.one("SELECT verification_state FROM v_activity_status WHERE activity_id='bt2'")))
    acts = [r[1] for r in tl if r[0] == "activity"]
    report("G6", len(acts) == len(set(acts)), "hoạt động nhiều revision chỉ hiện một lần", f"{sorted(acts)}")
    total = len(tl); dupe = db.x("SELECT kind, ref_id, COUNT(*) FROM v_lot_timeline WHERE root_lot_id='b80' GROUP BY 1,2 HAVING COUNT(*)>1")
    report("G7", dupe == [], "timeline QR-b80 không trùng dòng", f"{total} dòng, trùng={dupe}")
    lot_rows = [r for r in tl if r[1] in ("raw_r2", "proc_r1")]
    report("G8", bool(lot_rows), "timeline có mốc tạo/sửa bản ghi lô (lot_revision) và minh chứng gắn lô", "không có loại 'lot_revision' — sửa khối lượng RAW không hiện trên timeline")

    # ---------- H. Lô không có sự kiện / quét QR lô thu hoạch / chu kỳ chưa có anchor ----------
    print("\nH · Trường hợp biên của v_lot_status")
    f = base_fixture()
    f.ins("plot", "p1b", "f1", "L2", 100, None, None, "u_fns", T)
    f.ins("cultivation_cycle", "cna", "p1b", "cp", None, "ss", "2026-11-15", None, "u_fns", T)   # không có anchor
    f.act("thna", "cna", "at_th", "u1", "2027-02-10"); f.evid("weighing_slip", "activity_revision_id", "thna_r1")
    f.lot("hna", "harvest", 10, "kg", harvest="thna")
    f.lot("orph", "aggregated", 10, "kg")
    db = SQLiteDB(f)
    r = db.one("SELECT trace_state, traced_share, chain_evidence_state, n_chain_events FROM v_lot_status WHERE lot_id='h1'")
    report("H1", r == ("fully_traced", 1.0, "no_post_harvest_events", 0), "quét QR lô thu hoạch trực tiếp", str(r))
    r = db.one("SELECT trace_state, traced_share, complete_share, undetermined_share FROM v_lot_status WHERE lot_id='hna'")
    cs = db.one("SELECT cycle_state FROM v_cycle_completeness WHERE cycle_id='cna'")[0]
    r1 = db.one("SELECT complete_share FROM v_lot_status WHERE lot_id='h3'")
    report("H2", num(r[3]) == 1.0, "lô từ chu kỳ chưa có anchor: v_lot_status không phân biệt 'undetermined' với 'incomplete'",
           f"hna {r} (cycle_state={cs}) vs h3 (thiếu bón thúc) complete_share={num(r1[0])} — cùng 0, không có cột undetermined_share")
    r = db.one("SELECT trace_state, untraceable_share, chain_evidence_state FROM v_lot_status WHERE lot_id='orph'")
    report("H3", r[2] != "no_post_harvest_events", "lô mồ côi (aggregated, không có sự kiện) có chain_evidence_state hợp lý", str(r))
    f = base_fixture(); f.event("e_vc", "transport", None, "raw", "2027-02-13"); f.event("e_mua", "purchase", None, "h1", "2027-02-11")
    db = SQLiteDB(f)
    r = db.x("SELECT event_id, evidence_completeness FROM v_lot_chain_events WHERE root_lot_id='b80' AND event_type IN ('transport','purchase')")
    report("H4", all(x[1] == "not_required" for x in r), "mốc thu mua/vận chuyển 0 minh chứng vẫn 'complete' (không có yêu cầu ⇒ complete)", f"{r}; không phân biệt 'không yêu cầu' với 'đủ'")

    # ---------- I. Cấu hình & thực thể gốc sửa/xóa tự do ----------
    print("\nI · Bảng không append-only làm đổi kết luận lịch sử")
    db = SQLiteDB(base_fixture())
    b = db.one("SELECT cycle_state FROM v_cycle_completeness WHERE cycle_id='c3'")[0]
    ok1, _ = db.ok("UPDATE activity_type SET requirement='optional' WHERE activity_type_id='at_bt'")
    a = db.one("SELECT cycle_state FROM v_cycle_completeness WHERE cycle_id='c3'")[0]
    report("I1", not ok1, "UPDATE activity_type.requirement (mandatory→optional) đổi kết luận chu kỳ cũ", f"ok={ok1}; c3: {b} → {a}")
    db = SQLiteDB(base_fixture())
    db.c.executescript("INSERT INTO activity VALUES ('bt3','c3','at_bt','u3','%s','app',NULL);"
                       "INSERT INTO activity_revision VALUES ('bt3_r1','bt3',1,'2026-12-05','day','u3',NULL,'u3','%s',NULL);"
                       "INSERT INTO activity_input VALUES ('bt3_r1','m_ure',1,'kg');" % (T, T))
    b = db.one("SELECT evidence_completeness FROM v_activity_status WHERE activity_id='bt3'")[0]
    ok2, _ = db.ok("DELETE FROM evidence_requirement WHERE requirement_id='er1'")
    a = db.one("SELECT evidence_completeness FROM v_activity_status WHERE activity_id='bt3'")[0]
    report("I2", not ok2, "DELETE evidence_requirement biến 'missing_evidence' thành 'complete'", f"ok={ok2}; bt3: {b} → {a}")
    ok3, _ = db.ok("UPDATE plot SET farm_id='f2', code='L9' WHERE plot_id='p1'")
    fr = db.one("SELECT p.farm_id FROM lot l JOIN activity a ON a.activity_id=l.harvest_activity_id JOIN cultivation_cycle c ON c.cycle_id=a.cycle_id JOIN plot p ON p.plot_id=c.plot_id WHERE l.lot_id='h1'")
    report("I3", not ok3, "UPDATE plot.farm_id đổi 'sản phẩm từ farm nào' của lô cũ", f"ok={ok3}; H1 giờ thuộc {fr}")
    ok4, _ = db.ok("UPDATE certification SET valid_to='2030-01-01'") ; ok4b, _ = db.ok("UPDATE farm SET owner_agent_id='u2' WHERE farm_id='f1'")
    report("I4", not ok4b, "UPDATE farm.owner_agent_id không để lại lịch sử", f"ok={ok4b}")

    # ---------- J. Minh chứng trùng nội dung ----------
    print("\nJ · Một file tải lên 2 lần (cùng sha256) đếm là 2 minh chứng")
    f = base_fixture(er1_min=2)
    f.act("bt3", "c3", "at_bt", "u3", "2026-12-05", [("m_ure", 1, "kg")])
    f.evid("photo", "activity_revision_id", "bt3_r1", sha="SAME"); f.evid("photo", "activity_revision_id", "bt3_r1", sha="SAME")
    db = SQLiteDB(f)
    r = db.one("SELECT evidence_completeness FROM v_activity_status WHERE activity_id='bt3'")[0]
    report("J1", r != "complete", "min_count=2 thỏa bằng 2 bản ghi cùng sha256", f"bt3 = {r}")

    # ---------- K. Cân bằng khối lượng / thứ tự thời gian / sửa đồ thị về sau ----------
    print("\nK · Tính đúng của chuỗi lô")
    f = base_fixture()
    f.lot("b1l", "packaged", 300, "unit"); f.event("e_b1l", "packaging", "b1l", None, "2027-02-22", [("proc", 300, "l")])   # 200+200+300 > 400 l
    f.lot("early", "packaged", 10, "unit"); f.event("e_early", "packaging", "early", None, "2027-01-01", [("proc", 5, "l")])  # đóng chai trước khi ép
    db = SQLiteDB(f)
    used = db.one("SELECT SUM(quantity_used) FROM lot_input WHERE input_lot_id='proc'")[0]
    iss = db.x("SELECT issue, subject_id FROM v_integrity_issues")
    report("K1", any("balance" in i[0] or "over" in i[0] for i in iss), "dùng quá khối lượng lô PROC được phát hiện", f"đã dùng {used} l / 400 l; v_integrity_issues={iss}")
    report("K2", any("time" in i[0] for i in iss), "đóng chai (01/01) trước khi ép dầu (20/02) được phát hiện", "không có kiểm tra thứ tự thời gian")
    db = SQLiteDB(base_fixture())
    b = num(db.one("SELECT share FROM v_lot_sources WHERE root_lot_id='b80' AND source_lot_id='h1'")[0])
    db.c.executescript("INSERT INTO agent VALUES ('u4','person','Hộ 4','farmer',NULL,'%s');" % T)
    ok, err = db.ok("INSERT INTO lot_input VALUES ('e_ep','h1',1000,'kg','u_fns','%s')" % T)
    a = num(db.one("SELECT share FROM v_lot_sources WHERE root_lot_id='b80' AND source_lot_id='h1'")[0])
    cols = [r[1] for r in db.x("PRAGMA table_info(lot_input)")]
    report("K3", not ok, "thêm đầu vào vào sự kiện ép dầu ĐÃ xong, sau khi chai đã bán (đổi tỷ trọng QR hồi tố)",
           f"ok={ok}; tỷ trọng H1 của QR-b80: {b} → {a}; lot_input không có recorded_by/recorded_at: cột={cols}")

    # ---------- L. Trigger chu kỳ / anchor trên SQLite ----------
    print("\nL · Mốc lịch")
    db = SQLiteDB(base_fixture())
    ok, err = db.ok("INSERT INTO cycle_anchor VALUES ('anx','c1',5,'2026-11-25','u1','2020-01-01T00:00:00','nhảy số')")
    report("L1", not ok, "anchor revision nhảy cóc (1→5) và recorded_at lùi về 2020", f"ok={ok}")
    db.c.executescript("INSERT INTO activity VALUES ('bt_pre','c2','at_bt','u2','%s','app',NULL);"
                       "INSERT INTO activity_revision VALUES ('bt_pre_r1','bt_pre',1,'2025-01-01','day','u2',NULL,'u2','%s',NULL);" % (T, T))
    n = db.one("SELECT COUNT(*) FROM v_lot_timeline WHERE root_lot_id='h2' AND ref_id='bt_pre'")[0]
    n = n if not any(i[0] == "activity_before_cycle_start" and i[1] == "bt_pre" for i in db.x("SELECT issue, subject_id FROM v_integrity_issues")) else 0
    report("L2", n == 0, "hoạt động ghi ngày 2025 (trước started_at chu kỳ 15/11/2026) vẫn nhận", f"được ghi và hiện trên timeline ({n} dòng), không có cảnh báo")
    ok, err = db.ok("INSERT INTO activity VALUES ('imp1','c1','at_ph','u1','%s','import',NULL)" % T)
    report("L3", not ok, "bản ghi kênh 'import' không có external_ref (không chống nạp trùng được)", f"ok={ok}")


def run_new_v05():
    """Ca thử MỚI nhắm vào chính các bản sửa v0.5."""
    print("\n=== RV · Lỗi mới do bản sửa v0.5 (SQLite) — mã RV để không trùng N1–N30 của smoke_test ===")
    T2 = "2027-03-15T08:00:00"
    # RV1/N2: config append-only nhưng INSERT thêm luật vẫn đổi kết luận hồi tố
    db = SQLiteDB(base_fixture())
    b = (db.one("SELECT evidence_completeness FROM v_activity_status WHERE activity_id='bt1'")[0],
         num(db.one("SELECT complete_share FROM v_lot_status WHERE lot_id='b80'")[0]))
    ok = db.ok("INSERT INTO evidence_requirement VALUES ('er_sig','at_bt',NULL,'signature',1,'luật mới 2027',0)")[0]
    a = (db.one("SELECT evidence_completeness FROM v_activity_status WHERE activity_id='bt1'")[0],
         num(db.one("SELECT complete_share FROM v_lot_status WHERE lot_id='b80'")[0]))
    report("RV1", not ok or a == b, "thêm evidence_requirement mới làm đổi trạng thái hoạt động của chu kỳ ĐÃ ĐÓNG",
           f"INSERT ok={ok}; bt1 (đóng 28/02) & complete_share QR-b80: {b} → {a}")
    db = SQLiteDB(base_fixture())
    b = db.x("SELECT cycle_id, cycle_state FROM v_cycle_completeness WHERE cycle_id IN ('c1','c2') ORDER BY 1")
    ok = db.ok("INSERT INTO activity_type VALUES ('at_new','st1','TOP_DRESS_2','Bón thúc 2','mandatory',30,3,0,1,NULL,'detail','luật mới',0)")[0]
    a = db.x("SELECT cycle_id, cycle_state FROM v_cycle_completeness WHERE cycle_id IN ('c1','c2') ORDER BY 1")
    report("RV2", not ok or a == b, "thêm activity_type bắt buộc vào giai đoạn đang dùng làm chu kỳ cũ thành 'incomplete'",
           f"INSERT ok={ok}; {b} → {a}")
    # RV3: ghi hoạt động SAU khi chu kỳ đã đóng
    db = SQLiteDB(base_fixture())
    ok1 = db.ok("INSERT INTO activity VALUES ('late','c1','at_ph','u1','%s','app',NULL)" % T2)[0]
    ok2 = db.ok("INSERT INTO activity_revision VALUES ('late_r1','late',1,'2027-03-10','day','u1',NULL,'u1','%s',NULL)" % T2)[0]
    ok3 = db.ok("INSERT INTO activity_revision VALUES ('th1_r2','th1',2,'2027-03-12','day','u1',NULL,'u1','%s','sửa ngày')" % T2)[0]
    iss = [i for i in db.x("SELECT issue, subject_id FROM v_integrity_issues") if i[1] in ("late", "th1", "c1")]
    report("RV3", not (ok2 or ok3) or bool(iss), "chu kỳ đóng 28/02 vẫn nhận hoạt động/bản sửa ngày 10–12/03 (vượt bất biến closed_at ≥ hoạt động cuối)",
           f"activity ok={ok1}, revision ok={ok2}, sửa ngày thu hoạch ok={ok3}; v_integrity_issues={iss}")
    # RV4: bản ghi CŨ có ngày sai chặn việc đóng chu kỳ
    db = SQLiteDB(base_fixture(open_cycles=("c2",)))
    db.c.executescript("INSERT INTO activity_revision VALUES ('th2_r2','th2',2,'2027-03-05','day','u2',NULL,'u2','%s','gõ nhầm');"
                       "INSERT INTO activity_revision VALUES ('th2_r3','th2',3,'2027-02-10','day','u2',NULL,'u2','%s','sửa lại đúng');" % (T, T))
    ok, err = db.ok("UPDATE cultivation_cycle SET closed_at='2027-02-28' WHERE cycle_id='c2'")
    report("RV4", ok, "đóng chu kỳ khi chỉ bản ghi CŨ (đã sửa) có ngày sau closed_at", f"ok={ok} {err} — trigger xét mọi revision, không chỉ bản hiện hành")
    db2 = SQLiteDB(base_fixture(open_cycles=("c2",)))
    db2.ok("UPDATE cultivation_cycle SET closed_at='2027-02-10' WHERE cycle_id='c2'")
    ok, err = db2.ok("UPDATE cultivation_cycle SET closed_at='2027-02-20' WHERE cycle_id='c2'")
    report("RV5", ok, "đóng nhầm ngày thì không có cách sửa có lý do (không có bảng lịch sử đóng)", f"ok={ok} {err}")
    # RV6: QA từ chối sự kiện gộp vì thiếu một phiếu đầu vào → không thể bổ sung đầu vào
    f = base_fixture()
    f.lot("raw2", "aggregated", 20, "kg"); f.event("e_g2", "aggregation", "raw2", None, "2027-02-12", [("h1", 10, "kg")])
    f.evid("weighing_slip", "lot_event_id", "e_g2")
    f.ins("verification", "vrej", None, None, "e_g2", "u_qa", "rejected", "document_review", "thiếu lô hộ 2", None, None, T, T)
    db = SQLiteDB(f)
    ok, err = db.ok("INSERT INTO lot_input VALUES ('e_g2','h2',10,'kg','u_fns','%s')" % T)
    report("RV6", ok, "bổ sung đầu vào sau khi xác minh 'rejected' (luồng sửa hợp lệ)", f"ok={ok} ({err}) — chặn cả khi kết luận là từ chối")
    # RV7: K3 còn hở ở lô LÁ (lô chai không được dùng tiếp, sự kiện chưa xác minh)
    f = base_fixture()
    f.lot("proc2", "processed", 400, "l"); f.event("e_ep2", "transformation", "proc2", None, "2027-02-20", [("h1", 100, "kg")])
    f.evid("photo", "lot_event_id", "e_ep2")
    db = SQLiteDB(f)
    b = num(db.one("SELECT share FROM v_lot_sources WHERE root_lot_id='b80' AND source_lot_id='h1'")[0])
    ok, err = db.ok("INSERT INTO lot_input VALUES ('e_b80','proc2',200,'l','u_fns','2027-06-01T00:00:00')")
    a = num(db.one("SELECT share FROM v_lot_sources WHERE root_lot_id='b80' AND source_lot_id='h1'")[0])
    iss = [i for i in db.x("SELECT issue, subject_id FROM v_integrity_issues") if i[1] in ("e_b80", "b80")]
    report("RV7", not ok, "thêm đầu vào vào sự kiện ĐÓNG CHAI (lô lá) 3 tháng sau, khi QR đã lưu hành",
           f"ok={ok}; tỷ trọng H1 của QR-b80: {b} → {a}; v_integrity_issues={iss}")
    # RV8: nạp lại idempotent (INSERT OR IGNORE / ON CONFLICT DO NOTHING) bị trigger T0 làm lỗi
    db = SQLiteDB(base_fixture())
    db.c.executescript("INSERT INTO device VALUES ('d1','u_dev','soil','%%','p1',NULL,'u_fns','%s');"
                       "INSERT INTO observation VALUES ('o1','d1','2026-12-01T06:00:00',20,'p1',NULL,'%s','import','GW-1');" % (T, T))
    ok1, e1 = db.ok("INSERT OR IGNORE INTO observation VALUES ('o1','d1','2026-12-01T06:00:00',20,'p1',NULL,'%s','import','GW-1')" % T)
    ok2, e2 = db.ok("INSERT INTO observation VALUES ('o1b','d1','2026-12-01T06:00:00',20,'p1',NULL,'%s','import','GW-1') ON CONFLICT DO NOTHING" % T)
    report("RV8", ok1 and ok2, "nạp lại cùng mã ngoài bằng INSERT OR IGNORE / ON CONFLICT DO NOTHING (import idempotent)",
           f"OR IGNORE ok={ok1} ({e1}); ON CONFLICT DO NOTHING ok={ok2} ({e2}); trên PG câu thứ hai chạy được → hai hệ khác hành vi")
    # RV10: sha256 khác hoa/thường → J1 lách được
    f = base_fixture(er1_min=2)
    f.act("bt3", "c3", "at_bt", "u3", "2026-12-05", [("m_ure", 1, "kg")])
    f.evid("photo", "activity_revision_id", "bt3_r1", sha="abcdef"); f.evid("photo", "activity_revision_id", "bt3_r1", sha="ABCDEF")
    db = SQLiteDB(f)
    r = db.one("SELECT evidence_completeness FROM v_activity_status WHERE activity_id='bt3'")[0]
    report("RV10", r != "complete", "cùng file, sha256 viết hoa/thường khác nhau, đếm thành 2", f"bt3 = {r}; sha256 không CHECK định dạng (64 ký tự hex thường)")
    # RV11: bản ghi trùng của hoạt động BẮT BUỘC thiếu minh chứng không bị n_other_problem bắt
    f = base_fixture()
    f.act("bt1_dup", "c1", "at_bt", "u1", "2026-12-06", [("m_ure", 5, "kg")])   # lần ghi thứ 2, không ảnh
    db = SQLiteDB(f)
    r = db.one("SELECT evidence_completeness FROM v_activity_status WHERE activity_id='bt1_dup'")[0]
    c = db.one("SELECT cycle_state, n_other_problem FROM v_cycle_completeness WHERE cycle_id='c1'")
    report("RV11", c[0] != "complete", "lần ghi thứ 2 của hoạt động bắt buộc thiếu ảnh", f"bt1_dup={r}; c1={c} (chỉ bản ghi đầu tiên được xét; n_other_problem lọc requirement<>'mandatory')")
    # RV12: thông tin công khai của farm/plot vẫn sửa tự do
    db = SQLiteDB(base_fixture())
    ok1 = db.ok("UPDATE farm SET name='Hộ khác', province='Bình Thuận', commune='X' WHERE farm_id='f1'")[0]
    ok2 = db.ok("UPDATE plot SET geo_point='10.9,108.1', area_m2=1, growing_area_code='VG-999' WHERE plot_id='p1'")[0]
    report("RV12", not (ok1 or ok2), "đổi tỉnh/xã/tên hộ, toạ độ, mã vùng trồng của lô đất đã sinh lô (trang QR đổi theo)",
           f"farm UPDATE ok={ok1}, plot UPDATE ok={ok2}; không có lịch sử")
    # RV13: timeline đặt 'lot_created' theo recorded_at (giờ ghi/nạp), không theo thời điểm nghiệp vụ
    db = SQLiteDB(base_fixture())
    tl = db.x("SELECT at, kind, ref_id, detail FROM v_lot_timeline WHERE root_lot_id='b80' ORDER BY at")
    pos = [i for i, r in enumerate(tl) if r[2] == "b80_r1"][0]; pev = [i for i, r in enumerate(tl) if r[2] == "e_b80"][0]
    report("RV13", pos >= pev, "mốc 'lot_created' của QR-b80 nằm sau sự kiện đóng chai tạo ra nó",
           f"lot_created at={tl[pos][0]} (vị trí {pos}) trước cả hoạt động canh tác; đóng chai at={tl[pev][0]} (vị trí {pev}) — dữ liệu import/backfill sẽ dồn về ngày nạp")
    # RV14 (nhóm tự phát hiện, 28/11): cùng loại RV1 nhưng yêu cầu theo LOẠI SỰ KIỆN LÔ — không gắn crop profile nên lọt f_config_in_use
    db = SQLiteDB(base_fixture())
    sel = "SELECT lot_id, chain_evidence_state FROM v_lot_status WHERE lot_id IN ('b80','b250') ORDER BY 1"
    b = db.x(sel)
    ok = db.ok("INSERT INTO evidence_requirement VALUES ('er_pack',NULL,'packaging','photo',1,'luật mới 2027',0)")[0]
    a = db.x(sel)
    report("RV14", not ok or a == b, "thêm yêu cầu minh chứng cho loại sự kiện 'packaging' làm đổi trạng thái chai ĐÃ IN QR",
           f"INSERT ok={ok}; {b} → {a}")
    # RV15 (nhóm tự phát hiện, 28/11): luật cách ly thêm SAU thu hoạch đổi kết luận PHI, không để lại dấu thời điểm thêm
    f = base_fixture()
    f.ins("input_material", "m_y", "pesticide", "Thuốc Y", None, None, "l")
    f.act("ph1", "c1", "at_ph", "u1", "2027-02-05", [("m_y", 1, "l")])   # phun 5 ngày trước thu hoạch 10/02, chưa có luật cho mè
    f.evid("photo", "activity_revision_id", "ph1_r1")
    db = SQLiteDB(f)
    cnt = ("SELECT (SELECT COUNT(*) FROM v_phi_violations),"
           " (SELECT COUNT(*) FROM v_integrity_issues WHERE issue='missing_phi_rule')")
    b = db.one(cnt)
    ok = db.ok("INSERT INTO material_crop_rule VALUES ('m_y','SESAME',0,'bổ sung sau thu hoạch',1)")[0]   # luật lỏng
    a = db.one(cnt)
    report("RV15", not ok or a == b, "thêm luật cách ly (phi_days=0) cho thuốc đã phun sau khi vụ thu hoạch: cảnh báo 'thiếu luật' biến mất, không vi phạm, không dấu vết",
           f"INSERT ok={ok}; (vi phạm, thiếu luật): {tuple(b)} → {tuple(a)}; luật không có recorded_at")


def run_pg():
    print("\n=== Trigger PostgreSQL ===")
    db = Postgres()   # xóa + tạo lại PGDATABASE (*_test), nạp schema + trigger + view
    print(f"  PostgreSQL OK ({db.dbname})")

    def pg(sql):
        try:
            return True, db._psql(db.dbname, sql).strip()
        except DBError as e:
            return False, str(e).strip()
    ok, out = pg(base_fixture().text())
    if not ok:
        print("  nạp dữ liệu nền lỗi:", out[:300]); return
    cases = [
        ("P1", "variety_id NULL → giá trị (ROW IS DISTINCT FROM với NULL)", "UPDATE cultivation_cycle SET variety_id=NULL WHERE cycle_id='c1'", True),
    ]
    pg("INSERT INTO variety VALUES ('v1','SESAME','Mè đen',NULL,NULL);")
    for code, name, sql, _ in [
        ("P1", "variety_id NULL → 'v1'", "UPDATE cultivation_cycle SET variety_id='v1' WHERE cycle_id='c1'", None),
        ("P2", "season_id 'ss' → NULL", "UPDATE cultivation_cycle SET season_id=NULL WHERE cycle_id='c2'", None),
        ("P3", "closed_at + started_at cùng lúc", "UPDATE cultivation_cycle SET closed_at='2027-03-01', started_at='2026-11-01' WHERE cycle_id='c1'", None)]:
        ok, out = pg(sql)
        report(code, not ok, f"PG chặn UPDATE {name}", out.splitlines()[0] if out else "ĐI QUA")
    ok, out = pg("UPDATE cultivation_cycle SET variety_id=NULL WHERE cycle_id='c3';")
    report("P4", ok, "PG cho UPDATE NULL→NULL (không đổi) — không chặn nhầm", out or "ok")
    ok, out = pg("INSERT INTO cultivation_cycle VALUES ('c9','p1','cp',NULL,'ss','2027-03-01',NULL,'u_fns','%s'); UPDATE cultivation_cycle SET cycle_id='c9b' WHERE cycle_id='c9';" % T)
    report("P5", not ok, "PG: đổi khóa chính cycle_id (ngoài danh sách so sánh ROW)", out or "ĐI QUA")
    ok, out = pg("INSERT INTO verification VALUES ('v1','bt1_r1',NULL,NULL,'u_ktv','rejected','field_visit',NULL,NULL,NULL,now(),now()) "
                 "ON CONFLICT (verification_id) DO UPDATE SET result='verified';"
                 "INSERT INTO verification VALUES ('v1','bt1_r1',NULL,NULL,'u_ktv','rejected','field_visit',NULL,NULL,NULL,now(),now()) "
                 "ON CONFLICT (verification_id) DO UPDATE SET result='verified';")
    report("P6", not ok, "PG: UPSERT trên bảng append-only bị chặn", out.splitlines()[-1] if out else "ĐI QUA")
    ok, out = pg("INSERT INTO device VALUES ('d1','u_dev','soil','%','p1',NULL,'u_fns',now());"
                 "INSERT INTO observation VALUES ('o_close','d1','2027-02-28 10:00:00',20,'p1',NULL,now(),'iot_gateway','x');"
                 "INSERT INTO observation VALUES ('o_in','d1','2026-12-01 06:00:00',20,'p1',NULL,now(),'iot_gateway','y');"
                 "INSERT INTO observation VALUES ('o_out','d1','2027-03-05 06:00:00',20,'p1',NULL,now(),'iot_gateway','z');")
    a = pg("SELECT string_agg(ref_id, ',' ORDER BY ref_id) FROM v_lot_timeline WHERE root_lot_id='h1' AND kind='observation';")
    b = pg("SET datestyle='SQL, DMY'; SELECT string_agg(ref_id, ',' ORDER BY ref_id) FROM v_lot_timeline WHERE root_lot_id='h1' AND kind='observation';")
    report("P8", a == b, "PG: timeline không phụ thuộc DateStyle của phiên (view so ngày bằng kiểu DATE)", f"ISO: {a} số đo; 'SQL, DMY': {b} số đo")
    ok, out = pg("INSERT INTO observation VALUES ('o2','d1','2026-12-02 06:00:00',20,'p1',NULL,now(),'import','GW-1');"
                 "INSERT INTO observation VALUES ('o2b','d1','2026-12-02 06:00:00',20,'p1',NULL,now(),'import','GW-1') ON CONFLICT DO NOTHING;")
    report("P9", ok, "PG: nạp lại idempotent ON CONFLICT DO NOTHING (đối chiếu N8)", out or "ok")
    ok, out = pg("TRUNCATE verification;")
    report("P7", not ok, "PG: TRUNCATE bảng append-only (trigger mức dòng không bắt TRUNCATE)", out or "ĐI QUA — cần REVOKE TRUNCATE / trigger BEFORE TRUNCATE")


def run_perf(n_farms=200, n_lots=2000):
    print(f"\n=== Hiệu năng SQLite: {n_farms} hộ, ~{n_lots} lô ===")
    random.seed(1)
    f = base_fixture(n_farms=n_farms)
    for i in range(1, n_farms + 1):
        f.ins("agent", f"ud{i}", "device", "dev", "system", None, T)
        f.ins("device", f"d{i}", f"ud{i}", "soil", "%", f"p{i}", None, "u_fns", T)
        for k in range(20):
            f.ins("observation", f"o{i}_{k}", f"d{i}", f"2026-12-{(k % 28) + 1:02d}T06:00:00", 20, f"p{i}", None, T, "iot_gateway", None)
    lots = [f"h{i}" for i in range(1, n_farms + 1)]
    made = n_farms; layer = 0; e = 0
    # các tầng: gộp 10 hộ → 1 lô RAW; ép → PROC; đóng 2 loại chai; cho tới đủ n_lots
    raws = []
    for g in range(0, n_farms, 10):
        e += 1; lid = f"raw{e}"; f.lot(lid, "aggregated", 1000, "kg")
        f.event(f"eg{e}", "aggregation", lid, None, "2027-02-12", [(h, 100, "kg") for h in lots[g:g + 10]])
        f.evid("weighing_slip", "lot_event_id", f"eg{e}"); raws.append(lid); made += 1
    procs = []
    j = 0
    while made < n_lots:
        j += 1
        ins_ = random.sample(raws, 2)
        pid = f"pr{j}"; f.lot(pid, "processed", 400, "l")
        f.event(f"ep{j}", "transformation", pid, None, "2027-02-20", [(r_, 500, "kg") for r_ in ins_]); f.evid("photo", "lot_event_id", f"ep{j}")
        made += 1; procs.append(pid)
        for b in range(4):
            if made >= n_lots: break
            bid = f"bt{j}_{b}"; f.lot(bid, "packaged", 1000, "unit")
            f.event(f"eb{j}_{b}", "packaging", bid, None, "2027-02-22", [(pid, 80, "l")]); made += 1
    db = SQLiteDB(f)
    nl = db.one("SELECT COUNT(*) FROM lot")[0]; no = db.one("SELECT COUNT(*) FROM observation")[0]
    print(f"  dữ liệu: {nl} lô, {db.one('SELECT COUNT(*) FROM lot_event')[0]} sự kiện, {db.one('SELECT COUNT(*) FROM activity')[0]} hoạt động, {no} số đo")
    target = "bt1_0"
    for name, sql in [
        ("v_lot_sources (1 lô)", f"SELECT * FROM v_lot_sources WHERE root_lot_id='{target}'"),
        ("v_lot_chain_events (1 lô)", f"SELECT * FROM v_lot_chain_events WHERE root_lot_id='{target}'"),
        ("v_lot_status (1 lô)", f"SELECT * FROM v_lot_status WHERE lot_id='{target}'"),
        ("v_lot_timeline (1 lô)", f"SELECT * FROM v_lot_timeline WHERE root_lot_id='{target}' ORDER BY at"),
        ("v_cycle_completeness (1 chu kỳ)", "SELECT * FROM v_cycle_completeness WHERE cycle_id='c1'"),
    ]:
        t0 = time.perf_counter(); rows = db.x(sql); dt = time.perf_counter() - t0
        print(f"  {name:34s} {dt*1000:9.1f} ms   ({len(rows)} dòng)")
    t0 = time.perf_counter()
    rows = db.x(f"""WITH RECURSIVE src(lot_id, share, depth) AS (SELECT '{target}', 1.0, 0 UNION ALL
        SELECT li.input_lot_id, s.share*li.quantity_used/(SELECT SUM(quantity_used) FROM lot_input x WHERE x.event_id=ev.event_id), s.depth+1
        FROM src s JOIN lot_event ev ON ev.output_lot_id=s.lot_id JOIN lot_input li ON li.event_id=ev.event_id WHERE s.depth<20)
        SELECT lot_id, SUM(share) FROM src GROUP BY lot_id""")
    print(f"  {'truy ngược có tham số (CTE gieo 1 lô)':34s} {(time.perf_counter()-t0)*1000:9.1f} ms   ({len(rows)} dòng) — để so sánh")


if __name__ == "__main__":
    sys.argv = setup_output(sys.argv)
    mode = sys.argv[1] if len(sys.argv) > 1 else "sqlite"
    if mode == "perf":
        run_perf(*(int(x) for x in sys.argv[2:4]))
    else:
        run_sqlite()
        run_new_v05()
        if mode == "pg":
            run_pg()
        open_ = [c for c in findings if c not in KNOWN_LIMITS]
        known = [c for c in findings if c in KNOWN_LIMITS]
        print(f"\nTổng: {len(findings)} phát hiện ({len(open_)} chưa xử lý, {len(known)} đã ghi giới hạn), {len(oks)} ca đứng vững")
        print("Chưa xử lý:", ", ".join(open_) or "—")
        for c in known:
            print(f"Đã ghi giới hạn: {c} — {KNOWN_LIMITS[c]}")
