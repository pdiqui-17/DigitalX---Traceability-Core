# D1/D2 — Canonical data model cho Traceability Core (v0.5)

> Đề tài #6 · ĐACN · chuỗi mè → dầu mè · 25/11/2026
> Trạng thái: bản để nhóm và bên đánh giá phản biện.
> Cập nhật 28/11/2026: thêm mục 6A–6D (định nghĩa độ đầy đủ, nhãn hiển thị, rút lại liên kết, dạng của lõi, danh sách API, sơ đồ tuần tự QR) theo sổ quyết định `Project_Scope_Decision.txt` (SD-06, SD-07, SD-10, SD-12, SD-13, SD-14).
> **Đã kiểm (28/11):** 103 kiểm tra hồi quy (`smoke_test.py`) **103/103 đạt** và 6 kịch bản K1–K6 (`run_scenarios.py`) **6/6 đạt**, trên cả **SQLite** và **PostgreSQL 18** — log ở `db/logs/`. (v0.5 trước đó đã chạy 87/87 trên SQLite 3.53 và PostgreSQL 16; v0.5.1 thêm W1–W16 cho các phát hiện RV, mục 0a.) Ngoài ra một agent đánh giá độc lập (không viết schema) chạy bộ ca thử phá riêng — xem mục 0. Mỗi ca "bị chặn" phải khớp đúng loại lỗi mong đợi (CHECK / UNIQUE / khóa ngoại / thông báo của trigger) — tránh đạt giả do sai số cột hay sai cú pháp.

## Các file

| File | Nội dung |
|---|---|
| `schema.sql` | 27 bảng, ràng buộc, index, 11 view dùng chung (SQL chuẩn) |
| `triggers_sqlite.sql` / `triggers_postgres.sql` | **Sinh bởi `gen_triggers.py`.** Chỉ ghi thêm (kể cả bảng cấu hình), chặn ghi đè, số bản tăng đúng 1, đóng chu kỳ, khóa lô đất/nông hộ, loại lô đầu ra, cạnh lô, lô thu hoạch, luật xác minh |
| `views_sqlite.sql` / `views_postgres.sql` | **Sinh bởi `gen_views.py`.** 6 view có phép so ngày: lịch dự kiến, độ đầy đủ chu kỳ, trạng thái lô, vi phạm cách ly, kiểm nhất quán, digital timeline |
| `run_scenarios.py` | **Bản chính cho K1–K6** (minh chứng E3, E4): `python run_scenarios.py lac` (SQLite) hoặc `lac --pg` (PostgreSQL); `--log <file>` ghi log UTF-8 |
| `seed_me.sql`, `seed_lac.sql` | Bộ mock cho K1–K6: 3 hộ mè + chu kỳ chưa có ngày gieo; hộ D trồng lạc (chỉ INSERT) |
| `smoke_test.py` | 103 kiểm tra hồi quy: `python smoke_test.py sqlite` hoặc `postgres` |
| `dbtools.py` | Kết nối dùng chung SQLite / PostgreSQL (qua `psql`, cấu hình `db/.env`, mẫu `db/.env.example`) và ghi log UTF-8 |
| `logs/` | Log kết quả chạy thật — Evidence Board dẫn thẳng tới đây |
| `gen_diagram.py` | **Sinh class diagram tự động từ `schema.sql`** → sơ đồ không lệch SQL |
| `class_diagram.png` + `cd_1_canh_tac.png`, `cd_2_lo.png`, `cd_3_minh_chung_xac_minh.png` | Sơ đồ đầy đủ (phụ lục) + 3 sơ đồ con (chương thiết kế) |

**Thứ tự nạp:** `schema.sql` → `triggers_<hệ>.sql` → `views_<hệ>.sql`. SQLite: mỗi kết nối chạy `PRAGMA foreign_keys = ON`.

---

## 0. Thay đổi v0.5 (đánh giá độc lập vòng 4)

v0.4 đạt 57/57 nhưng bộ kiểm tra do chính người thiết kế viết. Vòng 4 giao cho một agent **không tham gia thiết kế** đọc đề bài + schema và tự viết ca thử phá (`review_tests.py`, ~40 ca). Kết quả trên v0.4: **30 phát hiện tái hiện được**, 10 ca đứng vững. Bốn lỗi mức Cao đều cùng một kiểu: hệ thống đưa ra **kết luận lạc quan sai** — trái nguyên tắc "thiếu phải hiện là thiếu" của đề bài.

| Mức | Mã | Lỗi (đã tái hiện) | Sửa | Kiểm tra |
|---|---|---|---|---|
| Cao | B1, B2 | Sự kiện đóng gói/gộp chưa ghi đầu vào → lô vẫn `fully_traced`; phần 40% từ lô "rỗng" biến mất | `v_lot_sources`: lô không phải thu hoạch mà sự kiện tạo ra **không có đầu vào** = `untraceable`. `trace_state` thêm `untraceable`, `share_inconsistent`; `fully_traced` chỉ khi phần truy được = 100% | N1, N2 |
| Cao | C1 | Sự kiện gộp ghi đầu ra là lô thu hoạch → tỷ trọng 200% | Trigger: loại lô đầu ra phải khớp loại sự kiện (gộp → aggregated, chế biến → processed, đóng gói → packaged). `v_integrity_issues` thêm `lot_type_mismatch`, `share_sum_mismatch` cho dữ liệu cũ | N3 |
| Cao | D2–D4 | SQLite `INSERT OR REPLACE` xóa dòng cũ mà không chạy trigger DELETE → đổi mốc gieo, khối lượng cạnh lô, ngày làm không để lại dấu vết | Trigger BEFORE INSERT trên mọi bảng chỉ ghi thêm: trùng khóa chính hoặc khóa duy nhất (kể cả UNIQUE một phần) → `trùng khóa (không ghi đè)`. PostgreSQL: UPSERT đã bị trigger UPDATE chặn; thêm BEFORE TRUNCATE | N4–N6 |
| Cao | E1, E2, E4 | `closed_at` là cột duy nhất được UPDATE và không có lịch sử: dời ngày đóng về trước hạn làm việc "thiếu" thành "chưa đến hạn" → chu kỳ `complete`; mở lại chu kỳ; đổi khóa `cycle_id` | `closed_at` chỉ đi NULL → ngày, **một lần**, không trước hoạt động cuối của chu kỳ. `v_cycle_expected` **không bao giờ** trả `not_due` khi chu kỳ đã đóng. Trigger bảo vệ cả `cycle_id` | N7–N11 |
| TB | F1 | Hoạt động có điều kiện (phun thuốc) đã ghi mà thiếu ảnh vẫn để chu kỳ `complete` | `n_other_problem` trong `v_cycle_completeness` | N12 |
| TB | I1–I4 | Sửa cấu hình (hạ "bắt buộc" thành "tùy chọn", xóa yêu cầu minh chứng) đổi kết luận của chu kỳ cũ; chuyển lô đất sang hộ khác; đổi chủ hộ | 5 bảng cấu hình chỉ ghi thêm (đổi quy trình = phiên bản crop profile mới). Khóa `plot.farm_id/code`, `farm.owner_agent_id` | N13–N16 |
| TB | J1 | Cùng một file tải 2 lần thỏa "cần 2 ảnh" | Đếm `DISTINCT` theo `sha256` | N17 |
| TB | K1, K2 | Dùng quá khối lượng lô; đóng chai trước khi ép | Cảnh báo `over_consumption`, `event_time_order` (`v_integrity_issues` chuyển sang file view theo hệ vì cần so ngày) | N18, N19 |
| TB | K3 | Thêm đầu vào vào sự kiện ép dầu đã xong, sau khi chai đã bán → đổi tỷ trọng QR hồi tố | `lot_input` có `recorded_by`, `recorded_at`; trigger chặn thêm đầu vào khi lô ra đã được dùng tiếp hoặc sự kiện đã được xác minh | N20, N21 |
| Thấp | L1 | Số bản ghi nhảy cóc (1 → 5) | `revision_no` phải = lớn nhất + 1 (`activity_revision`, `lot_revision`, `cycle_anchor`) | N22 |
| Thấp | L2 | Hoạt động ghi ngày trước khi chu kỳ bắt đầu | Cảnh báo mềm `activity_before_cycle_start` — không chặn cứng vì `started_at` không sửa được, chặn sẽ làm mất dữ liệu ghi muộn | N23 |
| Thấp | L3 | Bản ghi kênh `import` không có mã ngoài → không chống nạp trùng | CHECK: `import` bắt buộc `external_ref` | N24 |
| Thấp | H2–H4 | Lô từ chu kỳ chưa có mốc gieo lẫn với "thiếu"; lô mồ côi báo `no_post_harvest_events`; mốc không có yêu cầu minh chứng báo `complete` | `undetermined_share`; `no_source_event`; `not_required` | N25–N27 |
| Thấp | G1, G3, G5, G8 | Timeline thiếu xác minh/sửa bản ghi lô; số đo trong ngày đóng bị loại; xác minh của bản ghi cũ trình bày như hiện hành | Timeline thêm `lot_revision` (tạo/sửa) và xác minh bản ghi lô; so số đo ở mức ngày; nhãn `(bản ghi cũ)` | N28–N30 |
| — | G2, G4 | Chu kỳ thu hoạch nhiều đợt; hai chu kỳ chồng nhau trên một lô đất | **Hoãn, ghi giới hạn** (mục 8) | — |

