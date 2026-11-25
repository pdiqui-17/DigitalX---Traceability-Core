# Traceability Core — chuỗi mè → dầu mè

Đồ án chuyên ngành · Đề tài #6 *Agricultural Digital Thread & Evidence-aware Traceability*

Lõi dữ liệu truy xuất **có minh chứng** cho chuỗi mè → dầu mè: truy ngược từ mã QR trên chai dầu về từng hoạt động canh tác, kèm trạng thái minh chứng và xác minh của từng hoạt động. Thiết kế dùng chung cho mọi cây trồng; cây cụ thể chỉ là cấu hình (crop profile).

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `db/` | Schema SQL (SQLite + PostgreSQL), trigger, view, bộ kiểm tra, sinh sơ đồ |
| `docs/` | Thiết kế schema (`D1_D2_schema_design.md`), nhật ký thay đổi (`CHANGELOG.md`), khảo sát giải pháp (`S1_khao_sat_giai_phap.md`), kế hoạch (`plan.md`) |
| `docs/diagrams/` | UML class diagram (sinh tự động từ `db/schema.sql`) |

## Chạy kiểm tra

```bash
cd db
python3 smoke_test.py sqlite        # SQLite ≥ 3.35, không cần cài thêm
python3 smoke_test.py postgres      # cần PostgreSQL 16 tạm qua ./pg_load.sh
```

Kết quả hiện tại: **87/87 đạt** trên cả SQLite và PostgreSQL (v0.5).

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

Schema v0.5 (đã qua 4 vòng đánh giá, xem `docs/CHANGELOG.md`). Việc tiếp theo: bộ dữ liệu mock đầy đủ theo quy trình mè đen Bình Thuận, kịch bản kiểm chứng K1–K6, trang QR demo. Xem `docs/plan.md`.
