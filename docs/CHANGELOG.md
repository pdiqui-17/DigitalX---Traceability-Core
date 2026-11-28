# CHANGELOG — Traceability Core (schema + tài liệu thiết kế)

> Đề tài #6 · ĐACN · chuỗi mè → dầu mè. File này ghi **mỗi phiên bản thay đổi gì, vì sao, kiểm bằng gì**.
> Cách cập nhật: thêm phiên bản mới **lên trên cùng**, theo đúng khuôn bên dưới; không sửa mục của phiên bản cũ (nếu phát hiện ghi sai thì thêm dòng "Đính chính" ở phiên bản mới).
> Mã kiểm tra (F, V, R, D, C, N) là mã trong `db/smoke_test.py`; mã phát hiện (B1, E1, …) là mã trong bộ ca thử của bên đánh giá.

Khuôn một phiên bản:

```
## [vX.Y] — YYYY-MM-DD — <nguồn thay đổi: đánh giá vòng N / yêu cầu của thầy / nhóm tự phát hiện>
Kiểm tra: <số đạt>/<tổng> trên SQLite và PostgreSQL
### Sửa lỗi        — lỗi đã tái hiện → cách sửa → mã kiểm tra
### Thay đổi thiết kế — quyết định mới hoặc đổi quyết định cũ (ghi mã QĐ)
### Hoãn / giới hạn — việc biết nhưng chưa làm, lý do
### Còn mở         — câu hỏi chờ thầy / F&S / nhóm
```

---