## 0a. Thay đổi v0.5.1 (đánh giá độc lập chạy lại trên v0.5)

Bộ phản biện có thêm nhóm ca thử nhắm vào chính các bản sửa v0.5 (`run_new_v05` trong `review/review_tests.py`). Nhóm này trước ghi mã N1–N13, trùng mã N1–N30 của `smoke_test.py` mà E4 đang dẫn, nên đổi thành **RV1–RV13**. Kết quả trước khi sửa: 11 phát hiện chưa ai phân loại. Thêm P8 lộ ra khi `review_tests.py pg` chạy được trên Windows.

| Mức | Mã | Vấn đề | Sửa | Kiểm tra |
|---|---|---|---|---|
| Cao (QR) | RV7 | Thêm đầu vào vào sự kiện đóng chai 3 tháng sau → tỷ trọng nguồn trên QR đổi hồi tố. Lô chai là lô cuối chuỗi nên lọt quy tắc "đã dùng tiếp" | Đầu vào phải ghi cùng ngày ghi sự kiện; bổ sung sau đó chỉ khi kết luận hiệu lực là `rejected`. **Giới hạn:** quy tắc so hai giá trị `recorded_at` do client gửi lên, nên client ghi lùi ngày là vượt được (mục 8 dòng 19) | W9 |
| Cao (QR) | RV12 | Sửa tên/tỉnh/xã hộ, toạ độ/mã vùng trồng của lô đất đã sinh lô → trang QR đổi theo, không lịch sử | Khóa các trường này khi lô đất đã sinh lô thu hoạch; trước đó vẫn sửa được | W12–W14 |
| Cao (QR) | RV13 | Mốc `lot_created` lấy giờ nạp → đứng trước cả hoạt động canh tác | Lấy thời điểm sự kiện / hoạt động thu hoạch tạo lô; thêm `kind_rank` để sắp khi trùng giờ | W15, W16, V6 |
| Cao | RV1, RV2 | Thêm yêu cầu minh chứng / loại hoạt động vào crop profile đang dùng → chu kỳ đã đóng đổi kết luận hồi tố | Crop profile đã có chu kỳ thì không thêm giai đoạn / loại hoạt động / yêu cầu minh chứng → tạo phiên bản mới | W1–W3 |
| TB | RV3 | Chu kỳ đã đóng vẫn nhận bản ghi có ngày làm sau ngày đóng | Trigger chặn; ghi muộn việc làm trước ngày đóng vẫn được | W4, W5 |
| TB | RV4 | Không đóng được chu kỳ khi chỉ bản ghi CŨ (đã sửa) có ngày sau ngày đóng | Chỉ xét bản ghi hiện hành | W6 |
| TB | RV6 | Sự kiện bị từ chối vì thiếu đầu vào thì không bổ sung được (trigger khóa khi có BẤT KỲ lần xác minh nào) | Chỉ khóa khi kết luận hiệu lực là `verified`. Dấu vết: ghi chú từ chối → `lot_input.recorded_by/at` → `supersede_reason` của lần xác minh lại | W7, W8 |
| TB | RV11 | Lần ghi thứ 2 của hoạt động bắt buộc thiếu ảnh không làm chu kỳ chưa đủ | `n_other_problem` đếm mọi hoạt động có vấn đề chưa được xét ở `v_cycle_expected` | W11 |
| Thấp | RV10 | Cùng file, sha256 khác hoa/thường đếm thành 2 | Đếm theo `LOWER(sha256)`. Không thêm CHECK định dạng vì bộ mock dùng sha giả; kiểm định dạng ở tầng ứng dụng | W10 |
| Thấp | P8 | Timeline lọc số đo bằng so chuỗi → phụ thuộc `DateStyle` của phiên PostgreSQL | So bằng kiểu ngày; view chuyển sang `gen_views.py` | P8 (review pg) |
| — | RV5, RV8 | Đóng chu kỳ nhầm ngày; SQLite không phân biệt `INSERT OR IGNORE` với `INSERT` | **Ghi giới hạn** (mục 8 dòng 7b, 16) | — |
| Cao (QR) | RV14 *(nhóm tự phát hiện)* | Thêm yêu cầu minh chứng cho loại sự kiện `packaging` → `lot_b80`, `lot_b250` (đã in QR) đổi từ `complete` sang `incomplete`. `f_config_in_use` chỉ khóa yêu cầu có `activity_type_id`; yêu cầu theo `lot_event_type` không gắn crop profile nên lọt | **Ghi giới hạn** (mục 8 dòng 7c); sửa cùng đợt trang QR | RV14 (review) |
| TB | RV15 *(nhóm tự phát hiện)* | Thêm luật cách ly cho cặp (thuốc, cây) đang thiếu sau khi vụ đã thu hoạch → kết luận PHI đổi hồi tố, không có dấu vết thời điểm thêm | **Ghi giới hạn** (mục 8 dòng 20); sửa cùng đợt trang QR | RV15 (review) |

Fixture phải đổi theo khóa cấu hình: N17 và C13 (`smoke_test`), nhóm G (`review_tests`) trước đây thêm loại hoạt động vào profile đang có chu kỳ cho tiện; nay tạo cùng phần cấu hình, hoặc dùng profile chưa có chu kỳ. Ý đồ ca thử giữ nguyên.

**Cách làm để không sửa lệch giữa hai hệ:** trigger và view theo hệ giờ sinh từ một nguồn (`gen_triggers.py`, `gen_views.py`); sửa nguồn rồi chạy lại, không sửa tay file `.sql` sinh ra.

## 0'. Thay đổi v0.4 (theo đánh giá vòng 3)

Nhóm chạy thử các điểm đánh giá trên schema v0.3 trước khi sửa: điểm 3.1 tái hiện được (ép dầu thiếu ảnh nhưng QR-80 vẫn `fully_traced`), điểm 3.2 tái hiện được (UPDATE `anchor_date` không để lại dấu vết). Khi tái hiện 3.2 phát hiện thêm một lỗi bên đánh giá chưa nêu: dời mốc gieo làm mọi hoạt động lệch lịch nhưng chu kỳ vẫn `complete`, vì chưa có chiều đúng hạn.

| # | Vấn đề | Kết luận | Sửa | Kiểm tra |
|---|---|---|---|---|
| 3.1 | Trạng thái QR bỏ qua minh chứng khâu sau thu hoạch | Đúng, tái hiện được | `v_lot_ancestors` + `v_lot_chain_events` (mọi sự kiện tạo ra lô tổ tiên + mốc thu mua/vận chuyển của chúng). `v_lot_status` thêm `n_chain_events`, `n_chain_missing_evidence`, `n_chain_rejected`, `chain_evidence_state` (complete / incomplete / rejected / no_post_harvest_events) | V1–V4 |
| 3.2a | `anchor_date` sửa lặng lẽ | Đúng, tái hiện được | Bảng `cycle_anchor` chỉ ghi thêm (bản ≥ 2 bắt buộc lý do). `cultivation_cycle` bỏ cột `anchor_date`; trigger chỉ cho UPDATE `closed_at`, chặn DELETE | V10, C14–C16, C20 |
| 3.2b | Thiếu `created_by` ở bảng còn sửa được | Đúng | `created_by` + `created_at` cho `farm`, `plot`, `cultivation_cycle`, `certification`, `device`, `season` | (schema) |
| 3.2c | Không biết bản ghi đến từ kênh nào | Đúng | `source_channel` (app / import / iot_gateway / admin / mock) + `external_ref` cho `activity`, `lot`, `lot_event`, `evidence`, `observation`; UNIQUE (kênh, mã ngoài) chống nạp trùng | V8, C17, C18 |
| 3.3 | Vụ chưa là thực thể | Đúng | Bảng `season` (tổ chức, tên vụ, cây trồng, khoảng thời gian); chu kỳ tham chiếu `season_id` (cây lâu năm để NULL). `v_integrity_issues` báo chu kỳ thuộc vụ của cây khác | V7 |
| 3.4 | Chưa có digital timeline | Đúng | `v_lot_timeline` hợp nhất mốc chu kỳ, hoạt động (kèm 2 chiều trạng thái), số đo tại lô đất nguồn trong khoảng chu kỳ, sự kiện lô trên chuỗi, các lần xác minh (đánh dấu lần thay thế) | V5, V6 |
| 3.5 | Sửa bản ghi làm "mất" minh chứng | Đúng một phần — là chủ đích | Giữ nguyên; viết thành câu trả lời cho hội đồng (mục 10) | F2 |
| 3.6a | `conditional` chưa có logic | Sai một phần | Có logic: không tính vào lịch bắt buộc, nhưng đã ghi thì vẫn chấm minh chứng, vật tư, cách ly. Điều kiện kích hoạt: ĐATN (mục 10) | F10 |
| 3.6b, c | Minh chứng cảm biến theo từng số đo; thiết bị một đại lượng | Đúng | Giữ trong danh sách ĐATN | — |
| Thêm | Dời mốc gieo, chu kỳ vẫn `complete` | Lỗi mới (nhóm tự phát hiện) | `v_cycle_completeness` thêm `n_on_schedule`, `on_schedule_ratio` (KPI "nhật ký đúng hạn"), tách khỏi `cycle_state` | V9, V10 |
| Thêm | Bộ kiểm tra có thể đạt giả | Lỗi mới (nhóm tự phát hiện) | `blocked()` bắt buộc khớp loại lỗi; một ca cũ đạt nhờ sai số cột đã được sửa (C19) | toàn bộ C, R, D |

