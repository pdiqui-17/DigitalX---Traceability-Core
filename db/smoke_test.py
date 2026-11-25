"""Kiểm tra schema v0.5 — chạy cùng một bộ dữ liệu trên SQLite và PostgreSQL.

    python3 smoke_test.py sqlite
    python3 smoke_test.py postgres     # cần PostgreSQL tạm: ./pg_load.sh (dùng socket /tmp/pg, cổng 5544)

Nhóm kiểm tra:
  F  — chức năng (trạng thái, độ đầy đủ, truy ngược/xuôi, cách ly, cảm biến, chứng nhận)
  R  — hồi quy cho các lỗi bên đánh giá đã tái hiện (R0–R5, D1–D3)
  C  — ràng buộc và trigger phải chặn dữ liệu sai
"""
import sqlite3, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).parent
DIALECT = sys.argv[1] if len(sys.argv) > 1 else "sqlite"
T = "2026-11-25T08:00:00"

class DBError(Exception):
    pass

class SQLite:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        for f in ("schema.sql", "triggers_sqlite.sql", "views_sqlite.sql"):
            self.db.executescript((HERE / f).read_text(encoding="utf-8"))
    def run(self, sql):
        try:
            return [tuple(r) for r in self.db.execute(sql).fetchall()]
        except (sqlite3.IntegrityError, sqlite3.OperationalError) as e:
            raise DBError(str(e))