## [v0.5.1] — 2026-11-28 — nhóm chốt sổ quyết định SD-01…SD-18; ghi nhận họp với thầy (QR bắt buộc)
Kiểm tra: smoke_test **103/103** (87 + W1–W16) và K1–K6 6/6, trên SQLite và PostgreSQL 18; `review_tests` 0 phát hiện chưa xử lý (6 giới hạn đã ghi: SQLite 6 / 48, PostgreSQL 6 / 57) — log ở `db/logs/`. Bảng không đổi; thêm 4 trigger; `v_lot_timeline` chuyển sang `views_<hệ>.sql` và thêm cột `kind_rank`.
### Sửa lỗi
- K6 trước đây có hai bản: `F15` (hộ E, chỉ tới lô thu hoạch) và hộ D trong `run_scenarios.py`. Chốt **hộ D là bằng chứng K6 duy nhất**; `F15` giữ làm hồi quy cấu hình.
- `smoke_test.py postgres` không chạy được trên Windows (`pg_load.sh` dùng đường dẫn Linux). Thay bằng `db/dbtools.py`: kết nối qua `psql`, cấu hình ở `db/.env` (mẫu `.env.example`), database kiểm thử `*_test` bị xóa và tạo lại mỗi lần chạy. `F15` không còn dùng `sqlite_master`.
- Log chuyển hướng bằng PowerShell bị lỗi font (UTF-16 / sai bảng mã). Thêm `--log <file>`: script tự ghi UTF-8.
- `review/review_tests.py pg` cũng chuyển sang `dbtools.py` → chạy được trên Windows. Xóa `db/pg_load.sh` (chỉ chạy Linux, không còn nơi dùng) và `db/test_seeds.py` (11 kiểm tra đều đã có trong K1, K3, K6 và `smoke_test`). Phần SQLite giữ nguyên 14 phát hiện / 38 ca như trước khi sửa.
- Nhóm ca thử mới của bên đánh giá trên v0.5 (trước ghi N1–N13, trùng mã N1–N30 của `smoke_test` mà E4 dẫn) đổi thành **RV1–RV13**; script in riêng các phát hiện đã ghi giới hạn. Chi tiết từng mã: `D1_D2_schema_design.md` mục 0a.
- **[Cao, QR] RV7** — thêm đầu vào vào sự kiện đóng chai sau khi QR lưu hành → đầu vào phải ghi cùng ngày ghi sự kiện, bổ sung sau chỉ khi đang bị từ chối. (W9)
- **[Cao, QR] RV12** — sửa thông tin hộ / lô đất đã sinh lô → khóa khi đã có lô thu hoạch. (W12–W14)
- **[Cao, QR] RV13** — `lot_created` theo giờ nạp → theo thời điểm nghiệp vụ; thêm `kind_rank`. (W15, W16, V6)
- **[Cao] RV1, RV2** — thêm cấu hình vào crop profile đang dùng đổi kết luận hồi tố → chặn, buộc tạo phiên bản mới. (W1–W3)
- **[TB] RV3** chu kỳ đã đóng nhận ngày làm sau ngày đóng → chặn (W4, W5) · **RV4** đóng chu kỳ chỉ xét bản ghi hiện hành (W6) · **RV6** sự kiện bị từ chối được bổ sung đầu vào (W7, W8) · **RV11** lần ghi thứ 2 của hoạt động bắt buộc thiếu ảnh làm chu kỳ chưa đủ (W11).
- **[Thấp] RV10** — sha256 khác hoa/thường → đếm theo `LOWER(sha256)`. (W10)
- Fixture: N17, C13 (`smoke_test`) và nhóm G (`review_tests`) tạo cấu hình trước khi có chu kỳ (khóa RV1/RV2); V6 sắp theo `at, kind_rank`.
- **P8 (PostgreSQL, lộ ra khi chạy được `review_tests.py pg`):** `v_lot_timeline` lọc số đo IoT theo khoảng chu kỳ bằng cách so chuỗi (`SUBSTR(CAST(observed_at AS TEXT),1,10)` với `CAST(started_at AS TEXT)`). Phiên có `DateStyle = 'SQL, DMY'` cho chuỗi dạng `28/11/2026` → mất số đo (ISO: `o_close,o_in`; DMY: chỉ `o_close`). Sửa: chuyển view từ `schema.sql` sang `gen_views.py`, so bằng kiểu ngày (`date(...)` ở SQLite, `::date` ở PostgreSQL). Tổng số view vẫn 17. Sau sửa P8: `review_tests.py pg` 14 phát hiện / 47 ca đứng vững; sau sửa nhóm RV: 4 / 57 (SQLite 4 / 48), 4 phát hiện còn lại đều là giới hạn đã ghi.
### Thay đổi thiết kế
- `run_scenarios.py` là bản chính cho K1–K6, chạy được SQLite và PostgreSQL (`--pg`). Kiểm tra "UPDATE bị chặn" ở K5 giờ đòi đúng thông báo của trigger chỉ-ghi-thêm.
- `D1_D2_schema_design.md`: thêm 6A (độ đầy đủ 4 cấp — SD-07; nhãn hiển thị — SD-13; "bị từ chối" trên QR — SD-12; rút lại liên kết — SD-10; dịch vụ trung tâm — SD-06), 6B danh sách API A1–A7 + mã lỗi, 6C sơ đồ tuần tự quét QR (`docs/diagrams/qr_sequence.mmd`), 6D điều kiện nghiệm thu trang QR. Mục 6 bỏ "11 bước" khỏi tiêu chí O1 (SD-02).
- SD-14 chốt: trang QR là điều kiện nghiệm thu (họp với thầy; mô tả đề tài #6).
### Hoãn / giới hạn
- `v_activity_display_state` (SD-13) và `evidence_link_retraction` (SD-10): mới thiết kế, cài đặt ngay sau 29/11, trước trang QR.
- `docs/diagrams/qr_sequence.png` chưa xuất (máy chưa có `mmdc`); GitHub hiển thị khối Mermaid trong D1_D2 mục 6C.
- Ghi giới hạn (D1_D2 mục 8): RV5 đóng nhầm ngày (dòng 7b); RV8 nạp lại dữ liệu trùng trên SQLite (dòng 16); đầu vào ghi SAI cần `lot_supersession` (dòng 17); đính chính thông tin hộ / lô đất (dòng 18); `recorded_at` do client gửi (dòng 19; nói rõ là ghi lùi ngày thì vượt được quy tắc RV7).
- **Nhóm tự phát hiện (28/11), ghi giới hạn, sửa cùng đợt trang QR:** **[Cao, QR] RV14**: thêm yêu cầu minh chứng theo loại sự kiện lô làm chai đã in QR đổi `complete` thành `incomplete`, do `f_config_in_use` chỉ khóa yêu cầu theo loại hoạt động (mục 8 dòng 7c, hướng sửa `valid_from`). **[TB] RV15**: thêm luật cách ly sau thu hoạch đổi kết luận PHI, không có dấu vết thời điểm thêm (dòng 20, hướng sửa `recorded_at` + cờ hiển thị). Có ca tái hiện trong `review/review_tests.py`.
- Đính chính: README mục 2 và bảng file ở D1_D2 còn ghi "87 kiểm tra" → 103.
### Còn mở
- Dung sai ngày `tolerance_days` (hỏi thầy / F&S).

---

## [v0.5] — 2026-11-25 — đánh giá độc lập vòng 4

Kiểm tra: **87/87** trên SQLite 3.53 và PostgreSQL 16 (57 cũ + 30 mới N1–N30).
Nguồn: agent đánh giá không tham gia thiết kế tự viết ~40 ca thử phá trên v0.4 → 30 phát hiện tái hiện được, 10 ca đứng vững.

### Sửa lỗi
- **[Cao] B1, B2** — sự kiện chưa ghi đầu vào làm lô hiện `fully_traced`. → Lô có sự kiện tạo ra nhưng không có `lot_input` = `untraceable`; `trace_state` thêm `untraceable`, `share_inconsistent`; `fully_traced` chỉ khi phần truy được = 100%. (N1, N2)
- **[Cao] C1** — sự kiện gộp ghi đầu ra là lô thu hoạch → tỷ trọng 200%. → Trigger kiểm loại lô đầu ra khớp loại sự kiện; cảnh báo `lot_type_mismatch`, `share_sum_mismatch` cho dữ liệu cũ. (N3)
- **[Cao] D2–D4** — SQLite `INSERT OR REPLACE` vượt cơ chế chỉ ghi thêm. → Trigger BEFORE INSERT chặn trùng khóa chính/khóa duy nhất trên mọi bảng chỉ ghi thêm; PostgreSQL thêm BEFORE TRUNCATE. (N4–N6)
- **[Cao] E1, E2, E4** — sửa `closed_at` biến "thiếu" thành "chưa đến hạn"; mở lại chu kỳ; đổi `cycle_id`. → `closed_at` chỉ NULL → ngày, một lần, không trước hoạt động cuối; chu kỳ đã đóng không bao giờ `not_due`; khóa `cycle_id`. (N7–N11)
- **[TB] F1** — hoạt động có điều kiện thiếu minh chứng không ảnh hưởng chu kỳ. → `n_other_problem`. (N12)
- **[TB] I1–I4** — sửa cấu hình/lô đất/chủ hộ đổi kết luận lịch sử. → 5 bảng cấu hình chỉ ghi thêm; khóa `plot.farm_id`, `plot.code`, `farm.owner_agent_id`. (N13–N16)
- **[TB] J1** — một file tải 2 lần tính 2 minh chứng. → Đếm theo `sha256`. (N17)
- **[TB] K1, K2** — dùng quá khối lượng; sai thứ tự thời gian. → Cảnh báo `over_consumption`, `event_time_order`. (N18, N19)
- **[TB] K3** — thêm đầu vào hồi tố đổi tỷ trọng QR đã in. → `lot_input.recorded_by/recorded_at`; chặn khi lô ra đã dùng tiếp hoặc sự kiện đã xác minh. (N20, N21)
- **[Thấp] L1** số bản nhảy cóc (N22) · **L2** hoạt động trước ngày bắt đầu chu kỳ → cảnh báo mềm (N23) · **L3** `import` bắt buộc `external_ref` (N24).
- **[Thấp] H2–H4** — `undetermined_share`, `no_source_event`, `not_required`. (N25–N27)
- **[Thấp] G1, G3, G5, G8** — timeline thêm sửa/xác minh bản ghi lô, số đo trong ngày đóng, nhãn "bản ghi cũ". (N28–N30)

### Thay đổi thiết kế
- Trigger và view theo hệ **sinh tự động** (`gen_triggers.py`, `gen_views.py`) để SQLite và PostgreSQL không lệch.
- `v_integrity_issues` chuyển từ `schema.sql` sang `views_<hệ>.sql` (cần so ngày).
- Cấu hình (crop profile, giai đoạn, loại hoạt động, yêu cầu minh chứng, luật cách ly) chỉ ghi thêm: đổi quy trình = phiên bản crop profile mới.
- Bộ kiểm tra: kỳ vọng "unique" chấp nhận thông báo `trùng khóa` của trigger chặn ghi đè.

### Hoãn / giới hạn
- G2 chu kỳ thu hoạch nhiều đợt; G4 hai chu kỳ chồng nhau trên một lô đất → ĐATN.
- Đóng chu kỳ nhầm ngày chưa có cách đính chính; yêu cầu minh chứng theo loại sự kiện lô chưa có hiệu lực theo ngày.
- Hiệu năng: view tính cho mọi lô (`v_lot_status` ~1,5 s ở 2.000 lô theo số đo trên v0.4) → trang QR cần truy vấn tham số hóa.

### Còn mở
- Đối chiếu nhãn thuốc thật cho luật cách ly (đang `is_assumption = 1`).
- Hỏi thầy: dung sai ngày (`tolerance_days`); có hiện "bị từ chối" trên trang QR không.

---

## [v0.4] — 2026-11-25 — đánh giá vòng 3 (điểm 3.1–3.6)

Kiểm tra: **57/57** trên SQLite và PostgreSQL (thêm V1–V11, C14–C20).

### Sửa lỗi
- **3.1** trạng thái QR bỏ qua minh chứng khâu sau thu hoạch → `v_lot_ancestors`, `v_lot_chain_events`; `v_lot_status` thêm `chain_evidence_state`. (V1–V4)
- **3.2a** `anchor_date` sửa lặng lẽ → bảng `cycle_anchor` chỉ ghi thêm, bản ≥ 2 bắt buộc lý do; `cultivation_cycle` chỉ cho UPDATE `closed_at`, chặn DELETE. (V10, C14–C16, C20)
- **3.2b** `created_by`/`created_at` cho các bảng còn sửa được. **3.2c** `source_channel` + `external_ref`, UNIQUE chống nạp trùng. (V8, C17, C18)
- **Nhóm tự phát hiện:** dời mốc gieo mà chu kỳ vẫn `complete` → `on_schedule_ratio` tách khỏi `cycle_state` (V9, V10); bộ kiểm tra có thể đạt giả → `blocked()` bắt buộc khớp loại lỗi (C19).

### Thay đổi thiết kế
- Bảng `season` (vụ là thực thể). (V7)
- `v_lot_timeline` — digital timeline hợp nhất mốc chu kỳ, hoạt động, số đo, sự kiện lô, xác minh. (V5, V6)
- Điểm 3.5 (sửa bản ghi làm "mất" minh chứng) giữ nguyên là chủ đích; 3.6a `conditional` đã có logic.

### Hoãn / giới hạn
- 3.6b, c: minh chứng cảm biến theo khoảng thời gian, thiết bị đa đại lượng → ĐATN.

---

## [v0.3] — 2026-11-25 — đánh giá vòng 2 · commit đầu tiên `bf7b0a8`

Kiểm tra: **39/39** trên SQLite và PostgreSQL.

### Sửa lỗi (5/5 lỗi bên đánh giá tái hiện được)
- Nguồn không truy được bị bỏ im lặng → `source_status` + `untraceable_share`. (R1, R1b)
- Dữ liệu có vòng làm treo truy vấn → trigger chặn vòng khi ghi. (R2)
- Một file liên kết 2 lần được đếm 2 → `COUNT(DISTINCT)` + UNIQUE theo đích. (R3)
- "Đã xác minh" che "thiếu minh chứng" → tách `evidence_completeness` / `verification_state`. (R4)
- Từ chối rồi đạt → chuỗi thay thế, mỗi đối tượng một kết luận hiệu lực (QĐ6). (R5a, R5b)
- Một hoạt động thu hoạch sinh 2 lô; hai sự kiện cùng tạo một lô. (D1–D3)

### Thay đổi thiết kế
- Xác minh gắn được bản ghi hoạt động / bản ghi lô / sự kiện lô; yêu cầu minh chứng cho cả loại sự kiện lô.
- `v_cycle_expected`, `v_cycle_completeness`, `v_lot_destinations`, `v_integrity_issues`; trigger chỉ ghi thêm trên 11 bảng.
- `material_crop_rule` (cách ly theo cây trồng); nguồn luật + cờ giả định; hai vai người làm / người ghi; số đo lưu vị trí lúc đo; danh mục đơn vị; index.
- Class diagram sinh tự động từ SQL (`gen_diagram.py`).
- Không theo đề xuất "trạng thái mâu thuẫn" của bên đánh giá (thay bằng chuỗi thay thế).

---

## [v0.2] — trước 2026-11-25 — đánh giá vòng 1

Đối chiếu nhận xét của bên đánh giá 1 với hướng thiết kế sau buổi thầy chốt scope; sửa toàn bộ các điểm đúng. Thiết kế cũ của nhóm (trước khi align với lab của thầy) không đưa vào — được phân tích riêng.
Chi tiết từng điểm: xem lịch sử ở `D1_D2_schema_design.md` mục 4 (các dòng "Loại: … (v0.2)").

## [v0.1] — trước 2026-11-25 — thiết kế ban đầu

Canonical data model đầu tiên theo đề tài #6, scope cây mè: crop profile là dữ liệu (`crop_profile → stage → activity_type → evidence_requirement`), bản ghi chỉ ghi thêm, minh chứng + xác minh, đồ thị lô kiểu EPCIS (Aggregation/Transformation), ánh xạ W3C PROV-O. Kèm UML class diagram.