## 0''. Thay đổi v0.3 (theo đánh giá vòng 2)

Bên đánh giá đã chạy thử các view và tái hiện được lỗi. Nhóm chạy lại trên schema đầy đủ: **5/5 lỗi tái hiện được**. Bảng dưới là cách sửa và kiểm tra hồi quy tương ứng.

### 0.1 Lỗi đã tái hiện

| # | Lỗi | Sửa | Kiểm tra |
|---|---|---|---|
| 1 | Nguồn không truy được bị bỏ im lặng (P1 40% biến mất) | Dùng `v_lot_sources` theo đề xuất của bên đánh giá: thêm `source_status` = `harvest` / `untraceable` / `depth_limit_reached`. `v_lot_status` tính `untraceable_share` | R1, R1b |
| 2 | Dữ liệu có vòng làm treo mọi truy vấn | **Chặn ngay khi ghi**: trigger kiểm vòng trên `lot_input` (truy vấn đệ quy, cả hai hệ). Giới hạn độ sâu 20 trong view chỉ là lưới an toàn cho dữ liệu cũ | R2 |
| 3 | Một file liên kết 2 lần được đếm 2 | `COUNT(DISTINCT evidence_id)` + UNIQUE index từng loại đích của `evidence_link` | R3 |
| 4 | Đã xác minh che mất việc thiếu minh chứng | **Tách 2 cột:** `evidence_completeness` (complete / missing_evidence / missing_inputs) và `verification_state` (unverified / verified / rejected) | R4 |
| 5 | Từ chối rồi đạt → lấy lần mới nhất | **Mỗi đối tượng một kết luận hiệu lực.** Lần sau phải ghi rõ thay thế lần nào (`supersedes_verification_id` + lý do); trigger chặn lần xác minh không thay thế. Không cần trạng thái "mâu thuẫn" (xem QĐ6) | R5a, R5b |
| 0 | SQLite mặc định tắt khóa ngoại | Ghi quy ước; bộ kiểm tra bật và có ca kiểm khóa ngoại | R0 |
| D | Hai lô cùng một hoạt động thu hoạch; lô thu hoạch trỏ hoạt động không phải thu hoạch; hai sự kiện cùng tạo một lô | `UNIQUE (lot.harvest_activity_id)`, trigger kiểm `produces_lot`, `UNIQUE (lot_event.output_lot_id)` | D1, D2, D3 |

### 0.2 Vấn đề thiết kế khác

| Vấn đề | Kết luận | Sửa |
|---|---|---|
| Xác minh và trạng thái chỉ phủ hoạt động | Đúng | `verification` gắn được bản ghi hoạt động / bản ghi lô / sự kiện lô (đúng một). View `v_lot_event_status`, `v_lot_revision_status`, `v_lot_status` |
| Yêu cầu minh chứng chỉ cho loại hoạt động | Đúng | `evidence_requirement` gắn loại hoạt động **hoặc** loại sự kiện lô (vd gộp lô cần phiếu cân) |
| Thiếu view độ đầy đủ theo chu kỳ (hoạt động bắt buộc vắng mặt) | Đúng, quan trọng nhất | `v_cycle_expected` + `v_cycle_completeness`. `anchor_date` NULL → `undetermined`, không phải "thiếu" |
| Thiếu truy xuôi | Đúng | `v_lot_destinations` + index `lot_input(input_lot_id)` |
| Kiểm nhất quán liên bảng | Đúng | `v_integrity_issues`: lô mồ côi, sự kiện không đầu vào, mốc có đầu vào, thu hoạch chưa sinh lô, thuốc chưa có luật cách ly, khác đơn vị, vòng |
| "Chỉ ghi thêm" chỉ ở tầng ứng dụng | Đúng | Trigger chặn UPDATE/DELETE trên 11 bảng |
| Thời gian cách ly phụ thuộc cây trồng | Đúng | Bảng `material_crop_rule (vật tư, cây trồng, phi_days, nguồn, cờ giả định)` |
| Luật chưa có nguồn | Đúng | `rule_source`, `is_assumption` cho `activity_type`, `evidence_requirement`, `material_crop_rule` |
| Thiếu hai vai người làm / người ghi | Đúng | `activity_revision.performed_by`; `lot_event.recorded_by`; `evidence.recorded_by` |
| Số đo cảm biến bị quy nhầm khi thiết bị chuyển chỗ | Đúng | `observation` lưu vị trí tại thời điểm đo; thiết bị được phép chưa lắp |
| Đơn vị là chuỗi tự do | Đúng | CHECK danh mục `kg, g, l, ml, unit, m3` |
| Chưa có index | Đúng | Index cho truy xuôi, chu kỳ, các đích liên kết và xác minh |
| `activity_type` chưa UNIQUE | Đúng | `UNIQUE (stage_id, code)` |
| Quy ước thời gian | Đúng | UTC, ISO-8601; một bên độ chính xác "ngày" thì so ở mức ngày (các view lịch và cách ly đã làm vậy) |
| Class diagram lệch SQL | Đúng | Sinh tự động từ SQL bằng `gen_diagram.py` |
| PURCHASE / TRANSPORT mơ hồ | Đúng một phần | **Giữ** vì thầy yêu cầu ghi ngày thu mua, vận chuyển — nhưng định nghĩa rõ là **mốc thời gian trên một lô**, không chuyển sở hữu; trigger chặn mốc có đầu vào. Bên bán/mua, nơi đi/đến: ĐATN |
| Ý kiến "đề xuất trạng thái mâu thuẫn" | Không theo | Thay bằng chuỗi thay thế (QĐ6) |

### 0.3 Để ĐATN (ghi nhận, chưa làm)
GTIN / GS1 Digital Link; chứng nhận cho nhiều đối tượng (nhóm hộ, hợp tác xã); bên bán/mua và nơi đi/đến; bảng quy đổi đơn vị và luật cân bằng khối lượng; hoạt động lặp không biết trước số lần; lịch sử lắp đặt thiết bị, cảm biến đa đại lượng, bằng chứng theo khoảng thời gian; truy vấn tham số hóa cho một lô (view hiện tính cho mọi lô — đủ cho quy mô ĐACN).

---

## 1. Phạm vi: bắt buộc cho ĐACN và chỉ thiết kế

| Phần | ĐACN | Ghi chú |
|---|---|---|
| Crop profile mè (+ lạc mock), canh tác, bản ghi, minh chứng, xác minh | **Bắt buộc, chạy với dữ liệu mock** | Lõi của O1 |
| Đồ thị lô, sự kiện lô, truy ngược/xuôi, trạng thái lô | **Bắt buộc** | Lõi của O2 và trang QR |
| Độ đầy đủ chu kỳ, kiểm nhất quán | **Bắt buộc** | Tiêu chí completeness của đề bài |
| Vật tư và thời gian cách ly | Bắt buộc ở mức tối thiểu | Luật để `is_assumption = 1` cho tới khi đối chiếu nhãn thuốc thật |
| Cảm biến | Thiết kế + vài dòng mock | Đề bài liệt kê `sensor`; IoT thật: ĐATN |
| Chứng nhận | Thiết kế + 1 dòng mock | Không có trong danh sách entity của đề bài |

## 2. Đối chiếu tên với đề bài

| Đề bài #6 | Schema |
|---|---|
| farm | `farm` |
| season | `season` (vụ của tổ chức) + `cultivation_cycle` (chu kỳ của một lô đất trong vụ; cây lâu năm không cần vụ) |
| plot | `plot` |
| activity | `activity` + `activity_revision` |
| sensor | `device` + `observation` |
| harvest | `activity` có `activity_type.produces_lot = 1` → sinh `lot` loại `harvest` |
| batch | `lot` (+ `lot_revision`) |
| provenance model | `agent`, `*_revision`, `evidence` + `evidence_link`, `verification` (mục 6) |
| traceability API | các view `v_lot_sources`, `v_lot_destinations`, `v_lot_status`, `v_cycle_completeness` |
| digital timeline | `v_lot_timeline` |
| QR lookup | `lot.public_code` |
| completeness / traceability correctness | `v_cycle_completeness` (minh chứng + đúng hạn), `v_lot_status` (canh tác + chuỗi sau thu hoạch), `v_integrity_issues` |
| mapping dữ liệu hiện có | `source_channel` + `external_ref` trên các bản ghi nhập vào |

