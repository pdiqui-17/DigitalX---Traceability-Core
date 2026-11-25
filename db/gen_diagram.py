"""Sinh UML class diagram (Mermaid) TỰ ĐỘNG từ schema.sql để sơ đồ không lệch với SQL.
- Thuộc tính = cột không phải khóa ngoại; cột riêng tư đánh dấu '-'
- Quan hệ = khóa ngoại; bản số suy từ NOT NULL / UNIQUE
- Phương thức = các view tính toán (ánh xạ ở METHODS)
Chạy: python3 gen_diagram.py   → class_diagram.mmd + cd_1/2/3_*.mmd (render PNG bằng mmdc)
"""
import re, pathlib

HERE = pathlib.Path(__file__).parent
sql = (HERE / "schema.sql").read_text(encoding="utf-8")
sql = re.sub(r"--[^\n]*", "", sql)

PRIVATE = {"address_detail", "geo_point"}
METHODS = {
    "Activity": ["currentRevision() ActivityRevision", "evidenceCompleteness() String", "verificationState() String"],
    "CultivationCycle": ["currentAnchor() CycleAnchor", "expectedActivities() List", "completeness() CompletenessReport", "phiViolations() List"],
    "Lot": ["currentRevision() LotRevision", "traceSources() List", "traceDestinations() List", "status() LotStatus", "timeline() List"],
    "LotEvent": ["evidenceCompleteness() String", "verificationState() String"],
    "LotRevision": ["verificationState() String"],
    "Verification": ["isEffective() bool"],
    "Certification": ["isValidOn(date) bool"],
}
GROUPS = {
    "cd_1_canh_tac": ["crop_profile", "stage", "activity_type", "evidence_requirement", "variety", "input_material",
                      "material_crop_rule", "farm", "plot", "season", "cultivation_cycle", "cycle_anchor", "activity",
                      "activity_revision", "activity_input", "agent"],
    "cd_2_lo": ["activity", "lot", "lot_revision", "lot_event", "lot_input", "facility", "agent"],
    "cd_3_minh_chung_xac_minh": ["evidence", "evidence_link", "verification", "activity_revision", "lot_revision",
                                 "lot_event", "plot", "certification", "device", "observation"],
}

def pascal(t): return "".join(w.capitalize() for w in t.split("_"))
def camel(c):
    w = c.split("_"); return w[0] + "".join(x.capitalize() for x in w[1:])

tables = {}
for name, body in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", sql, re.S):
    cols, fks = [], []
    for line in body.split("\n"):
        line = line.strip().rstrip(",")
        m = re.match(r"(\w+)\s+(TEXT|INTEGER|NUMERIC|TIMESTAMP|DATE)\b(.*)", line)
        if not m or m.group(1).upper() in ("CHECK", "UNIQUE", "PRIMARY"):
            continue
        col, typ, rest = m.groups()
        ref = re.search(r"REFERENCES (\w+)", rest)
        if ref:
            fks.append((col, ref.group(1), "NOT NULL" in rest or "PRIMARY KEY" in rest, "UNIQUE" in rest))
        else:
            t = {"TEXT": "String", "INTEGER": "int", "NUMERIC": "Decimal", "TIMESTAMP": "DateTime", "DATE": "Date"}[typ]
            cols.append(("-" if col in PRIVATE else "+") + f"{t} {camel(col)}")
    tables[name] = (cols, fks)

def diagram(names):
    out = ["classDiagram", "    direction TB"]
    for t in names:
        cols, _ = tables[t]
        out.append(f"    class {pascal(t)} {{")
        out += [f"        {c}" for c in cols]
        out += [f"        +{m.split(' ')[0]} {m.split(' ')[1]}" for m in METHODS.get(pascal(t), [])]
        out.append("    }")
    for t in names:
        for col, ref, notnull, unique in tables[t][1]:
            if ref not in names:
                continue
            label = col[:-3] if col.endswith("_id") else col
            out.append(f'    {pascal(t)} "{"0..1" if unique else "0..*"}" --> "{"1" if notnull else "0..1"}" {pascal(ref)} : {camel(label)}')
    return "\n".join(out) + "\n"

(HERE.parent / "docs" / "diagrams" / "class_diagram.mmd").write_text(diagram(list(tables)), encoding="utf-8")
for f, names in GROUPS.items():
    (HERE.parent / "docs" / "diagrams" / f"{f}.mmd").write_text(diagram(names), encoding="utf-8")
print(f"{len(tables)} lớp, {sum(len(v[1]) for v in tables.values())} quan hệ")