class Postgres:
    CMD = ["psql", "-h", "/tmp/pg", "-p", "5544", "-U", "postgres", "-d", "postgres",
           "-v", "ON_ERROR_STOP=1", "-tA", "-F", "\x1f", "-q"]
    def __init__(self):
        r = subprocess.run([str(HERE / "pg_load.sh")], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("Không nạp được PostgreSQL:\n" + r.stdout + r.stderr)
    def run(self, sql):
        r = subprocess.run(self.CMD, input=sql, capture_output=True, text=True)
        if r.returncode != 0:
            raise DBError(r.stderr.strip())
        rows = []
        for line in r.stdout.splitlines():
            if line == "":
                continue
            rows.append(tuple(None if v == "" else v for v in line.split("\x1f")))
        return rows

db = SQLite() if DIALECT == "sqlite" else Postgres()

def q(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"

def ins(table, *vals):
    if table == "lot_input" and len(vals) == 4:      # v0.5: cạnh lô có người ghi / lúc ghi
        vals = vals + ("u_fns", T)
    db.run(f"INSERT INTO {table} VALUES ({', '.join(q(v) for v in vals)})")

def num(v):
    return None if v is None else round(float(v), 3)

results = []
def check(code, name, ok, detail=""):
    results.append((code, ok))
    print(f"  [{'ĐẠT' if ok else 'LỖI'}] {code} {name}" + (f" — {detail}" if detail else ""))

EXPECT = {"check": ("CHECK constraint failed", "violates check constraint"),
          "unique": ("UNIQUE constraint failed", "duplicate key", "trùng khóa"),
          "fk": ("FOREIGN KEY constraint failed", "violates foreign key"),
          "notnull": ("NOT NULL constraint failed", "violates not-null")}

def blocked(code, name, sql, expect):
    """Phải bị chặn VÀ đúng lý do (tránh đạt giả do sai số cột, sai cú pháp...)."""
    try:
        db.run(sql)
        check(code, f"chặn: {name}", False, "KHÔNG bị chặn")
    except DBError as e:
        msg = str(e).splitlines()[0].replace("ERROR:  ", "")
        ok = any(k in msg for k in EXPECT.get(expect, (expect,)))
        check(code, f"chặn: {name}", ok, msg[:90] if ok else f"bị chặn SAI LÝ DO: {msg[:90]}")

# ====================================================================
# Dữ liệu
# ====================================================================
for a in [("u_a","person","Hộ A","farmer"), ("u_b","person","Hộ B","farmer"), ("u_c","person","Hộ C","farmer"),
          ("u_ktv","person","Kỹ thuật viên","technician"), ("u_ktv2","person","Kỹ thuật viên 2","verifier"),
          ("u_fns","organization","F&S","company"), ("u_qa","person","QA F&S","company"),
          ("u_cert","organization","Tổ chức chứng nhận","certifier"), ("u_dev","device","Cảm biến ẩm đất","system")]:
    ins("agent", *a, None, T)
ins("facility", "fac_tm", "Điểm thu mua Lương Hòa", "collection_point", "u_fns", "Tây Ninh", "Lương Hòa", None)
ins("facility", "fac_nm", "Nhà máy F&S", "processing_plant", "u_fns", "Tây Ninh", "Lương Hòa", None)

ins("crop_profile", "cp_me", "SESAME", "Mè đen 2 vỏ", 1, "sowing", '{"oil_content_pct":"number"}', "QT Bình Thuận", "2026-01-01")
ins("variety", "v_me", "SESAME", "Mè đen Bình Thuận", "{}", "thuộc tính chưa xác minh")
ins("stage", "st_cs", "cp_me", 3, "Chăm sóc")
ins("stage", "st_th", "cp_me", 4, "Thu hoạch")
# activity_type: id, stage, code, name, requirement, offset, tolerance, produces_lot, uses_inputs, attr_schema, public, source, assumption
ins("activity_type", "at_bt", "st_cs", "TOP_DRESS_1", "Bón thúc 1", "mandatory", 15, 3, 0, 1, None, "detail", "QT Bình Thuận mục 6", 0)
ins("activity_type", "at_phun", "st_cs", "SPRAY", "Phun thuốc", "conditional", None, 0, 0, 1, None, "detail", "QT Bình Thuận mục 9", 0)
ins("activity_type", "at_th", "st_th", "HARVEST", "Thu hoạch", "mandatory", 80, 7, 1, 0, None, "summary", "giả định nhóm", 1)
ins("evidence_requirement", "er1", "at_bt", None, "photo", 1, "giả định nhóm", 1)
ins("evidence_requirement", "er2", "at_phun", None, "photo", 1, "giả định nhóm", 1)
ins("evidence_requirement", "er3", "at_th", None, "weighing_slip", 1, "giả định nhóm", 1)
ins("evidence_requirement", "er4", None, "aggregation", "weighing_slip", 1, "giả định nhóm", 1)
ins("input_material", "m_ure", "fertilizer", "Urê", "N", None, "kg")
ins("input_material", "m_x", "pesticide", "Thuốc X", "Hoạt chất X", "REG-X", "ml")
ins("input_material", "m_y", "pesticide", "Thuốc Y", "Hoạt chất Y", "REG-Y", "ml")
ins("material_crop_rule", "m_x", "SESAME", 7, "giả định nhóm — cần đối chiếu nhãn", 1)
ins("material_crop_rule", "m_y", "PEANUT", 5, "giả định nhóm — cần đối chiếu nhãn", 1)   # chưa có luật cho mè

ins("season", "ss_dx", "u_fns", "Đông Xuân 2026–2027", "SESAME", "2026-11-01", "2027-03-31", "u_fns", T)
for k in "abc":
    ins("farm", f"f{k}", f"u_{k}", f"Hộ {k.upper()}", "Tây Ninh", "Lương Hòa", None, "u_fns", T)
    ins("plot", f"p{k}", f"f{k}", "L1", 5000, None, None, "u_fns", T)
    ins("cultivation_cycle", f"c{k}", f"p{k}", "cp_me", "v_me", "ss_dx", "2026-11-15", "2027-02-28", "u_fns", T)
    ins("cycle_anchor", f"an_{k}1", f"c{k}", 1, "2026-11-20", f"u_{k}", T, None)
ins("plot", "pc2", "fc", "L2", 3000, None, None, "u_fns", T)
ins("cultivation_cycle", "cc2", "pc2", "cp_me", "v_me", "ss_dx", "2026-11-15", None, "u_fns", T)   # chưa có ngày gieo

n = [0]
def evidence(kind, col, target, obs=None, by="u_fns"):
    n[0] += 1; eid = f"ev{n[0]}"
    if kind == "sensor":
        ins("evidence", eid, kind, None, None, obs, None, None, by, T, "iot_gateway", f"GW-EV-{eid}")
    else:
        ins("evidence", eid, kind, f"s3://{eid}", f"sha{eid}", None, None, None, by, T, "app", None)
    if col:
        db.run(f"INSERT INTO evidence_link (link_id, evidence_id, {col}, linked_by, linked_at) "
               f"VALUES ({q('l'+eid)}, {q(eid)}, {q(target)}, {q(by)}, {q(T)})")
    return eid

def activity(aid, cycle, atype, who, when, inputs=()):
    ins("activity", aid, cycle, atype, who, T, "app", None)
    ins("activity_revision", aid + "_r1", aid, 1, when, "day", who, None, who, T, None)
    for m, qty, u in inputs:
        ins("activity_input", aid + "_r1", m, qty, u)
    return aid + "_r1"

def verify(vid, col, target, who, result, supersedes=None, reason=None, at="2026-12-10T09:00:00"):
    cols = {"activity_revision_id": None, "lot_revision_id": None, "lot_event_id": None}
    cols[col] = target
    ins("verification", vid, cols["activity_revision_id"], cols["lot_revision_id"], cols["lot_event_id"],
        who, result, "field_visit", None, supersedes, reason, at, T)

# Hộ A: bón thúc đúng lịch, có ảnh + vật tư, KTV xác minh; phun thuốc X 5 ngày trước thu hoạch
r = activity("bt_a", "ca", "at_bt", "u_a", "2026-12-05", [("m_ure", 30, "kg")]); evidence("photo", "activity_revision_id", r)
verify("ver_bt_a", "activity_revision_id", r, "u_ktv", "verified")
r = activity("ph_a", "ca", "at_phun", "u_a", "2027-02-05", [("m_x", 200, "ml")]); evidence("photo", "activity_revision_id", r)
# Hộ B: bón thúc có ảnh; sau đó sửa liều (bản 2) mà chưa liên kết lại ảnh; phun thuốc Y (chưa có luật cách ly cho mè)
r = activity("bt_b", "cb", "at_bt", "u_b", "2026-12-05", [("m_ure", 30, "kg")]); evidence("photo", "activity_revision_id", r)
ins("activity_revision", "bt_b_r2", "bt_b", 2, "2026-12-05", "day", "u_b", None, "u_b", T, "Ghi sai liều: 25 kg")
ins("activity_input", "bt_b_r2", "m_ure", 25, "kg")
r = activity("ph_b", "cb", "at_phun", "u_b", "2027-01-20", [("m_y", 150, "ml")]); evidence("photo", "activity_revision_id", r)
# Hộ C: KHÔNG ghi bón thúc
# Thu hoạch 3 hộ, mỗi hộ có phiếu cân, sinh lô thu hoạch
for k, kg in [("a", 400), ("b", 350), ("c", 250)]:
    r = activity(f"th_{k}", f"c{k}", "at_th", f"u_{k}", "2027-02-10")
    evidence("weighing_slip", "activity_revision_id", r)
    ins("lot", f"h{k}", f"H-{k.upper()}", "harvest", f"th_{k}", "u_fns", T, "app", None)
    ins("lot_revision", f"h{k}_r1", f"h{k}", 1, "Hạt mè", kg, "kg", None, None, "u_fns", T, None)

def new_lot(lid, code, ltype, name, qty, unit, pack=None):
    ins("lot", lid, code, ltype, None, "u_fns", T, "app", None)
    ins("lot_revision", lid + "_r1", lid, 1, name, qty, unit, pack, None, "u_fns", T, None)

def event(eid, etype, out, subj, when, prec, fac, by="u_fns"):
    ins("lot_event", eid, etype, out, subj, when, prec, fac, by, by, T, "app", None)

new_lot("raw", "RAW-01", "aggregated", "Hạt mè", 1000, "kg")
event("e_gop", "aggregation", "raw", None, "2027-02-12T09:00:00", "minute", "fac_tm")
for k, kg in [("a", 400), ("b", 350), ("c", 250)]:
    ins("lot_input", "e_gop", f"h{k}", kg, "kg")
evidence("weighing_slip", "lot_event_id", "e_gop")
verify("ver_gop", "lot_event_id", "e_gop", "u_qa", "verified")
event("e_vc", "transport", None, "raw", "2027-02-13", "day", None)
new_lot("proc", "PROC-01", "processed", "Dầu mè rang", 400, "l")
event("e_ep", "transformation", "proc", None, "2027-02-20T08:00:00", "minute", "fac_nm")
ins("lot_input", "e_ep", "raw", 1000, "kg")
evidence("lab_report", "lot_revision_id", "proc_r1")
for lid, code, pack, cnt, lit in [("b80", "QR-80", "chai thủy tinh 80ml", 2500, 200), ("b250", "QR-250", "chai thủy tinh 250ml", 800, 200)]:
    new_lot(lid, code, "packaged", "Dầu mè rang", cnt, "unit", pack)
    event("e_" + lid, "packaging", lid, None, "2027-02-22T10:00:00", "minute", "fac_nm")
    ins("lot_input", "e_" + lid, "proc", lit, "l")
ins("lot_revision", "raw_r2", "raw", 2, "Hạt mè", 995, "kg", None, None, "u_fns", T, "Cân lại sau khi sàng")

ins("device", "dev1", "u_dev", "soil_moisture", "%", "pa", None, "u_fns", T)
ins("observation", "obs1", "dev1", "2026-12-01T06:00:00", 23.5, "pa", None, T, "iot_gateway", "GW-0001")
evidence("sensor", "plot_id", "pa", obs="obs1")
db.run("UPDATE device SET plot_id = 'pb' WHERE device_id = 'dev1'")   # chuyển thiết bị sang lô đất khác
ins("certification", "cert1", "VietGAP", "VG-123", "u_cert", "2026-01-01", "2027-01-31", "fa", None, None, None, "u_fns", T)
evidence("document", "certification_id", "cert1")

# ====================================================================
print(f"\n=== {DIALECT} ===\nF · Chức năng")
st = {r[0]: (r[1], r[2]) for r in db.run("SELECT activity_id, evidence_completeness, verification_state FROM v_activity_status")}
check("F1", "hộ A bón thúc: đủ minh chứng + đã xác minh", st["bt_a"] == ("complete", "verified"), str(st["bt_a"]))
check("F2", "hộ B sửa liều, chưa liên kết lại ảnh → thiếu minh chứng", st["bt_b"] == ("missing_evidence", "unverified"), str(st["bt_b"]))

exp = {(r[0], r[1]): r[2] for r in db.run("SELECT cycle_id, code, schedule_state FROM v_cycle_expected")}
check("F3", "hộ C không ghi bón thúc → bị phát hiện 'not_recorded'", exp[("cc", "TOP_DRESS_1")] == "not_recorded", exp[("cc", "TOP_DRESS_1")])
check("F4", "chu kỳ chưa có ngày gieo → 'undetermined', không phải 'thiếu'", exp[("cc2", "TOP_DRESS_1")] == "undetermined", exp[("cc2", "TOP_DRESS_1")])
cs = {r[0]: r[1] for r in db.run("SELECT cycle_id, cycle_state FROM v_cycle_completeness")}
check("F5", "trạng thái chu kỳ A/B/C/C2", (cs["ca"], cs["cb"], cs["cc"], cs["cc2"]) == ("complete", "incomplete", "incomplete", "undetermined"),
      f"A={cs['ca']}, B={cs['cb']}, C={cs['cc']}, C2={cs['cc2']}")

src = sorted((r[0], num(r[1]), r[2]) for r in db.run(
    "SELECT h.public_code, s.share, s.source_status FROM v_lot_sources s JOIN lot h ON h.lot_id = s.source_lot_id "
    "JOIN lot b ON b.lot_id = s.root_lot_id WHERE b.public_code = 'QR-80'"))
check("F6", "truy ngược QR-80 theo số lượng thực dùng", src == [("H-A", 0.4, "harvest"), ("H-B", 0.35, "harvest"), ("H-C", 0.25, "harvest")], str(src))
ls = db.run("SELECT traced_share, complete_share, verified_share, untraceable_share, trace_state FROM v_lot_status WHERE public_code = 'QR-80'")[0]
check("F7", "trạng thái lô QR-80: 100% truy được, 40% từ chu kỳ đủ minh chứng",
      (num(ls[0]), num(ls[1]), num(ls[3]), ls[4]) == (1.0, 0.4, 0.0, "fully_traced"),
      f"traced={num(ls[0])}, complete={num(ls[1])}, verified={num(ls[2])}, state={ls[4]}")
dst = sorted(r[0] for r in db.run("SELECT d.public_code FROM v_lot_destinations x JOIN lot d ON d.lot_id = x.destination_lot_id "
                                   "JOIN lot h ON h.lot_id = x.root_lot_id WHERE h.public_code = 'H-A'"))
check("F8", "truy xuôi từ lô thu hoạch H-A tới các lô chai", dst == ["PROC-01", "QR-250", "QR-80", "RAW-01"], str(dst))
es = db.run("SELECT evidence_completeness, verification_state FROM v_lot_event_status WHERE event_id = 'e_gop'")[0]
check("F9", "sự kiện gộp lô có trạng thái minh chứng + xác minh riêng", es == ("complete", "verified"), str(es))
phi = [(r[0], r[1], num(r[2]), str(r[3])) for r in db.run("SELECT harvest_activity_id, trade_name, days_between, phi_days FROM v_phi_violations")]
check("F10", "phát hiện vi phạm cách ly (theo cây trồng)", phi == [("th_a", "Thuốc X", 5.0, "7")], str(phi))
iss = sorted({(r[0], r[1]) for r in db.run("SELECT issue, subject_id FROM v_integrity_issues")})
check("F11", "kiểm tra nhất quán: thuốc Y chưa có luật cách ly cho mè", ("missing_phi_rule", "ph_b_r1") in iss, str(iss))
q2 = db.run("SELECT revision_no, quantity, reason FROM v_lot_current WHERE lot_id = 'raw'")[0]
check("F12", "sửa khối lượng lô có lý do, giữ bản cũ", (str(q2[0]), num(q2[1]), q2[2]) == ("2", 995.0, "Cân lại sau khi sàng"), str(q2))
ob = db.run("SELECT plot_id FROM observation WHERE observation_id = 'obs1'")[0][0]
check("F13", "thiết bị chuyển chỗ, số đo cũ vẫn giữ vị trí lúc đo", ob == "pa", f"observation ở {ob}, thiết bị hiện ở pb")
cv = db.run("SELECT CASE WHEN c.valid_from <= '2027-02-10' AND '2027-02-10' <= c.valid_to THEN 1 ELSE 0 END "
            "FROM certification c WHERE c.cert_number = 'VG-123'")[0][0]
check("F14", "chứng nhận hết hạn trước ngày thu hoạch", str(cv) == "0")
ins("crop_profile", "cp_lac", "PEANUT", "Lạc (mock)", 1, "sowing", None, "mock", "2026-01-01")
ins("stage", "st_lac", "cp_lac", 1, "Thu hoạch")
ins("activity_type", "at_lac", "st_lac", "HARVEST", "Nhổ, phơi, tách vỏ", "mandatory", 100, 7, 1, 0, None, "summary", "mock", 1)
check("F15", "thêm cây lạc chỉ bằng dữ liệu", True, "3 INSERT, 0 lệnh DDL")

print("\nV · Bổ sung v0.4 (đánh giá vòng 3)")
cs = db.run("SELECT chain_evidence_state, n_chain_events, n_chain_missing_evidence FROM v_lot_status WHERE public_code = 'QR-80'")[0]
check("V1", "chuỗi sau thu hoạch QR-80: 4 sự kiện, đủ minh chứng", (cs[0], str(cs[1]), str(cs[2])) == ("complete", "4", "0"), str(cs))
ins("evidence_requirement", "er_ep", None, "transformation", "photo", 1, "giả định nhóm", 1)
cs = db.run("SELECT chain_evidence_state, n_chain_missing_evidence, trace_state FROM v_lot_status WHERE public_code = 'QR-80'")[0]
check("V2", "ép dầu thiếu ảnh → trang QR báo chuỗi 'incomplete' (trước đây vẫn fully_traced)", (cs[0], str(cs[1])) == ("incomplete", "1"), str(cs))
evidence("photo", "lot_event_id", "e_ep")
cs = db.run("SELECT chain_evidence_state FROM v_lot_status WHERE public_code = 'QR-80'")[0][0]
check("V3", "bổ sung ảnh ép dầu → chuỗi 'complete'", cs == "complete", cs)
verify("ver_ep", "lot_event_id", "e_ep", "u_qa", "rejected")
cs = db.run("SELECT chain_evidence_state, n_chain_rejected FROM v_lot_status WHERE public_code = 'QR-80'")[0]
check("V4", "QA từ chối sự kiện ép dầu → chuỗi 'rejected'", (cs[0], str(cs[1])) == ("rejected", "1"), str(cs))
tl = db.run("SELECT kind, ref_id, at FROM v_lot_timeline WHERE root_lot_id = 'b80' ORDER BY at, kind")
kinds = sorted({r[0] for r in tl})
check("V5", "timeline QR-80 hợp nhất 6 loại (v0.5 thêm lot_revision)", kinds == ["activity", "cycle_anchor", "lot_event", "lot_revision", "observation", "verification"], f"{len(tl)} dòng: {kinds}")
check("V6", "timeline sắp theo thời gian: bắt đầu từ mốc gieo, kết thúc ở đóng chai",
      tl[0][0] == "cycle_anchor" and tl[-1][1] in ("e_b80", "ver_ep") and any(r[1] == "e_ep" for r in tl),
      f"đầu={tl[0][:2]}, cuối={tl[-1][:2]}")
ns = db.run("SELECT COUNT(*) FROM cultivation_cycle c JOIN season s ON s.season_id = c.season_id WHERE s.name = 'Đông Xuân 2026–2027'")[0][0]
check("V7", "vụ là thực thể: truy vấn mọi chu kỳ của vụ Đông Xuân", str(ns) == "4", f"{ns} chu kỳ")
ch = db.run("SELECT source_channel, external_ref FROM observation WHERE observation_id = 'obs1'")[0]
check("V8", "số đo ghi rõ kênh nguồn và mã ngoài", ch == ("iot_gateway", "GW-0001"), str(ch))
r0 = db.run("SELECT on_schedule_ratio, cycle_state FROM v_cycle_completeness WHERE cycle_id = 'ca'")[0]
check("V9", "chiều đúng hạn tách riêng: chu kỳ A 100% đúng lịch", (num(r0[0]), r0[1]) == (1.0, "complete"), str(r0))
ins("cycle_anchor", "an_a2", "ca", 2, "2026-12-20", "u_ktv", T, "Ngày gieo ghi nhầm, đối chiếu sổ tay")
r1 = db.run("SELECT on_schedule_ratio, cycle_state, n_off_schedule FROM v_cycle_completeness WHERE cycle_id = 'ca'")[0]
hist = db.run("SELECT COUNT(*) FROM cycle_anchor WHERE cycle_id = 'ca'")[0][0]
check("V10", "đổi mốc gieo có lý do: giữ lịch sử, lịch tính lại, đúng hạn rơi về 0%",
      (num(r1[0]), r1[1], str(r1[2]), str(hist)) == (0.0, "complete", "2", "2"),
      f"đúng hạn={num(r1[0])}, minh chứng={r1[1]}, lệch lịch={r1[2]}, lịch sử={hist} bản")
db.run("UPDATE cultivation_cycle SET closed_at = '2027-03-01' WHERE cycle_id = 'cc2'")
check("V11", "chu kỳ đang mở được đóng một lần", db.run("SELECT closed_at FROM cultivation_cycle WHERE cycle_id='cc2'")[0][0].startswith("2027-03-01"))

print("\nR · Hồi quy các lỗi bên đánh giá đã tái hiện")
blocked("R0", "khóa ngoại được kiểm (hoạt động trỏ chu kỳ không tồn tại)",
        f"INSERT INTO activity VALUES ('x0','khong_co','at_bt','u_a',{q(T)},'app',NULL)", "fk")
new_lot("h1x", "P1", "aggregated", "Hạt mè không rõ nguồn", 200, "kg")      # lô không có nguồn
new_lot("r1x", "R1", "aggregated", "Hạt mè", 500, "kg")
event("e_r1", "aggregation", "r1x", None, "2027-02-14", "day", None)
ins("lot_input", "e_r1", "ha", 300, "kg"); ins("lot_input", "e_r1", "h1x", 200, "kg")
s1 = sorted((r[0], num(r[1]), r[2]) for r in db.run(
    "SELECT l.public_code, s.share, s.source_status FROM v_lot_sources s JOIN lot l ON l.lot_id = s.source_lot_id WHERE s.root_lot_id = 'r1x'"))
check("R1", "nguồn không truy được được HIỆN RA, không bị bỏ", s1 == [("H-A", 0.6, "harvest"), ("P1", 0.4, "untraceable")], str(s1))
s1b = db.run("SELECT untraceable_share, trace_state FROM v_lot_status WHERE lot_id = 'r1x'")[0]
check("R1b", "trạng thái lô ghi rõ 40% không truy được", (num(s1b[0]), s1b[1]) == (0.4, "partially_untraceable"), str(s1b))
blocked("R2", "thêm cạnh tạo vòng (RAW-01 làm đầu vào của chính nguồn của nó)", "INSERT INTO lot_input VALUES ('e_ep','b80',1,'unit','u_fns','2026-11-25T08:00:00')", "tạo vòng")
db.run(f"INSERT INTO evidence VALUES ('ev_dup','photo','s3://dup','shadup',NULL,NULL,NULL,'u_c',{q(T)},'app',NULL)")
activity("bt_c2", "cc", "at_bt", "u_c", "2026-12-20")
db.run(f"INSERT INTO evidence_link (link_id,evidence_id,activity_revision_id,linked_by,linked_at) VALUES ('ld1','ev_dup','bt_c2_r1','u_c',{q(T)})")
blocked("R3", "liên kết cùng một file 2 lần vào cùng bản ghi",
        f"INSERT INTO evidence_link (link_id,evidence_id,activity_revision_id,linked_by,linked_at) VALUES ('ld2','ev_dup','bt_c2_r1','u_c',{q(T)})", "unique")
activity("bt_x", "cc2", "at_bt", "u_c", "2026-12-05", [("m_ure", 10, "kg")])
verify("ver_x", "activity_revision_id", "bt_x_r1", "u_ktv", "verified")
sx = db.run("SELECT evidence_completeness, verification_state FROM v_activity_status WHERE activity_id = 'bt_x'")[0]
check("R4", "đã xác minh nhưng 0 minh chứng: hai cột hiển thị riêng", sx == ("missing_evidence", "verified"), str(sx))
r5 = activity("bt_y", "cc2", "at_bt", "u_c", "2026-12-06", [("m_ure", 10, "kg")]); evidence("photo", "activity_revision_id", r5)
verify("ver_y1", "activity_revision_id", r5, "u_ktv", "rejected", at="2026-12-07T09:00:00")
blocked("R5a", "xác minh thứ hai không thay thế lần trước",
        f"INSERT INTO verification VALUES ('ver_y2',{q(r5)},NULL,NULL,'u_ktv2','verified','field_visit',NULL,NULL,NULL,'2026-12-08T09:00:00',{q(T)})", "kết luận hiệu lực")
verify("ver_y3", "activity_revision_id", r5, "u_ktv", "verified", supersedes="ver_y1", reason="Nông dân chụp lại ảnh rõ", at="2026-12-08T09:00:00")
sy = db.run("SELECT verification_state FROM v_activity_status WHERE activity_id = 'bt_y'")[0][0]
hist = db.run(f"SELECT COUNT(*) FROM verification WHERE activity_revision_id = {q(r5)}")[0][0]
check("R5b", "kiểm tra lại có ghi rõ thay thế: kết luận hiệu lực + giữ lịch sử", (sy, str(hist)) == ("verified", "2"), f"{sy}, {hist} lần trong lịch sử")
blocked("D1", "hai lô cùng một hoạt động thu hoạch", f"INSERT INTO lot VALUES ('hx','H-X','harvest','th_a','u_fns',{q(T)},'app',NULL)", "unique")
blocked("D2", "lô thu hoạch trỏ vào hoạt động không phải thu hoạch", f"INSERT INTO lot VALUES ('hy','H-Y','harvest','bt_a','u_fns',{q(T)},'app',NULL)", "produces_lot")
blocked("D3", "hai sự kiện cùng tạo ra một lô",
        f"INSERT INTO lot_event VALUES ('e_dup','aggregation','raw',NULL,{q(T)},'day',NULL,'u_fns','u_fns',{q(T)},'app',NULL)", "unique")

print("\nC · Ràng buộc và trigger")
blocked("C1", "UPDATE bản ghi hoạt động (chỉ ghi thêm)", "UPDATE activity_revision SET reason = 'x' WHERE revision_id = 'bt_a_r1'", "append-only")
blocked("C2", "DELETE minh chứng (chỉ ghi thêm)", "DELETE FROM evidence WHERE evidence_id = 'ev1'", "append-only")
blocked("C3", "mốc vận chuyển có đầu vào", "INSERT INTO lot_input VALUES ('e_vc','ha',1,'kg','u_fns','2026-11-25T08:00:00')", "mốc thu mua")
blocked("C4", "nông dân tự xác minh bản ghi của mình",
        f"INSERT INTO verification VALUES ('vs','bt_c2_r1',NULL,NULL,'u_c','verified','field_visit',NULL,NULL,NULL,{q(T)},{q(T)})", "trùng người")
blocked("C5", "thay thế xác minh của đối tượng khác",
        f"INSERT INTO verification VALUES ('vz','bt_c2_r1',NULL,NULL,'u_ktv','verified','field_visit',NULL,'ver_bt_a','x',{q(T)},{q(T)})", "cùng đối tượng")
blocked("C6", "bản sửa hoạt động không có lý do",
        f"INSERT INTO activity_revision VALUES ('bt_c2_r2','bt_c2',2,{q(T)},'day','u_c',NULL,'u_c',{q(T)},NULL)", "check")
blocked("C7", "đơn vị ngoài danh mục", "INSERT INTO lot_input VALUES ('e_r1','hb',10,'bao','u_fns','2026-11-25T08:00:00')", "check")
blocked("C8", "số lượng thiếu đơn vị", "INSERT INTO lot_input VALUES ('e_r1','hc',10,NULL,'u_fns','2026-11-25T08:00:00')", "check")
blocked("C9", "minh chứng gắn 2 đối tượng một lúc",
        f"INSERT INTO evidence_link VALUES ('lx','ev1',NULL,NULL,'e_gop','pa',NULL,'u_fns',{q(T)})", "check")
blocked("C10", "chứng nhận gắn 2 phạm vi",
        f"INSERT INTO certification VALUES ('cx','VietGAP','1','u_cert','2026-01-01','2027-01-01','fa','pa',NULL,NULL,'u_fns',{q(T)})", "check")
blocked("C11", "số đo cảm biến không ghi vị trí", f"INSERT INTO observation VALUES ('obx','dev1',{q(T)},1,NULL,NULL,{q(T)},'iot_gateway',NULL)", "check")
blocked("C12", "luật cách ly không có nguồn", "INSERT INTO material_crop_rule VALUES ('m_y','SESAME',3,NULL,1)", "notnull")
blocked("C13", "hai loại hoạt động trùng mã trong một giai đoạn",
        "INSERT INTO activity_type VALUES ('at_dup','st_cs','TOP_DRESS_1','x','optional',NULL,0,0,0,NULL,'detail',NULL,0)", "unique")

blocked("C14", "đổi lặng lẽ cây trồng của chu kỳ", "UPDATE cultivation_cycle SET crop_profile_id = 'cp_lac' WHERE cycle_id = 'ca'", "chỉ được cập nhật closed_at")
blocked("C15", "sửa mốc gieo không có lý do", f"INSERT INTO cycle_anchor VALUES ('an_x','cb',2,'2026-11-25','u_b',{q(T)},NULL)", "check")
blocked("C16", "UPDATE lịch sử mốc gieo", "UPDATE cycle_anchor SET anchor_date = '2026-11-01' WHERE cycle_anchor_id = 'an_b1'", "append-only")
blocked("C17", "nạp trùng mã ngoài từ cùng kênh", f"INSERT INTO observation VALUES ('obs2','dev1',{q(T)},20,'pa',NULL,{q(T)},'iot_gateway','GW-0001')", "unique")
blocked("C18", "kênh nguồn ngoài danh mục", f"INSERT INTO observation VALUES ('obs3','dev1',{q(T)},20,'pa',NULL,{q(T)},'excel',NULL)", "check")
blocked("C19", "minh chứng cảm biến không có số đo", f"INSERT INTO evidence VALUES ('evx','sensor',NULL,NULL,NULL,NULL,NULL,'u_fns',{q(T)},'app',NULL)", "check")
blocked("C20", "xóa chu kỳ canh tác", "DELETE FROM cultivation_cycle WHERE cycle_id = 'cc2'", "không cho DELETE")

print("\nN · Hồi quy v0.5 (đánh giá độc lập vòng 4)")
PG = DIALECT != "sqlite"
# --- Cao 1: sự kiện không có đầu vào không được tính là truy được
new_lot("bx", "QR-X", "packaged", "Dầu mè", 100, "unit"); event("e_bx", "packaging", "bx", None, "2027-02-25", "day", "fac_nm")
r = db.run("SELECT trace_state, untraceable_share, traced_share FROM v_lot_status WHERE lot_id = 'bx'")[0]
check("N1", "đóng gói chưa ghi đầu vào → 'untraceable' (trước: fully_traced)", (r[0], num(r[1]), num(r[2])) == ("untraceable", 1.0, 0.0), str(r))
new_lot("ghost", "G-1", "aggregated", "Hạt mè", 200, "kg"); event("e_ghost", "aggregation", "ghost", None, "2027-02-11", "day", "fac_tm")
new_lot("mix", "MIX-1", "aggregated", "Hạt mè", 500, "kg"); event("e_mix", "aggregation", "mix", None, "2027-02-12", "day", "fac_tm")
ins("lot_input", "e_mix", "ha", 300, "kg"); ins("lot_input", "e_mix", "ghost", 200, "kg")
r = db.run("SELECT trace_state, untraceable_share FROM v_lot_status WHERE lot_id = 'mix'")[0]
check("N2", "40% từ lô có sự kiện rỗng → hiện 40% không truy được", (r[0], num(r[1])) == ("partially_untraceable", 0.4), str(r))
# --- Cao 2: loại lô đầu ra phải khớp loại sự kiện
blocked("N3", "sự kiện gộp ghi đầu ra là lô thu hoạch (tỷ trọng từng lên 200%)",
        f"INSERT INTO lot_event VALUES ('e_bad','aggregation','hb',NULL,{q(T)},'day',NULL,'u_fns','u_fns',{q(T)},'app',NULL)", "không khớp loại sự kiện")
# --- Cao 4: ghi đè qua INSERT OR REPLACE (SQLite) / UPSERT, TRUNCATE (PostgreSQL)
if PG:
    blocked("N4", "UPSERT đổi kết luận xác minh",
            f"INSERT INTO verification VALUES ('ver_bt_a','bt_c2_r1',NULL,NULL,'u_ktv','rejected','field_visit',NULL,NULL,NULL,{q(T)},{q(T)}) "
            "ON CONFLICT (verification_id) DO UPDATE SET result = 'rejected'", "append-only")
    blocked("N5", "UPSERT đổi khối lượng cạnh lô (đổi tỷ trọng QR)",
            f"INSERT INTO lot_input VALUES ('e_mix','ha',4000,'kg','u_fns',{q(T)}) ON CONFLICT (event_id, input_lot_id) DO UPDATE SET quantity_used = 4000", "append-only")
    blocked("N6", "TRUNCATE bảng chỉ ghi thêm", "TRUNCATE verification CASCADE", "append-only")
else:
    blocked("N4", "INSERT OR REPLACE đổi kết luận xác minh",
            f"INSERT OR REPLACE INTO verification VALUES ('ver_bt_a','bt_c2_r1',NULL,NULL,'u_ktv','rejected','field_visit',NULL,NULL,NULL,{q(T)},{q(T)})", "trùng khóa")
    blocked("N5", "INSERT OR REPLACE đổi khối lượng cạnh lô (đổi tỷ trọng QR)",
            f"INSERT OR REPLACE INTO lot_input VALUES ('e_mix','ha',4000,'kg','u_fns',{q(T)})", "trùng khóa")
    blocked("N6", "INSERT OR REPLACE đổi mốc gieo không để lại lịch sử",
            f"INSERT OR REPLACE INTO cycle_anchor VALUES ('an_b1','cb',1,'2026-10-01','u_b',{q(T)},NULL)", "trùng khóa")
# --- Cao 3: closed_at
blocked("N7", "dời ngày đóng chu kỳ đã đóng (từng biến 'thiếu' thành 'chưa đến hạn')",
        "UPDATE cultivation_cycle SET closed_at = '2026-12-01' WHERE cycle_id = 'cc'", "đã đóng")
blocked("N8", "mở lại chu kỳ đã đóng", "UPDATE cultivation_cycle SET closed_at = NULL WHERE cycle_id = 'ca'", "đã đóng")
ins("plot", "pz", "fc", "L3", 1000, None, None, "u_fns", T)
ins("cultivation_cycle", "cz", "pz", "cp_me", "v_me", "ss_dx", "2026-11-15", "2026-11-30", "u_fns", T)
ins("cycle_anchor", "an_z1", "cz", 1, "2026-11-20", "u_c", T, None)
z = db.run("SELECT schedule_state FROM v_cycle_expected WHERE cycle_id = 'cz' AND code = 'TOP_DRESS_1'")[0][0]
check("N9", "chu kỳ đã đóng: việc chưa ghi là 'not_recorded', không bao giờ 'not_due'", z == "not_recorded", z)
ins("cultivation_cycle", "cy", "pz", "cp_me", "v_me", "ss_dx", "2026-12-01", None, "u_fns", T)
activity("bt_cy", "cy", "at_bt", "u_c", "2026-12-20", [("m_ure", 5, "kg")])
blocked("N10", "đóng chu kỳ trước ngày hoạt động cuối", "UPDATE cultivation_cycle SET closed_at = '2026-12-10' WHERE cycle_id = 'cy'", "trước ngày hoạt động cuối")
blocked("N11", "đổi khóa chính chu kỳ", "UPDATE cultivation_cycle SET cycle_id = 'cy2' WHERE cycle_id = 'cy'", "chỉ được cập nhật closed_at")
# --- Trung bình
r = activity("ph_a2", "ca", "at_phun", "u_a", "2027-01-10", [("m_x", 100, "ml")])   # phun thuốc không có ảnh
r = db.run("SELECT cycle_state, n_other_problem FROM v_cycle_completeness WHERE cycle_id = 'ca'")[0]
check("N12", "hoạt động có điều kiện thiếu minh chứng → chu kỳ 'incomplete'", (r[0], str(r[1])) == ("incomplete", "1"), str(r))
blocked("N13", "hạ hoạt động bắt buộc thành tùy chọn (đổi kết luận cũ)", "UPDATE activity_type SET requirement = 'optional' WHERE activity_type_id = 'at_bt'", "append-only")
blocked("N14", "xóa yêu cầu minh chứng", "DELETE FROM evidence_requirement WHERE requirement_id = 'er1'", "append-only")
blocked("N15", "chuyển lô đất sang hộ khác", "UPDATE plot SET farm_id = 'fb' WHERE plot_id = 'pa'", "không đổi định danh")
blocked("N16", "đổi chủ hộ", "UPDATE farm SET owner_agent_id = 'u_b' WHERE farm_id = 'fa'", "không đổi định danh")
ins("activity_type", "at_bt2", "st_cs", "TOP_DRESS_2", "Bón thúc 2", "optional", None, 0, 0, 0, None, "detail", "mock", 1)
ins("evidence_requirement", "er_j", "at_bt2", None, "photo", 2, "mock", 1)
activity("bt_j", "cc2", "at_bt2", "u_c", "2026-12-10")
for i in (1, 2):
    ins("evidence", f"ev_j{i}", "photo", f"s3://j{i}", "SAME", None, None, None, "u_c", T, "app", None)
    db.run(f"INSERT INTO evidence_link (link_id,evidence_id,activity_revision_id,linked_by,linked_at) VALUES ('lj{i}','ev_j{i}','bt_j_r1','u_c',{q(T)})")
j = db.run("SELECT evidence_completeness FROM v_activity_status WHERE activity_id = 'bt_j'")[0][0]
check("N17", "cần 2 ảnh, tải cùng một file 2 lần → vẫn thiếu", j == "missing_evidence", j)
new_lot("b1l", "QR-1L", "packaged", "Dầu mè", 300, "unit"); event("e_b1l", "packaging", "b1l", None, "2027-02-23", "day", "fac_nm")
ins("lot_input", "e_b1l", "proc", 300, "l")
new_lot("early", "QR-E", "packaged", "Dầu mè", 10, "unit"); event("e_early", "packaging", "early", None, "2027-01-01", "day", "fac_nm")
ins("lot_input", "e_early", "proc", 5, "l")
iss = {(r[0], r[1]) for r in db.run("SELECT issue, subject_id FROM v_integrity_issues")}
check("N18", "dùng quá khối lượng lô PROC (200+200+300+5 > 400 l) được báo", ("over_consumption", "proc") in iss)
check("N19", "đóng chai (01/01) trước khi ép dầu (20/02) được báo", ("event_time_order", "e_early") in iss)
blocked("N20", "thêm đầu vào hồi tố vào sự kiện ép dầu khi dầu đã đóng chai",
        f"INSERT INTO lot_input VALUES ('e_ep','hc',10,'kg','u_fns',{q(T)})", "đã được dùng tiếp")
verify("ver_mix", "lot_event_id", "e_mix", "u_qa", "verified")
blocked("N21", "thêm đầu vào vào sự kiện đã được xác minh",
        f"INSERT INTO lot_input VALUES ('e_mix','hc',10,'kg','u_fns',{q(T)})", "đã được xác minh")
# --- Thấp
blocked("N22", "số bản mốc gieo nhảy cóc", f"INSERT INTO cycle_anchor VALUES ('an_j','ca',5,'2026-11-25','u_ktv',{q(T)},'x')", "tăng đúng 1")
activity("bt_pre", "cb", "at_phun", "u_b", "2025-01-01", [("m_ure", 1, "kg")])
iss = {(r[0], r[1]) for r in db.run("SELECT issue, subject_id FROM v_integrity_issues")}
check("N23", "hoạt động trước ngày bắt đầu chu kỳ được cảnh báo", ("activity_before_cycle_start", "bt_pre") in iss)
blocked("N24", "bản ghi kênh 'import' không có mã ngoài", f"INSERT INTO activity VALUES ('imp1','ca','at_phun','u_a',{q(T)},'import',NULL)", "check")
r = activity("th_c2", "cc2", "at_th", "u_c", "2027-02-10"); evidence("weighing_slip", "activity_revision_id", r)
ins("lot", "hc2", "H-C2", "harvest", "th_c2", "u_fns", T, "app", None)
ins("lot_revision", "hc2_r1", "hc2", 1, "Hạt mè", 50, "kg", None, None, "u_fns", T, None)
r = db.run("SELECT undetermined_share, complete_share FROM v_lot_status WHERE lot_id = 'hc2'")[0]
check("N25", "lô từ chu kỳ chưa có mốc gieo: tách riêng undetermined_share", (num(r[0]), num(r[1])) == (1.0, 0.0), str(r))
r = db.run("SELECT chain_evidence_state FROM v_lot_status WHERE lot_id = 'h1x'")[0][0]
check("N26", "lô mồ côi → 'no_source_event' (trước: no_post_harvest_events)", r == "no_source_event", r)
r = db.run("SELECT evidence_completeness FROM v_lot_event_status WHERE event_id = 'e_vc'")[0][0]
check("N27", "mốc vận chuyển không có yêu cầu → 'not_required' (không phải 'complete')", r == "not_required", r)
ins("observation", "obs_close", "dev1", "2027-02-28T10:00:00", 21, "pa", None, T, "iot_gateway", "GW-0002")
n1 = db.run("SELECT COUNT(*) FROM v_lot_timeline WHERE root_lot_id = 'ha' AND ref_id = 'obs_close'")[0][0]
check("N28", "số đo trong ngày đóng chu kỳ có trên timeline", str(n1) == "1", f"{n1} dòng")
verify("ver_lab", "lot_revision_id", "proc_r1", "u_qa", "rejected")
refs = {r[0]: r[1] for r in db.run("SELECT ref_id, detail FROM v_lot_timeline WHERE root_lot_id = 'b80' AND kind IN ('verification','lot_revision')")}
check("N29", "timeline có xác minh bản ghi lô và lần sửa lô", refs.get("ver_lab") == "lot_revision" and refs.get("raw_r2") == "lot_corrected", str({k: refs.get(k) for k in ('ver_lab', 'raw_r2')}))
verify("ver_old", "activity_revision_id", "bt_b_r1", "u_ktv", "verified")
d = db.run("SELECT detail FROM v_lot_timeline WHERE root_lot_id = 'hb' AND ref_id = 'ver_old'")[0][0]
check("N30", "xác minh của bản ghi cũ được ghi nhãn 'bản ghi cũ'", d == "activity (bản ghi cũ)", d)

ok = sum(1 for _, o in results if o)
print(f"\nTổng ({DIALECT}): {ok}/{len(results)} đạt")
sys.exit(0 if ok == len(results) else 1)