## 3. Yêu cầu đầu vào

| Mã | Yêu cầu | Nguồn |
|---|---|---|
| R1 | Đổi cây không sửa schema | Họp với thầy; O1 |
| R2 | Minh chứng và xác minh tách bạch, cho cả hoạt động và lô | Khảo sát 47/50 và 47/50; slide F&S; đánh giá vòng 2 |
| R3 | Sửa dữ liệu giữ bản cũ và lý do | Khảo sát 31/50; slide F&S |
| R4 | Truy ngược và truy xuôi qua gộp lô, có tỷ trọng; nguồn không rõ phải hiện ra | Khảo sát 34/49, 31/45; Bộ NN&MT; đề bài |
| R5 | Phát hiện hoạt động bắt buộc chưa ghi | Đề bài (completeness); KPI F&S "tỷ lệ nhật ký đúng hạn" |
| R6 | Thiếu thì hiện là thiếu; không đủ dữ liệu thì hiện "không xác định" | Đề bài |
| R7 | Thu mua, vận chuyển chỉ ghi thời điểm | Họp với thầy |
| R8 | Xuất được dữ liệu tối thiểu quốc gia | QĐ 25/QĐ-BNNMT |
| R9 | Công khai vị trí đến cấp xã | Khảo sát 32/47 |
| R10 | Cây lâu năm không làm vỡ mô hình | Phòng thủ trước hội đồng |
| R11 | Thuốc BVTV có cấu trúc; thời gian cách ly theo cây trồng | Khảo sát 36/50, 20/50; nhãn thuốc |
| R12 | Chứng nhận có thời hạn, có bên cấp | Khảo sát 38/50, 30/47 |
| R13 | Có entity cảm biến | Đề bài |
| R14 | Ai làm, ai ghi, ở đâu, xảy ra lúc nào, ghi lúc nào | W3C PROV, GS1 EPCIS; phát hiện ghi lùi ngày |
| R15 | Dữ liệu chỉ ghi thêm, được DB đảm bảo | Đề bài: immutable; đánh giá vòng 2 |

## 4. Lý do thiết kế

### QĐ1. Quy trình của cây là dữ liệu → R1, R10
Phần riêng của từng cây nằm trong dòng dữ liệu `crop_profile → stage → activity_type → evidence_requirement`; thuộc tính riêng của giống trong `variety.attributes`. Thêm cây lạc = 3 INSERT (F15). **Loại:** bảng riêng từng cây; EAV thuần; cột riêng của mè. **Đánh đổi:** kiểm JSON ở tầng ứng dụng; `crop_profile.version` giữ quy trình cũ cho vụ cũ.

### QĐ2. Chu kỳ canh tác với mốc cấu hình được → R6, R10
Mốc tính lịch nằm trong bảng **`cycle_anchor` chỉ ghi thêm** (v0.4) + `crop_profile.anchor_event`; `offset_days ± tolerance_days` cho cửa sổ dự kiến. **Chưa có mốc → `undetermined`**, không phải "thiếu" (F4). Sửa mốc = bản mới có lý do; lịch dự kiến tự tính lại và vẫn xem được mốc cũ (V10). Hoạt động lặp có số lần biết trước (bón thúc 1, 2) là các loại hoạt động riêng.

### QĐ3. Vật tư có cấu trúc, cách ly theo cây trồng → R11
`input_material` + `activity_input` (gắn bản ghi) + `material_crop_rule (vật tư, cây trồng, phi_days, nguồn, cờ giả định)`. **Loại:** `phi_days` trên vật tư (v0.2) — nhãn thuốc ghi theo từng cây. Thuốc chưa có luật cho cây đó → `v_integrity_issues` báo `missing_phi_rule` (F11), không đoán.

### QĐ4. Tách sự việc khỏi bản ghi → R3, R15
`activity` / `lot` bất biến; `activity_revision` / `lot_revision` chỉ ghi thêm, bản ≥ 2 bắt buộc có lý do. **Trigger chặn UPDATE/DELETE** trên 11 bảng (C1, C2).

### QĐ5. Minh chứng gắn với bản ghi cụ thể → R2
`evidence` (file/số đo bất biến) + `evidence_link` (đúng một đích; UNIQUE theo từng đích). Bản ghi mới phải được liên kết lại; việc liên kết lại được ghi nhận (`linked_by`, `linked_at`). Giao diện nên có thao tác "giữ lại các minh chứng này" tạo nhiều liên kết một lần. Minh chứng được phép tải lên trước, gắn sau.

### QĐ6. Xác minh: mỗi đối tượng một kết luận hiệu lực, thay thế có lý do → R2 *(mới ở v0.3)*
- **Đối tượng xác minh là bản ghi** (hoạt động / lô / sự kiện lô), không phải từng file. Người xác minh kết luận "bản ghi này có đúng sự thật không"; minh chứng là căn cứ.
- **Tại mỗi thời điểm một kết luận hiệu lực.** Lần sau bắt buộc trỏ `supersedes_verification_id` tới kết luận hiệu lực của cùng đối tượng, kèm lý do; trigger chặn mọi lần xác minh không thay thế (R5a) hoặc thay thế đối tượng khác (C5). Lịch sử giữ đủ: "từ chối 7/12 vì ảnh mờ → đạt 8/12 sau khi chụp lại" (R5b).
- **Không tự xác minh:** người xác minh khác người làm và người ghi (C4).
- **Vì sao không dùng trạng thái "mâu thuẫn"** (đề xuất của bên đánh giá): nếu cho nhiều kết luận song song thì mọi lần kiểm tra lại hợp lệ đều thành mâu thuẫn. F&S làm theo mô hình một kỹ thuật viên phụ trách một vùng; nhiều bên cùng ký (vd chứng nhận hữu cơ) là phần mở rộng ĐATN.

### QĐ7. Trạng thái có hai chiều độc lập → R2, R6 *(sửa ở v0.3)*
- `evidence_completeness`: `complete` / `missing_evidence` (thiếu minh chứng so với yêu cầu) / `missing_inputs` (hoạt động cần vật tư mà chưa khai — thiếu **dữ liệu**, không phải thiếu minh chứng).
- `verification_state`: `unverified` / `verified` / `rejected`.
- **Loại:** một enum duy nhất (v0.2) — "đã xác minh" che mất "thiếu minh chứng" (R4).

### QĐ8. Độ đầy đủ theo chu kỳ phát hiện cả hoạt động vắng mặt → R5, R6 *(mới ở v0.3)*
`v_cycle_expected`: mỗi chu kỳ × mỗi hoạt động **bắt buộc** → `undetermined` / `not_due` / `not_recorded` / `off_schedule` / `on_schedule`, kèm hai chiều trạng thái. `v_cycle_completeness`: số đến hạn, số thiếu, số đủ minh chứng, số đã xác minh, `completeness_ratio`, `cycle_state` (complete / incomplete / undetermined). Đây là loại "thiếu" quan trọng nhất: hộ C không ghi bón thúc bị phát hiện (F3).

### QĐ9. Một bảng lô + đồ thị lô do sự kiện tạo ra → R4, R7, R14
- `lot_event` (gộp / chế biến / đóng gói tạo ra lô; thu mua / vận chuyển là **mốc** trên một lô) có `performed_by`, `recorded_by`, `facility_id`, `occurred_at` có độ chính xác.
- `lot_input(event_id, input_lot_id, quantity_used, unit)`: mỗi cạnh thuộc một sự kiện.
- **Ràng buộc cấu trúc:** mỗi lô tạo bởi tối đa một sự kiện; mỗi hoạt động thu hoạch sinh tối đa một lô; mốc không có đầu vào; không có vòng — tất cả do DB đảm bảo (D1–D3, C3, R2).
- **Tỷ trọng:** lưu số lượng thực dùng, suy ra tỷ trọng khi truy vấn. Thiếu số lượng hoặc khác đơn vị → NULL ("không rõ"), không chia đều.

### QĐ10. Trạng thái lô tổng hợp từ nguồn theo tỷ trọng → R2, R4 *(mới ở v0.3)*
`v_lot_status` (cái người quét QR thấy): `traced_share`, `untraceable_share`, `complete_share` (từ chu kỳ đủ minh chứng), `verified_share`, `trace_state` (fully_traced / partially_untraceable / unknown_share / cycle_detected). Ví dụ QR-80: truy được 100%, 40% khối lượng đến từ chu kỳ đủ minh chứng (F7). Lô có 40% không rõ nguồn → `partially_untraceable` (R1b).

