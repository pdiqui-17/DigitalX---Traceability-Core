# Traceability Core — chuỗi mè → dầu mè

Đồ án chuyên ngành · Đề tài #6 *Agricultural Digital Thread & Evidence-aware Traceability*

Lõi dữ liệu truy xuất **có minh chứng** cho chuỗi mè → dầu mè: truy ngược từ mã QR trên chai dầu về từng hoạt động canh tác, kèm trạng thái minh chứng và xác minh của từng hoạt động. Thiết kế dùng chung cho mọi cây trồng; cây cụ thể chỉ là cấu hình (crop profile).

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `db/` | Schema SQL (SQLite + PostgreSQL), trigger, view, bộ kiểm tra, sinh sơ đồ |
| `docs/` | Thiết kế schema (`D1_D2_schema_design.md`), nhật ký thay đổi (`CHANGELOG.md`), khảo sát giải pháp (`S1_khao_sat_giai_phap.md`), kế hoạch (`plan.md`), luồng test K6 (`K6_lac_test_flow.md`) |
| `docs/diagrams/` | UML class diagram (sinh tự động từ `db/schema.sql`) |

## Chạy kiểm tra

### 1. Demo kịch bản K1–K6 (dễ đọc, dùng để trình bày)

Đây là **bản chính cho K1–K6** (minh chứng E3, E4 trên Evidence Board).

```bash
cd db
python run_scenarios.py lac        # K1–K6 trên SQLite (mè + lạc đầu-cuối)
python run_scenarios.py lac --pg   # K1–K6 trên PostgreSQL (xem mục "Cấu hình PostgreSQL")
python run_scenarios.py lac --raw  # kèm câu SQL và dữ liệu thô (raw rows) DB trả về
python run_scenarios.py            # chỉ mè: K1–K5
```

Output in ra bảng có ✅/❌. Dùng `--raw` để xem nguyên văn câu SQL và từng dòng dữ liệu thật do DB trả về.  
Xem giải thích luồng K6 tại [`docs/K6_lac_test_flow.md`](docs/K6_lac_test_flow.md).

### 2. Bộ kiểm tra hồi quy đầy đủ (87 kiểm tra)

```bash
cd db
python smoke_test.py sqlite      # SQLite ≥ 3.35, không cần cài thêm
python smoke_test.py postgres    # PostgreSQL (xem mục "Cấu hình PostgreSQL")
```

Mỗi dòng in `[ĐẠT]` hoặc `[LỖI]` kèm chi tiết. Dòng cuối tổng kết `x/87 đạt`. Bộ này giữ các kiểm tra mà sổ quyết định trích dẫn cho tiêu chí O1/O2 (F1–F7, R1, R4, N1, N2, N9, N17, V9, V10, C1, C6…).

### 3. Xem trực tiếp dữ liệu thô từ SQLite CLI (100% không qua Python)

```bash
cd db
sqlite3 :memory: ".read inspect_raw.sql"
```

Chạy thẳng các truy vấn `SELECT` trên toàn bộ view cốt lõi (`v_lot_sources`, `v_lot_status`, `v_cycle_completeness`, `v_cycle_expected`, `v_activity_status`, `v_phi_violations`, `v_integrity_issues`, `v_lot_timeline`) để tự đối chiếu kết quả thật từ engine DB.

### Cấu hình PostgreSQL

1. Copy `db/.env.example` thành `db/.env` và điền `PGPASSWORD` (cùng `PGHOST`, `PGPORT`, `PGUSER` nếu khác mặc định). `db/.env` không được commit.
2. `PGDATABASE` (mặc định `traceability_test`) **bị xóa và tạo lại mỗi lần chạy**, nên tên bắt buộc kết thúc bằng `_test`.
3. Kiểm tra kết nối: `python dbtools.py` → `PostgreSQL OK (...): 27 bảng, 17 view, 31 trigger`.

Chỉ cần `psql` (cài cùng PostgreSQL), không cần thư viện Python nào. Ca phản biện độc lập cũng chạy được trên PostgreSQL: `python ../review/review_tests.py pg` (dùng chung `db/.env`).

### Lưu kết quả ra file

Dùng `--log`: script tự ghi file UTF-8, nên không bị lỗi font như khi dùng `>` hoặc `Out-File` trong PowerShell.

```bash
cd db
python run_scenarios.py lac --log logs/k1_k6_sqlite.txt
python run_scenarios.py lac --pg --log logs/k1_k6_postgres.txt
python smoke_test.py sqlite --log logs/smoke_sqlite.txt
python smoke_test.py postgres --log logs/smoke_postgres.txt
python ../review/review_tests.py --log logs/review_sqlite.txt
python ../review/review_tests.py pg --log logs/review_postgres.txt
```

Kết quả hiện tại (28/11/2026), log ở [`db/logs/`](db/logs/):

| Bộ | SQLite | PostgreSQL 18 |
|---|---|---|
| Kịch bản K1–K6 (`run_scenarios.py lac`) | 6/6 | 6/6 |
| Hồi quy (`smoke_test.py`) | 103/103 | 103/103 |
| Ca phản biện độc lập (`review/review_tests.py [pg]`) — phát hiện / đứng vững | 4 / 48 | 4 / 57 (thêm 9 ca trigger PG) |

4 phát hiện còn lại của bộ phản biện (G2, G4, RV5, RV8) là giới hạn đã ghi trong `docs/D1_D2_schema_design.md` mục 8; script in riêng chúng ở dòng "Đã ghi giới hạn".

## Thứ tự nạp schema

- SQLite: `schema.sql` → `triggers_sqlite.sql` → `views_sqlite.sql` (mỗi kết nối bật `PRAGMA foreign_keys = ON`)
- PostgreSQL: `schema.sql` → `triggers_postgres.sql` → `views_postgres.sql`

## Sau khi sửa schema

Trigger và view theo hệ được **sinh**, không sửa tay:

```bash
cd db
python3 gen_triggers.py              # → triggers_sqlite.sql, triggers_postgres.sql
python3 gen_views.py                 # → views_sqlite.sql, views_postgres.sql
python3 gen_diagram.py               # ghi .mmd vào docs/diagrams/
mmdc -i ../docs/diagrams/class_diagram.mmd -o ../docs/diagrams/class_diagram.png
```

## Trạng thái

Schema v0.5 (đã qua 4 vòng đánh giá, xem `docs/CHANGELOG.md`). K1–K6 đạt trên SQLite và PostgreSQL. Thiết kế API truy xuất và sơ đồ tuần tự quét QR: `docs/D1_D2_schema_design.md` mục 6B–6C. Việc tiếp theo: **trang QR (điều kiện nghiệm thu)**, rồi bộ mock mè đủ 11 bước theo quy trình Bình Thuận. Quyết định phạm vi: `docs/Project_Scope_Decision.txt`; phân công: `docs/plan.md`.