### QĐ11. Kiểm nhất quán liên bảng là một view → R6, R15 *(mới ở v0.3)*
`v_integrity_issues` liệt kê các lỗi không viết được bằng CHECK. Đồng thời là bộ phát hiện lỗi cho các ca thử nghiệm đứt chuỗi.

### QĐ12. Agent, địa điểm, hai vai → R14
`agent` (người / tổ chức / phần mềm / thiết bị theo PROV-O), `facility` (EPCIS bizLocation). Bản ghi hoạt động và sự kiện lô có cả **người làm** và **người ghi**; mọi bản ghi có **thời điểm xảy ra** và **thời điểm ghi** → so được để phát hiện ghi lùi ngày.

### QĐ13. Cảm biến → R13
`device` là một agent loại thiết bị; vị trí hiện tại có thể trống (chưa lắp). `observation` **ghi vị trí tại thời điểm đo** (F13). Minh chứng loại `sensor` trỏ một số đo.

### QĐ14. Công khai / riêng tư → R9
Công khai `province`, `commune` (từ 7/2025 không còn cấp huyện); riêng tư `address_detail`, `geo_point`; `activity_type.public_level`.

### QĐ15. Mã QR tách khỏi khóa nội bộ
`lot.public_code` ≠ `lot_id`. GTIN để ĐATN.

### QĐ16. Chứng nhận → R12
`issued_by` là agent; một phạm vi; bản scan là `evidence`. `isValidOn(date)` so ngày (F14).

### QĐ17. Trạng thái lô có hai phía: canh tác và chuỗi sau thu hoạch → R2, R4 *(mới ở v0.4)*
`v_lot_status` giữ phía canh tác (tỷ trọng từ chu kỳ đủ minh chứng / đã xác minh) và thêm phía chuỗi: duyệt mọi sự kiện lô trên đường truy ngược (gộp, ép, đóng gói, cùng các mốc thu mua/vận chuyển của lô tổ tiên) và các bản ghi lô bị từ chối. Hai phía **không gộp thành một điểm** — trang QR hiện cả hai, đúng nguyên tắc "thiếu thì nói thiếu ở đâu".

### QĐ18. Vụ là thực thể của tổ chức, chu kỳ là của lô đất → R10 *(mới ở v0.4)*
`season` thuộc một tổ chức (vd chương trình Đông Xuân của F&S), có cây trồng và khoảng thời gian; `cultivation_cycle` là một lô đất trong vụ đó. Tách hai khái niệm để: hỏi được "toàn bộ vụ Đông Xuân" bằng khóa ngoại; cây lâu năm vẫn có chu kỳ mà không cần vụ.

### QĐ19. Digital timeline là một view dùng chung → đề bài *(mới ở v0.4)*
`v_lot_timeline(root_lot_id, at, time_precision, kind, ref_id, detail, actor_id, evidence_state, verification_state, source_channel, kind_rank)`. Sắp xếp: `ORDER BY at, kind_rank` (v0.5.1). Mốc `lot_created` lấy thời điểm của sự kiện / hoạt động thu hoạch tạo ra lô, không lấy giờ nạp dữ liệu. Một nguồn duy nhất cho mọi màn hình — nếu mỗi API tự ghép, các màn hình sẽ lệch nhau. Số đo cảm biến chỉ lấy tại lô đất nguồn và trong khoảng thời gian của chu kỳ.

### QĐ20. Kênh nguồn và mã ngoài → mapping dữ liệu hiện có *(mới ở v0.4)*
Mỗi bản ghi nhập vào biết đến từ đâu (`source_channel`) và mã của nó ở hệ thống cũ (`external_ref`). UNIQUE (kênh, mã ngoài) để import chạy lại nhiều lần mà không nạp trùng.

### QĐ21. Hai chiều cho chu kỳ: đủ minh chứng và đúng hạn *(mới ở v0.4)*
`cycle_state` chỉ nói về minh chứng; `on_schedule_ratio` nói về đúng lịch. Không gộp — cùng lý do với QĐ7.

## 5. Ánh xạ PROV-O và EPCIS

| Schema | W3C PROV-O | GS1 EPCIS | Dữ liệu tối thiểu quốc gia |
|---|---|---|---|
| `agent` | `prov:Agent` (Person / Organization / SoftwareAgent) | party | Nông hộ |
| `facility` | `prov:Location` | bizLocation | Cơ sở sơ chế/chế biến |
| `farm`, `plot` | `prov:Entity`, `prov:Location` | readPoint | Vùng sản xuất; `growing_area_code` |
| `season` | `prov:Plan` (kế hoạch canh tác của tổ chức) | — | Thời gian sản xuất |
| `cycle_anchor` | `prov:Entity`; `prov:wasRevisionOf` bản trước | — | Thời gian sản xuất |
| `activity` | `prov:Activity` | ObjectEvent (tùy chọn) | Các khâu |
| `activity_revision` | `prov:Entity` (bản ghi); `prov:wasRevisionOf` bản trước; `prov:wasAttributedTo` người ghi; `prov:wasAssociatedWith` người làm | — | — |
| `activity_input` | `prov:used` | ilmd | — |
| `evidence` | `prov:Entity` | certificationInfo, sensorElement | — |
| `evidence_link` | `prov:wasDerivedFrom` (bản ghi được hỗ trợ bởi minh chứng) | — | — |
| `verification` | `prov:Activity` + `prov:wasAssociatedWith` người xác minh; thay thế ↔ `prov:wasInvalidatedBy` kết luận cũ | — | — |
| `device`, `observation` | `prov:Agent` (thiết bị), `prov:Entity` | sensorElement | — |
| `lot`, `lot_revision` | `prov:Entity`; `prov:wasRevisionOf` | EPC class + lot | Lô hàng |
| `lot_event` + `lot_input` | `prov:Activity`; lô ra `prov:wasDerivedFrom` lô vào; `prov:wasGeneratedBy` sự kiện | Aggregation / Transformation / Transaction / ObjectEvent | Các khâu |
| hoạt động thu hoạch → lô | `prov:wasGeneratedBy` | ObjectEvent (commissioning) | Thời gian thu hoạch |
| `lot.public_code` | — | — | Tem / QR |

## 6. Mục tiêu O1/O2 trả lời bằng truy vấn nào

| Tiêu chí | View | Kiểm tra |
|---|---|---|
Theo sổ quyết định SD-02 (4 tiêu chí O1) và SD-03 (O2). "Biểu diễn đủ 11 bước quy trình mè" **không còn là tiêu chí O1** — đó là tiêu chí đạt của bộ mock (plan Việc 1, sau 29/11). "Xuất dữ liệu tối thiểu quốc gia" là OUT (ĐATN); bảng ánh xạ ở mục 5 chỉ là ý thiết kế.

| Tiêu chí | View | Kiểm tra |
|---|---|---|
| O1-1 · Hai trục trạng thái độc lập mỗi hoạt động (độ đầy đủ × xác minh), tự tính | `v_activity_status` | F1, F2, R4, N17 |
| O1-2 · Hoạt động bắt buộc chưa ghi hoặc lệch lịch bị phát hiện | `v_cycle_expected`, `v_cycle_completeness` | F3–F5, V9, V10, N9 · K3 |
| O1-3 · Sửa hoạt động giữ bản cũ, bắt buộc lý do, minh chứng không tự chuyển | `activity_revision`, `v_activity_status` | C1, C6, F2 · K5 |
| O1-4 · Thêm cây chỉ bằng dữ liệu cấu hình, chạy đủ một chu kỳ | mọi view, không DDL | **K6** (`run_scenarios.py`, hộ D lạc) |
| O1 · Bị từ chối tính là chưa đạt | `v_activity_status`, `v_lot_event_status` | V4, R5 · K4 |
| O2 · Chai truy đúng hộ nguồn + tỷ trọng | `v_lot_sources` | F6, R1 · K1, K2 |
| O2 · Phần không truy được phải hiện ra | `v_lot_status` | R1, N1, N2 |
| O2 · Truy xuôi (thu hồi) | `v_lot_destinations` | F8 |
| O2 · Trạng thái lô trên trang QR | `v_lot_status` | F7, R1b |
| Bổ sung · Vi phạm cách ly | `v_phi_violations` | F10 |
| Bổ sung · Nhất quán | `v_integrity_issues` | F11 |

## 6A. Định nghĩa và quy tắc đã chốt (28/11)

### 6A.1 Độ đầy đủ minh chứng — 4 cấp (SD-07)

Thước đo của O1. Hệ thống **tự tính**; không có cột nào cho người dùng tự điền.

| Cấp | View | Quy tắc | Giá trị |
|---|---|---|---|
| 1 · Hoạt động | `v_activity_status` | ĐỦ khi với **mọi** `evidence_requirement` của loại hoạt động: số file khác nhau (cùng `sha256` chỉ tính 1), đúng loại, gắn vào **bản ghi hiện hành** ≥ `min_count`; nếu `uses_inputs = 1` thì phải ghi vật tư | `complete` · `missing_evidence` · `missing_inputs` |
| 2 · Sự kiện lô | `v_lot_event_status` | Cùng luật cho gộp / ép / đóng gói. Loại sự kiện không có yêu cầu → `not_required` | `complete` · `missing_evidence` · `not_required` |
| 3 · Chu kỳ canh tác | `v_cycle_completeness` | `completeness_ratio` = (hoạt động **bắt buộc đã đến hạn**, đủ minh chứng, không bị từ chối) / (hoạt động bắt buộc đã đến hạn). `cycle_state = complete` khi không thiếu hoạt động nào, tất cả đủ minh chứng, không có gì bị từ chối, và hoạt động không bắt buộc đã ghi cũng đủ. Chưa có ngày gieo → `undetermined` (không tính là thiếu) | `complete` · `incomplete` · `undetermined` |
| 4 · Lô thành phẩm | `v_lot_status` | `complete_share` = % khối lượng lô đến từ các chu kỳ `complete` | 0–1 |

Xác minh là **trục riêng** (`verification_state`, `all_verified`, `verified_share`); đúng/lệch lịch cũng tách riêng (`on_schedule_ratio`).

**Giới hạn (ghi trong báo cáo):** chỉ đo *đủ số lượng đúng loại*, không đo minh chứng có đúng sự thật (`captured_at` chưa được so với ngày làm hoạt động); mọi ngưỡng `evidence_requirement` hiện là giả định nhóm (`is_assumption = 1`); hoạt động có điều kiện mà nông dân không ghi thì không phát hiện được; "đủ minh chứng" ≠ "đáng tin" — chỉ số độ tin cậy để ĐATN.

### 6A.2 Nhãn hiển thị từ hai trục (SD-13)

Lõi lưu 2 trục độc lập, **không lưu nhãn**. Một view duy nhất trong lõi — `v_activity_display_state` — ánh xạ ra nhãn để trang QR, web nhà đầu tư và mọi bên gọi vào hiện giống nhau. Xét từ trên xuống, gặp dòng đúng thì dừng:

| # | Điều kiện | Nhãn |
|---|---|---|
| 1 | Kết luận xác minh hiệu lực = `rejected` | **Bị từ chối** |
| 2 | `missing_evidence` hoặc `missing_inputs` | **Thiếu minh chứng** |
| 3 | `complete` và `verified` | **Đã xác minh** |
| 4 | `complete` và `unverified` | **Tự khai, chưa xác minh** |

Trường hợp đặc biệt (R4): đã xác minh nhưng 0 minh chứng → rơi vào dòng 2, hiện "Thiếu minh chứng", vì trang QR phải thể hiện trung thực độ đầy đủ. Lý do không lưu 4 trạng thái: có tổ hợp thang 4 trạng thái không biểu diễn được (R4). *Trạng thái: quy tắc chốt; view cài sau 29/11, trước trang QR.*

### 6A.3 Hiển thị "bị từ chối" trên trang QR (SD-12)

- Hiện nhãn **"Bị từ chối"** kèm tên hoạt động và ngày.
- Hiện **vai trò** người xác minh (`agent.role`, vd "kỹ thuật viên"), không hiện tên.
- **Không** hiện `verification.note` — ghi chú nội bộ.
- `activity_type.public_level = 'private'` → chỉ hiện *số lượng* hoạt động bị từ chối, không hiện chi tiết.

### 6A.4 Rút lại liên kết minh chứng gắn nhầm (SD-10)

`evidence_link` chỉ ghi thêm và `verification` xác minh cả bản ghi, nên hiện không sửa được một ảnh gắn nhầm. Thiết kế:

- Bảng mới **`evidence_link_retraction`** (chỉ ghi thêm): `retraction_id`, `link_id` → `evidence_link.link_id` (UNIQUE — mỗi liên kết rút tối đa một lần), `retracted_by` → `agent`, `retracted_at`, `reason` (NOT NULL), `replacement_link_id` (tùy chọn) → `evidence_link.link_id`.
- `v_activity_status` và `v_lot_event_status` chỉ đếm liên kết **chưa bị rút** → độ đầy đủ tự tính lại.
- `v_integrity_issues` thêm cảnh báo `verified_then_evidence_retracted`: bản ghi đã xác minh nhưng sau đó minh chứng bị rút.
- Trigger/view sửa trong `gen_triggers.py` / `gen_views.py`, không sửa tay file SQL. *Trạng thái: thiết kế chốt; cài đặt sau 29/11.*

### 6A.5 Dạng của lõi: dịch vụ trung tâm (SD-06)

Định hướng: **dịch vụ trung tâm**, các hệ thống khác (trang QR, Story, dashboard) gọi vào qua API. Lý do: truy xuất đi xuyên nhiều tổ chức (hộ → thu mua → nhà máy → thương hiệu); nếu mỗi nơi giữ database riêng (thư viện nhúng), chuỗi lô đứt ở ranh giới tổ chức. Luật nghiệp vụ đang nằm trong trigger của database → hợp với một nơi lưu trung tâm sở hữu luật. Đánh đổi: phải vận hành dịch vụ, có xác thực, phụ thuộc mạng. ĐACN chỉ ghi định hướng và danh sách API (6B); hiện thực dịch vụ hoàn chỉnh để ĐATN (SD-05).

## 6B. Danh sách API truy xuất (D2)

Mô tả đề tài #6 yêu cầu ĐACN *thiết kế* schema/API. Mỗi endpoint đọc từ đúng **một view của lõi** (QĐ19: không để mỗi API tự ghép). Chỉ đọc; tham số là `public_code` in trên QR, **không bao giờ** lộ `lot_id` (QĐ15).

| # | Endpoint | Ai dùng | Đọc từ | Trả về |
|---|---|---|---|---|
| A1 | `GET /v1/lots/{public_code}` | Trang QR (công khai) | `v_lot_current`, `v_lot_status` | Tên sản phẩm, quy cách; `traced_share`, `untraceable_share`, `complete_share`, `verified_share`, `undetermined_share`; `trace_state`, `chain_evidence_state` |
| A2 | `GET /v1/lots/{public_code}/sources` | Trang QR (công khai) | `v_lot_sources` + `farm` (chỉ `province`, `commune`) + `v_cycle_completeness` | Từng hộ nguồn: tỷ lệ góp, `source_status`, `cycle_state`, `completeness_ratio` |
| A3 | `GET /v1/lots/{public_code}/timeline` | Trang QR (công khai) | `v_lot_timeline` + `v_activity_display_state`, lọc theo `public_level` | Sự kiện theo thời gian kèm nhãn hiển thị (6A.2); quy tắc "bị từ chối" theo 6A.3 |
| A4 | `GET /v1/lots/{public_code}/destinations` | F&S (nội bộ, thu hồi) | `v_lot_destinations` | Mọi lô con / chai đã dùng lô này |
| A5 | `GET /v1/cycles/{cycle_id}/completeness` | F&S, nhà đầu tư (nội bộ) | `v_cycle_completeness`, `v_cycle_expected`, `v_phi_violations` | Tỷ lệ đủ minh chứng, đúng lịch; danh sách hoạt động thiếu / lệch lịch; vi phạm cách ly |
| A6 | `GET /v1/activities/{activity_id}` | F&S, kỹ thuật viên (nội bộ) | `v_activity_status`, `activity_revision`, `evidence_link`, `v_verification_effective` | Hai trục trạng thái, lịch sử bản sửa kèm lý do, minh chứng gắn với từng bản |
| A7 | `GET /v1/integrity-issues` | F&S (nội bộ) | `v_integrity_issues` | Danh sách bất nhất quán liên bảng |

**Mã lỗi** (dùng chung):

| Mã | Khi nào | Trang QR hiện |
|---|---|---|
| `400 INVALID_CODE` | `public_code` sai định dạng | "Mã không hợp lệ" |
| `404 LOT_NOT_FOUND` | Không có lô mang mã này | "Không tìm thấy sản phẩm — có thể là mã giả" |
| `503 UNAVAILABLE` | CSDL / dịch vụ không phản hồi | "Hệ thống đang bận, thử lại sau" |

Lô **có** nhưng không truy được **không phải lỗi**: trả `200` với `trace_state = untraceable` hoặc `partially_untraceable`, và trang hiện rõ phần không truy được (O2).

Endpoint công khai (A1–A3) không cần đăng nhập. Endpoint nội bộ (A4–A7) cần xác thực — mô hình tài khoản và phân quyền là OUT (SD-09). Ghi dữ liệu (tạo hoạt động, gắn minh chứng, xác minh) đi thẳng vào bảng với trigger hiện có; API ghi để ĐATN.

## 6C. Sơ đồ tuần tự: quét QR → API → truy ngược → trang hiển thị

File nguồn: `docs/diagrams/qr_sequence.mmd`. Truy vấn A1–A3 phải là truy vấn **tham số hóa cho một lô**, không quét view cho mọi lô (mục 8, dòng 7e).

```mermaid
sequenceDiagram
    autonumber
    actor NTD as Người tiêu dùng
    participant QR as Trang QR (web)
    participant API as Traceability API
    participant DB as Lõi CSDL (view)

    NTD->>QR: Quét mã trên chai → mở URL /q/{public_code}
    alt Mất mạng / không tải được trang
        QR-->>NTD: "Không kết nối được, thử lại" (không hiện dữ liệu cũ như dữ liệu mới)
    else Có mạng
        QR->>API: GET /v1/lots/{public_code}
        API->>API: Kiểm định dạng mã
        alt Sai định dạng
            API-->>QR: 400 INVALID_CODE
            QR-->>NTD: "Mã không hợp lệ"
        else Đúng định dạng
            API->>DB: v_lot_current + v_lot_status theo public_code (truy vấn một lô)
            alt Không có lô
                DB-->>API: 0 dòng
                API-->>QR: 404 LOT_NOT_FOUND
                QR-->>NTD: "Không tìm thấy sản phẩm — có thể là mã giả"
            else Có lô
                DB-->>API: sản phẩm, traced/untraceable/complete/verified_share, trace_state, chain_evidence_state
                API-->>QR: 200 tóm tắt lô
                QR-->>NTD: Màn tóm tắt: % truy được, % đủ minh chứng, % đã xác minh; phần không truy được hiện rõ
                opt Bấm "xem nguồn"
                    QR->>API: GET /v1/lots/{public_code}/sources
                    API->>DB: v_lot_sources + farm (tỉnh, xã) + v_cycle_completeness
                    DB-->>API: hộ nguồn, tỷ lệ, trạng thái chu kỳ
                    API-->>QR: 200 danh sách nguồn
                    QR-->>NTD: Từng hộ: tỷ lệ góp, trạng thái chu kỳ
                end
                opt Bấm "xem nhật ký"
                    QR->>API: GET /v1/lots/{public_code}/timeline
                    API->>DB: v_lot_timeline + v_activity_display_state, lọc theo public_level
                    DB-->>API: sự kiện theo thời gian + nhãn hiển thị
                    API-->>QR: 200 timeline (ẩn ghi chú xác minh, ẩn tên người)
                    QR-->>NTD: Hoạt động: Đã xác minh / Tự khai / Thiếu minh chứng / Bị từ chối
                end
            end
        end
    end
```

## 6D. Trang QR — điều kiện nghiệm thu (SD-14)

Trang QR là **bắt buộc** cho ĐACN. Thứ tự làm, vì trang đọc từ các thành phần này: (1) `v_activity_display_state` (6A.2) → (2) `evidence_link_retraction` (6A.4) → (3) truy vấn tham số hóa một lô → (4) trang theo A1–A3 và 6C.

**Đạt khi:** quét mã QR thật trên dữ liệu mock → màn tóm tắt (đọc trong ~30 giây, vị trí đến cấp tỉnh/xã) → bấm xem từng hộ, từng hoạt động và nhãn trạng thái; ba nhánh lỗi ở 6C hiện đúng thông báo.

## 7. Kết quả kiểm tra (103/103 hồi quy + K1–K6 6/6, trên SQLite và PostgreSQL)

| Bộ | Lệnh | SQLite | PostgreSQL 18 | Log |
|---|---|---|---|---|
| Kịch bản K1–K6 (minh chứng E3, E4) | `python run_scenarios.py lac [--pg]` | 6/6 | 6/6 | `db/logs/k1_k6_sqlite.txt`, `k1_k6_postgres.txt`, `k1_k6_sqlite_raw.txt` (kèm SQL + dữ liệu thô) |
| Hồi quy schema | `python smoke_test.py sqlite\|postgres` | 103/103 | 103/103 | `db/logs/smoke_sqlite.txt`, `smoke_postgres.txt` |
| Ca phản biện độc lập (phát hiện / đứng vững) | `python ../review/review_tests.py [pg]` | 6 / 48 | 6 / 57 | `db/logs/review_sqlite.txt`, `review_postgres.txt` — 0 chưa xử lý; 6 phát hiện còn lại (G2, G4, RV5, RV8, RV14, RV15) là giới hạn đã ghi ở mục 8 |

**K6 duy nhất** là hộ D trong `run_scenarios.py` / `seed_lac.sql` (gieo → bón lót → phun → thu hoạch → rang → vận chuyển → đóng gói → truy ngược QR-LAC-200). `F15` (hộ E) trong `smoke_test.py` chỉ là hồi quy cấu hình lạc, không dùng làm bằng chứng K6.

v0.5 thêm nhóm **N1–N30** (hồi quy cho các phát hiện của đánh giá độc lập, mục 0). v0.4 thêm nhóm **V1–V11** (chuỗi sau thu hoạch, timeline, vụ, kênh nguồn, đúng hạn, lịch sử mốc gieo) và **C14–C20**. Phần dưới mô tả 39 kiểm tra từ v0.3, vẫn giữ nguyên.


Dữ liệu: 3 hộ ở Tây Ninh (400/350/250 kg) + một chu kỳ chưa có ngày gieo; gộp tại điểm thu mua (có phiếu cân, QA xác minh); vận chuyển (mốc); ép dầu; 2 lô chai; 1 cảm biến chuyển chỗ; 1 chứng nhận hết hạn; thuốc X (có luật cách ly 7 ngày cho mè, phun 5 ngày trước thu hoạch); thuốc Y (chưa có luật cho mè).

- **F1–F15 chức năng:** trạng thái 2 chiều; hộ C không ghi bón thúc bị phát hiện; chu kỳ chưa có ngày gieo → không xác định; QR-80 = 40/35/25%, truy được 100%, 40% từ chu kỳ đủ minh chứng; truy xuôi H-A → 4 lô; sự kiện gộp có trạng thái riêng; vi phạm cách ly; thiếu luật cách ly; sửa lô có lý do; số đo giữ vị trí cũ; chứng nhận hết hạn; thêm cây lạc.
- **R0–R5, D1–D3 hồi quy:** đủ các ca bên đánh giá tái hiện, đều đạt.
- **C1–C13 ràng buộc và trigger:** chỉ ghi thêm, mốc có đầu vào, tự xác minh, thay thế sai đối tượng, đơn vị, liên kết 2 đích, chứng nhận 2 phạm vi, số đo thiếu vị trí, luật thiếu nguồn, trùng mã loại hoạt động.

*Đây là kiểm tra schema. Minh chứng E3, E4 đến từ kịch bản K1–K6 (`run_scenarios.py`) cộng các kiểm tra hồi quy được trích dẫn ở mục 6 (SD-15, SD-18). Bộ mock mè đủ 11 bước là việc sau 29/11.*

## 8. Giới hạn đã biết

| # | Vấn đề | Hiện tại | Hướng sau |
|---|---|---|---|
| 1 | View tính cho mọi lô | Đủ cho quy mô ĐACN | Truy vấn tham số hóa cho một lô (đo thời gian truy vấn) |
| 2 | Chuỗi hợp lệ dài hơn 20 bước bị báo `depth_limit_reached` | Không xảy ra với mè | Tăng giới hạn hoặc closure table |
| 3 | Kiểm JSON theo JSON Schema | Tầng ứng dụng | — |
| 4 | Quy đổi đơn vị | Khác đơn vị → "không rõ" + báo nhất quán | Bảng quy đổi, cân bằng khối lượng (ĐATN) |
| 5 | Sửa một cạnh lô đã ghi | Chỉ ghi thêm; v0.5 chặn thêm cạnh khi lô ra đã dùng tiếp / sự kiện đã xác minh | Bản sửa cho sự kiện lô (ĐATN) |
| 6 | Hoạt động lặp không biết trước số lần | Loại `conditional`, không tính vào độ đầy đủ | Luật tần suất (ĐATN) |
| 7 | `not_due` so với ngày hiện tại | Chỉ khi chu kỳ còn mở; đã đóng thì chưa ghi = thiếu | — |
| 7b | Đóng chu kỳ nhầm ngày | Không sửa được (chỉ đóng một lần) | Bảng đính chính có lý do như `cycle_anchor` nếu thực tế cần |
| 7c | **[Cao, QR — RV14]** Thêm yêu cầu minh chứng cho **loại sự kiện lô** áp dụng hồi tố cho sự kiện cũ | Yêu cầu theo loại hoạt động đi theo phiên bản crop profile (RV1). Yêu cầu theo loại sự kiện không gắn crop profile nên lọt khóa `f_config_in_use`: thêm yêu cầu ảnh cho `packaging` làm `lot_b80`, `lot_b250` (đã in QR) đổi `chain_evidence_state` từ `complete` sang `incomplete`. Hồi quy V2 hiện đang dùng chính cách thêm hồi tố này | Cùng đợt trang QR: thêm `valid_from` cho `evidence_requirement`; `v_lot_event_status` chỉ áp yêu cầu có `valid_from` ≤ ngày ghi sự kiện; viết lại V2. Vẫn phụ thuộc dòng 19 |
| 7d | Chu kỳ thu hoạch nhiều đợt (G2); hai chu kỳ chồng nhau trên một lô đất (G4) | Timeline lô thu hoạch đợt 1 hiện cả hoạt động sau đợt 1; số đo có thể tính cho cả hai chu kỳ | Cắt timeline theo ngày thu hoạch; ràng buộc không chồng chu kỳ (ĐATN) |
| 7e | Hiệu năng view tính cho mọi lô | Agent đo v0.4: `v_lot_status` 1,5 s ở 200 hộ/2.000 lô, CTE gieo một lô 0,4 ms | Trang QR dùng truy vấn tham số hóa cho một lô |
| 8 | Luật cách ly và yêu cầu minh chứng đang là giả định | `is_assumption = 1` | **Đối chiếu nhãn thuốc thật** |
| 9 | Sai lệch mốc ngày cho phép | `tolerance_days` | **Hỏi thầy** |
| 10 | Mức chi tiết khi hiện "bị từ chối" trên QR | **Đã chốt (SD-12, mục 6A.3):** nhãn + hoạt động + ngày + vai trò người xác minh; không hiện ghi chú, không hiện tên | Cài cùng trang QR |
| 11 | Tách dữ liệu theo tổ chức (SD-08) | Hiện `crop_profile` không có `organization_id`; cấu hình dùng chung. Báo cáo chỉ viết "dùng chung cho nhiều loại cây trong một chuỗi", **không** viết "an toàn cho nhiều doanh nghiệp" | Thêm `organization_id` vào `crop_profile` (stage / activity_type / evidence_requirement kế thừa qua khóa ngoại); bắt buộc rà lại trước khi triển khai đa tổ chức |
| 12 | Rút lại liên kết minh chứng gắn nhầm | **Đã chốt thiết kế (SD-10, mục 6A.4):** bảng `evidence_link_retraction` chỉ ghi thêm | Cài đặt sau 29/11, trước trang QR |
| 13 | Ánh xạ hai trục trạng thái ra nhãn | **Đã chốt quy tắc (SD-13, mục 6A.2):** 4 nhãn, xét từ trên xuống, một view trong lõi | Cài `v_activity_display_state` sau 29/11, trước trang QR |
| 14 | Phân quyền ai được ghi / xác minh (SD-09) | Dữ liệu ghi rõ người làm / người ghi / người xác minh; trigger chặn tự xác minh bản ghi của mình (C4). Chưa có tài khoản, chưa kiểm soát ai gọi thao tác nào | ĐATN |
| 15 | Loại lô / loại sự kiện lô cố định (SD-11) | `lot_type` (4 loại) và `event_type` (5 loại) cố định bằng CHECK; hoạt động canh tác thì mở rộng tự do bằng dữ liệu | Thêm loại mới phải sửa schema → ĐATN nếu cần |
| 16 | Nạp lại dữ liệu trùng (RV8) | SQLite: trigger chặn ghi đè không phân biệt được `INSERT OR IGNORE` / `ON CONFLICT DO NOTHING` với `INSERT` thường → cả hai đều báo lỗi; PostgreSQL thì `ON CONFLICT DO NOTHING` chạy được. ĐACN chỉ dùng mock, không có import | Import viết `INSERT … SELECT … WHERE NOT EXISTS` (chạy giống nhau trên hai hệ) |
| 17 | Đầu vào ghi SAI (không phải thiếu) của sự kiện lô | Chỉ ghi thêm nên không xóa được dòng sai; RV6 chỉ cho bổ sung khi bị từ chối. Làm lại = lô mới + sự kiện mới; lô cũ không có dấu "đã thay thế", và đầu vào bị đếm hai lần ở `over_consumption` | Bảng `lot_supersession` (lô cũ → lô mới, lý do) + loại lô đã thay thế khỏi `over_consumption` + QR mã cũ chỉ sang mã mới (ĐATN) |
| 18 | Thông tin hộ / lô đất sai sau khi đã sinh lô (RV12) | Bị khóa, chưa có cách đính chính | Bảng lịch sử thông tin hộ / lô đất có lý do (ĐATN) |
| 19 | `recorded_at` do client gửi | Quy tắc RV7 so `lot_input.recorded_at` với `lot_event.recorded_at`, cả hai do client gửi lên. Chỉ cần gửi `lot_input.recorded_at` trùng ngày ghi sự kiện là thêm được đầu vào hồi tố vào lô chai đã in QR. Cách sửa dòng 7c cũng dựa vào giá trị này | Dịch vụ trung tâm (SD-06) tự đặt `recorded_at`, không nhận từ client |
| 20 | **[TB — RV15]** Thêm luật cách ly sau khi vụ đã thu hoạch | `material_crop_rule` đã chặn UPDATE/DELETE nhưng vẫn cho INSERT, vì luật gắn theo `crop_code` chứ không theo phiên bản profile. Cặp (thuốc, cây) chưa có luật thì đang báo `missing_phi_rule`; thêm luật sẽ chuyển kết luận PHI của vụ đã xong (ví dụ thuốc Y cho mè: `v_phi_violations` từ 1 lên 2). Thêm luật cho cặp đang thiếu là quy trình đã định (dòng 8), nên vấn đề thật là: (a) không biết luật được thêm khi nào, trang QR không phân biệt được luật có trước hay sau thu hoạch; (b) thêm một luật lỏng (`phi_days = 0`) làm mất cảnh báo "thiếu luật" mà không hiện vi phạm, rồi không sửa lại được | Cùng đợt trang QR: thêm `recorded_at`, `recorded_by` vào `material_crop_rule`; `v_phi_violations` và `missing_phi_rule` thêm cờ "luật bổ sung sau thu hoạch" để trang QR hiển thị. Sửa nhãn thuốc: đưa `valid_from` vào khóa chính |

## 9. Việc tiếp theo
- ✅ Việc 2: kịch bản K1–K6 → E3, E4 (6/6 trên SQLite và PostgreSQL, 28/11).
- Ngay sau 29/11, theo thứ tự (mục 6D): `v_activity_display_state` (SD-13) → `evidence_link_retraction` (SD-10) → truy vấn tham số hóa một lô và đo thời gian → **trang QR** (SD-14, bắt buộc). Cùng đợt: sửa RV14 (mục 8 dòng 7c) vì ảnh hưởng trực tiếp trạng thái chuỗi hiển thị trên QR, và RV15 (dòng 20).
- Việc 1: bộ mock mè đủ 11 bước theo quy trình Bình Thuận (hiện `seed_me.sql` có 3 loại hoạt động).
- Đối chiếu nhãn thuốc thật cho luật cách ly; hỏi thầy dung sai ngày (`tolerance_days`).
- Khi rà thiết kế trước triển khai đa tổ chức: xem lại SD-08.

## 10. Câu hỏi hội đồng dự kiến

**"Nông dân sửa bản ghi thì minh chứng cũ đi đâu?"** (điểm 3.5) — Minh chứng gắn với **một bản ghi cụ thể** (`activity_revision`), không gắn với hoạt động. Sửa bản ghi = thêm bản mới; ảnh cũ vẫn chứng minh cho bản cũ, không tự chuyển sang bản mới. Bản mới hiện `missing_evidence` cho tới khi người ghi **liên kết lại** (một thao tác, không cần tải lại file). Đây là chủ đích: nếu ảnh tự đi theo, sửa liều từ 30 kg thành 25 kg vẫn "có ảnh" dù ảnh chụp bao 30 kg.

**"Hoạt động có điều kiện (phun thuốc) xử lý thế nào?"** (điểm 3.6a) — Không tính vào lịch bắt buộc (không phải lần nào cũng phun), nhưng **đã ghi thì vẫn chấm**: minh chứng, vật tư, thời gian cách ly. Từ v0.5, phun thuốc thiếu ảnh hoặc bị từ chối làm chu kỳ chưa đủ (`n_other_problem`). Điều kiện kích hoạt tự động (vd mưa nhiều → bắt buộc phun phòng nấm): ĐATN.

**"Sao biết bộ kiểm tra không tự chấm điểm cho mình?"** — Vòng 4 do agent không viết schema tự thiết kế ca thử phá; nó tìm ra 30 lỗi mà 57 kiểm tra của nhóm không bắt được. Mỗi lỗi được chuyển thành một kiểm tra hồi quy (N1–N30) trước khi coi là đã sửa, rồi agent chạy lại bộ ca của nó trên bản mới.

**"Nếu dữ liệu đã nạp trước khi có trigger thì sao?"** — `v_integrity_issues` kiểm lại những gì trigger chặn (vòng, loại lô sai, tổng tỷ trọng ≠ 100%, dùng quá khối lượng, sai thứ tự thời gian) nên dữ liệu cũ hoặc nạp từ nguồn ngoài vẫn bị phát hiện.
