# Plan ĐACN — Lõi truy xuất có minh chứng cho chuỗi mè → dầu mè

> Đề tài #6 — Agricultural Digital Thread & Evidence-aware Traceability
> Cập nhật: 28/11/2026 (chiều) · Nhóm: **Duy Quý** (trưởng nhóm) · **Mạnh Dũng** (kỹ thuật) · **Duy Đan** (nội dung & minh chứng)
> Mốc gần nhất: **29/11/2026 gửi thầy Fishbone & Evidence Board** (còn 1 ngày) · Bảo vệ ĐACN: cuối năm (chờ lịch)
> **Mọi quyết định phạm vi và thiết kế: `Project_Scope_Decision.txt` (SD-01 … SD-18).** File này chỉ giữ kế hoạch và phân công; nếu hai nơi nói khác nhau, theo sổ quyết định.
> Repo code: https://github.com/pdiqui-17/DigitalX---Traceability-Core

---

## 0. Những gì đã chốt

| Hạng mục | Quyết định | Nguồn |
|---|---|---|
| Đề tài | Vẫn là đề tài #6; ĐACN giới hạn ở cây mè vì đã có quy trình và dữ liệu | Họp với thầy |
| Phạm vi canh tác | Mè đen 2 vỏ, quy trình Bình Thuận làm khung; farm mock đặt ở Tây Ninh | Tài liệu trong Project, website F&S |
| Sản phẩm | Dầu mè rang chai 80ml / 250ml (F&S). Can 25kg bán sỉ: ngoài phạm vi | foodnseed.vn |
| Thu mua, vận chuyển | Chỉ ghi ngày | Họp với thầy |
| Dữ liệu demo | Mock | Họp với thầy |
| QR | **Trang QR là điều kiện nghiệm thu**, làm càng sớm càng tốt sau 29/11 (SD-14, chốt 28/11). Early proof vẫn là cốt lõi của mô hình | Họp với thầy (nhà đầu tư yêu cầu QR bắt buộc, làm trước); mô tả đề tài #6 ("QR lookup experience") |
| Mở rộng | Lõi dùng chung + crop profile; cây thứ 2 để demo là **lạc (mock)**, và / hoặc lúa (chưa có); không hard-code "một vụ = một lần gieo" | Nhóm chốt 25/11; SD-04 |
| Trạng thái minh chứng | Lõi giữ hai trục riêng: độ đầy đủ minh chứng × trạng thái xác minh; cần cơ chế tính/ánh xạ trong lõi. QR không cần phơi bày mọi tổ hợp (SD-13) | Nhóm chốt nguyên tắc 27/11 |
| Lớp tiêu chí | Early proof chứng minh mô hình là cốt lõi; trang QR bắt buộc, là cách trình bày của C2 (SD-14, SD-17). Visibility, Predictability để ĐATN nhưng schema lưu sẵn dữ liệu | Họp với thầy; SD-14 |
| Khung báo cáo | Hướng dẫn bảo vệ ĐACN v4 + mẫu Fishbone & Evidence Board **phiên bản 3** (slide 2–3, đề tài phần mềm) | Drive của thầy; bản chép ở `docs/_tham_khao/` (không đẩy lên GitHub) |

## 1. Lập luận đề tài (bản nháp)

- **P1 — Vấn đề:** Doanh nghiệp đầu tư vùng trồng mè phân tán nhưng không kiểm chứng được hoạt động canh tác; QR trên chai dầu không chứng minh được nguồn gốc. Hệ thống quốc gia: 821.734 sản phẩm đăng ký nhưng chỉ 161.324 (≈19,6%) có dữ liệu truy xuất.
- **S1 — Khảo sát:** Giải pháp hiện có làm từng mảnh; chưa thấy giải pháp nào kết hợp (1) quy trình theo cây làm khung kỳ vọng, (2) minh chứng và trạng thái xác minh theo từng hoạt động, (3) truy qua gộp lô và chuyển hóa, (4) trang QR thể hiện trung thực độ đầy đủ.
- **Mục đích:** Lõi truy xuất nguồn gốc có minh chứng, cấu hình được theo loại nông sản; chuỗi mè đen → dầu mè là trường hợp chính để kiểm chứng.
- **O1:** Khả năng xác định mức độ minh chứng của từng hoạt động canh tác so với quy trình của loại cây.
  *Tiêu chí đã chốt:* (1) tự tính riêng độ đầy đủ và trạng thái xác minh; (2) phát hiện hoạt động bắt buộc bị thiếu hoặc lệch lịch; (3) sửa hoạt động có phiên bản cũ, lý do, minh chứng không tự chuyển; (4) thêm cây bằng cấu hình và chạy đủ một chu kỳ.
  *Đã bỏ khỏi O1 (SD-02):* “đủ 11 bước mè” → tiêu chí của bộ mock (Việc 1); “xuất dữ liệu tối thiểu quốc gia” → OUT/ĐATN.
- **O2:** Khả năng truy ngược từ lô thành phẩm, qua gộp và chế biến, về nguồn và minh chứng.
  *Tiêu chí đã chốt:* trên bộ mock (3 hộ → 1 lô ép → 2 lô chai), truy đúng hộ nguồn và tỷ lệ; bắt buộc hiện phần không truy được và tính đúng tỷ lệ nguồn từ chu kỳ đủ minh chứng.
- **D1 → O1:** Lõi entity chung + crop profile; sự kiện chỉ ghi thêm, sửa tạo bản mới kèm lý do (tham chiếu W3C PROV).
- **D2 → O2:** Sự kiện lô theo EPCIS (Aggregation, Transformation), đồ thị nguồn gốc lô, **danh sách API (bắt buộc — mô tả đề tài yêu cầu thiết kế API)** và sơ đồ tuần tự quét QR; hiện thực API hoàn chỉnh để ĐATN. Định hướng dịch vụ trung tâm (SD-06). Trang QR bắt buộc (SD-14).
- **C1:** Lõi đánh giá minh chứng canh tác theo cấu hình cây → O1 → **E3** (K3, K4, K5, K6) · **C2:** Truy xuất lô thành phẩm về nguồn và minh chứng → O2 → **E4** (K1, K2, R1, N1, N2, F7). QR là cách trình bày của C2 (SD-17, SD-18).

## 2. Trạng thái hiện tại

| Mã | Nội dung | Trạng thái | Ở đâu |
|---|---|---|---|
| E1 · P1 | Khảo sát người tiêu dùng n=50 + số liệu hệ thống quốc gia | Có bản phân tích, mức **P** | Chat 22/11; file CSV khảo sát |
| E2 · S1 | Khảo sát giải pháp, 8 giải pháp, 7 tiêu chí | Bản 4, mức **P**, **chưa kiểm thử trực tiếp** | Project: `claude/S1_khao_sat_giai_phap.md` |
| D1/D2 | Thiết kế lõi, crop profile, luồng lô | **Schema v0.5, 4 vòng đánh giá.** 28/11: thêm định nghĩa độ đầy đủ, nhãn hiển thị, rút lại liên kết, dịch vụ trung tâm, **danh sách API (6B)**, **sơ đồ tuần tự QR (6C)**. Phân quyền: OUT (SD-09) | `docs/D1_D2_schema_design.md` mục 6A–6D; `docs/diagrams/qr_sequence.mmd` |
| E3 · C1 | Kiểm thử đánh giá minh chứng: K3, K4, K5, K6 | **K3–K6 đạt trên SQLite và PostgreSQL 18** (28/11); mức P | `db/run_scenarios.py`; log `db/logs/k1_k6_sqlite.txt`, `k1_k6_postgres.txt` |
| E4 · C2 | Kiểm thử truy xuất: K1, K2 + R1, N1, N2, F7 | **K1, K2 đạt; R1, N1, N2, F7 đạt** (103/103 hồi quy) trên SQLite và PostgreSQL 18; mức P | K1–K2: log như trên; R1, N1, N2, F7: `db/logs/smoke_sqlite.txt`, `smoke_postgres.txt` |
| Trang QR | Điều kiện nghiệm thu (SD-14) | **Thiết kế xong** (API + sơ đồ tuần tự); trang **chưa có** | `docs/D1_D2_schema_design.md` mục 6B–6D |
| Outline báo cáo | | **Chưa có** | — |
| 2 slide DefenseBoard | | **Chưa có** | — |

## 3. Kế hoạch chi tiết đến 29/11

> Thứ tự đúng: **thiết kế dữ liệu (Việc 0) → dữ liệu mock theo schema (Việc 1) → prototype kiểm tra (Việc 2)**. Đây là lõi của đề tài #6 ("canonical schema, provenance model, traceability API"), nên phải có trước khi sinh dữ liệu.

### Phân công theo người và theo ngày (cập nhật 28/11)

> Bảng này thay cho ngày và người ghi ở tiêu đề các Việc 0–9 bên dưới. Nội dung từng Việc vẫn dùng để tham khảo.

Nguyên tắc: người không trực tiếp thiết kế là người đặt câu hỏi phản biện, không tự viết test kỹ thuật — đúng cách vòng đánh giá 4 tìm ra 30 lỗi mà bộ test tự viết của người thiết kế không bắt được (xem `docs/CHANGELOG.md` v0.5).

**Duy Quý — trưởng nhóm (điều hành, quyết định, liên hệ thầy; không code)**

| Ngày | Việc | Xong khi |
|---|---|---|
| 27/11 ✅ | Bàn với Mạnh Dũng và chốt các quyết định thiết kế SD-01 … SD-18 | Đã ghi vào `Project_Scope_Decision.txt` |
| 28/11 sáng | Gửi sổ quyết định cho Mạnh Dũng và Duy Đan, yêu cầu đọc phần TÓM TẮT. Duyệt mục 4 (câu hỏi gửi thầy) | Cả nhóm đã đọc; mục 4 đúng ý |
| 28/11 chiều | Viết nội dung slide Fishbone theo sổ quyết định (Claude soạn nháp): Mục đích, O1/O2 kèm tiêu chí, IN/OUT, D1/D2, C1/C2, ranh giới ĐACN–ĐATN | Mỗi ô 1–2 dòng, khớp SD |
| 28/11 tối | Chủ trì rà ngược chuỗi E → C → O → Mục đích (Việc 7) cùng cả nhóm; gạch mọi câu nói quá bằng chứng | Mỗi C có E; không còn số liệu chưa chạy |
| 29/11 | Việc 9: đánh dấu đủ checklist 4.2, đặt tên file đúng chuẩn, kiểm tra thầy mở được repo và mọi link, gửi thầy | Đã gửi |

**Mạnh Dũng — kỹ thuật (schema, test, tài liệu thiết kế)**

| Ngày | Việc | Xong khi |
|---|---|---|
| 28/11 ✅ | K1–K6: `run_scenarios.py` là bản chính, chạy được SQLite và PostgreSQL (`--pg`, cấu hình `db/.env`); `smoke_test.py` giữ làm bộ hồi quy (87 kiểm tra, v0.5.1 thêm W1–W16 → 103), cũng chạy được PostgreSQL trên Windows qua `db/dbtools.py` | ✅ 6/6 và 103/103 trên cả hai hệ |
| 28/11 ✅ | Log UTF-8 bằng `--log` (không qua PowerShell), lưu ở `db/logs/` để Evidence Board dẫn thẳng tới | ✅ 5 file log đọc được |
| 28/11 ✅ | Một bản K6 duy nhất: hộ D trong `run_scenarios.py`; `F15` (hộ E) chỉ là hồi quy. Cập nhật `docs/K6_lac_test_flow.md` | ✅ |
| 28/11 ✅ | `docs/D1_D2_schema_design.md`: mục 6A (SD-06, 07, 10, 12, 13), **6B danh sách API**, **6C sơ đồ tuần tự quét QR** (cả nhánh lỗi), 6D điều kiện nghiệm thu trang QR; sửa mục 6 (bỏ "11 bước", F15 → K6), mục 7, mục 8 dòng 10–15 | ✅ Tài liệu khớp code và sổ quyết định |
| 28/11 tối | Gửi Duy Đan số liệu E3 (K3–K6) và E4 (K1, K2, R1, N1, N2, F7) kèm link log; commit và push mọi thay đổi | `git status` sạch, đã push |
| Ngay sau 29/11 | **Trang QR (bắt buộc, SD-14)**, theo thứ tự: view `v_activity_display_state` (SD-13) → bảng `evidence_link_retraction` (SD-10), cả hai qua `gen_views.py` / `gen_triggers.py` kèm test → truy vấn tham số hóa một lô → trang QR theo API A1–A3 | Quét QR thật → tóm tắt → từng hộ, từng hoạt động; 3 nhánh lỗi đúng (D1_D2 mục 6D) |
| Sau trang QR | Bộ mock mè đủ 11 bước theo quy trình Bình Thuận (Việc 1) | Có test chạy đạt |

**Duy Đan — nội dung & minh chứng (Việc 4, 5, Evidence Board, slide)**

| Ngày | Việc | Xong khi |
|---|---|---|
| 28/11 sáng | E1: link trực tiếp tới file CSV khảo sát, kiểm tra thầy mở được. E2: bấm thử 14 link nguồn S1 (Việc 5); nếu kịp, quét thử 5–8 mã QR thật (Việc 4) | Có link trực tiếp; có mẫu số nếu đã kiểm thử |
| 28/11 chiều | Điền Evidence Board 4 dòng, đủ 5 cột, theo SD-18 (E3 cho C1, E4 cho C2). Lấy số liệu từ Mạnh Dũng | Không ô nào trống hoặc ghi "link" chung chung |
| 28/11 tối | Ghép 2 slide cùng Duy Quý theo mẫu gốc của thầy (Việc 8) | File `.pptx` đúng mẫu slide 2–3 |
| Sau 29/11 | Outline báo cáo (Việc 6). Mốc 29/11 không cần: ô link báo cáo ghi "Chưa có" | — |

**Phụ lục — 5 câu hỏi phản biện cho trưởng nhóm**

1. **Đổi cây trồng** — "Nếu mai mốt đổi từ mè sang một nông sản khác hẳn — không ép dầu mà bán thô, hoặc thêm bước sấy/phân loại — mình cần sửa code hay chỉ cần nhập thêm dữ liệu?"
   ✅ Yên tâm nếu: phân biệt rõ "hoạt động canh tác" (linh hoạt) với "loại lô hàng/sự kiện lô" (đang cố định — 4 `lot_type`, 5 `event_type`, viết cứng trong schema). 🚩 Hỏi tiếp nếu: trả lời "tất cả đều linh hoạt" mà không nhắc giới hạn này.
2. **Test lạc có thật không** — "Test chứng minh 'thêm cây lạc không cần sửa gì' có chạy thử một vụ lạc từ đầu đến cuối không, hay chỉ thêm vài dòng cấu hình?"
   ✅ Yên tâm nếu: có kết quả chạy thật, có lô hàng lạc cụ thể, có truy xuất ra kết quả. 🚩 Hỏi tiếp nếu: "mới thêm cấu hình, chưa chạy thử đầu-cuối."
3. **Luồng quét QR** — "Khi quét mã QR trên chai dầu, hệ thống làm các bước gì theo thứ tự? Quét sai mã hoặc mất mạng thì sao?"
   ✅ Yên tâm nếu: kể rõ từng bước, kể cả trường hợp lỗi. 🚩 Hỏi tiếp nếu: chỉ nói chung chung "thì nó hiện thông tin ra."
4. **Ai được ghi dữ liệu** — "Ai được ghi dữ liệu — nông dân, kỹ thuật viên? Ai xác minh? Hệ thống có kiểm tra đúng người không?"
   ✅ Yên tâm nếu: phân biệt rõ vai trò người làm/người ghi/người xác minh trong dữ liệu. 🚩 Hỏi tiếp nếu: "ai đăng nhập cũng ghi/xác minh được hết, chưa phân quyền" → ghi vào mục giới hạn báo cáo.
5. **Sửa dữ liệu, minh chứng cũ ra sao** — "Nếu nông dân sửa một hoạt động đã ghi, ảnh minh chứng cũ có tự áp dụng cho bản sửa không?"
   ✅ Yên tâm nếu: trả lời mạch lạc — ảnh cũ không tự chuyển, phải gắn lại thủ công, có lý do rõ (chủ đích, không phải lỗi). 🚩 Hỏi tiếp nếu: ấp úng hoặc trả lời khác lần trước.

---

### Việc 0 — Canonical data model & DB design (D1/D2) · ✅ ĐÃ XONG (26/11) · Claude dựng bản nháp, B + C phản biện
- **Đầu vào:** Whiteboard D1/D2 (mức khái niệm), quy trình mè, yêu cầu từ khảo sát người dùng và slide công ty, dữ liệu tối thiểu của hệ thống quốc gia.
- **Làm:**
  - **ERD logic:** đầy đủ entity, thuộc tính, khóa chính/khóa ngoại, bản số quan hệ (1–n, n–n). Gồm 4 cụm:
    - Cấu hình theo cây: CropProfile, Stage, ActivityType, EvidenceRequirement
    - Canh tác: Farm, Plot, CultivationCycle, Activity, Evidence, Verification
    - Lô và sự kiện: Lot (thu hoạch / nguyên liệu / chế biến / chai), LotEvent (Aggregation, Transformation, thu mua, vận chuyển), LotInput (lô nào góp vào lô nào, khối lượng)
    - Provenance: Agent (ai ghi, ai xác minh), RecordRevision (bản sửa kèm lý do)
  - **Quy tắc dữ liệu:** bảng nào chỉ ghi thêm (immutable), bảng nào được cập nhật; cách lưu bản sửa; ràng buộc (vd tổng khối lượng góp vào lô = khối lượng lô).
  - **Sơ đồ trạng thái** của hoạt động: thiếu → tự khai → đã xác minh / bị từ chối.
  - **Mapping** sang W3C PROV (Entity/Activity/Agent) và EPCIS (Object/Aggregation/Transformation), và sang bộ dữ liệu tối thiểu của hệ thống quốc gia.
  - **Phác Traceability API:** các endpoint chính (tra cứu theo mã QR lô chai, truy ngược lô, chỉ số đầy đủ, timeline hoạt động).
  - **Sơ đồ tuần tự** cho luồng quét QR → API → truy ngược → trang hiển thị.
- **Đầu ra:** ERD (Mermaid/dbdiagram), DDL SQL bản đầu, sơ đồ trạng thái, sơ đồ tuần tự, bảng mapping; cập nhật Whiteboard.
- **Đạt khi:** mọi tiêu chí của O1/O2 đều trả lời được bằng một truy vấn trên schema; thêm crop profile lạc không cần thêm bảng hay cột.

### Việc 1 — Chuỗi mock dữ liệu (E3) · 26/11 · Claude dựng, B duyệt
- **Đầu vào:** schema từ Việc 0, quy trình mè Bình Thuận, file giống mè.
- **Làm:**
  - Crop profile mè: giai đoạn, loại hoạt động, mốc ngày dự kiến, minh chứng bắt buộc.
  - Crop profile lạc (mock) để chứng minh mở rộng.
  - 3 nông hộ ở Tây Ninh, mỗi hộ 1 lô đất, 1 chu kỳ canh tác vụ Đông Xuân.
  - Nhật ký hoạt động, cố ý cài: 2–3 hoạt động **thiếu minh chứng**, 1 hoạt động **bị từ chối**, 1 hoạt động **lệch mốc ngày**, 1 bản ghi **bị sửa** (có lý do).
  - 3 lô thu hoạch → 1 lô nguyên liệu (ghi ngày thu mua) → 1 lô ép (ghi ngày vận chuyển) → lô chai 80ml và 250ml.
- **Đầu ra:** bảng dữ liệu (Sheets hoặc CSV/JSON).
- **Đạt khi:** mọi entity trên Whiteboard đều có dữ liệu; mỗi kịch bản cài sẵn có ít nhất 1 bản ghi.

### Việc 2 — Prototype kiểm tra truy ngược (E3 → C1) · 26–27/11 · Claude dựng, B kiểm tra
- **Làm:** script nhỏ đọc bộ mock, thực hiện:
  - truy ngược từ mỗi lô chai → tập hộ nguồn + tỷ lệ;
  - tính chỉ số đầy đủ theo crop profile cho từng hộ và từng lô chai;
  - kiểm tra: thêm crop profile lạc không phải sửa schema.
- **Kịch bản kiểm thử (viết trước khi chạy):**

  | # | Kịch bản | Kết quả mong đợi |
  |---|---|---|
  | K1 | Truy ngược lô chai 80ml | Đúng 3 hộ, tỷ lệ khớp khối lượng góp |
  | K2 | Truy ngược lô chai 250ml | Đúng 3 hộ, tỷ lệ khớp |
  | K3 | Hộ có hoạt động thiếu minh chứng | Chỉ số đầy đủ giảm đúng, mục thiếu được liệt kê |
  | K4 | Hoạt động bị từ chối | Tính là chưa đạt, không bị xếp vào "tự khai" |
  | K5 | Bản ghi bị sửa | Còn bản cũ + lý do, bản mới được dùng |
  | K6 | Thêm crop profile lạc | Không đổi cấu trúc bảng; **phải chạy đầy đủ một chu kỳ lạc (gieo → thu hoạch → lô → truy xuất)**, không chỉ chèn cấu hình |

> ✅ 28/11: K6 thật nằm ở `db/run_scenarios.py` (hộ D lạc, chạy đủ chu kỳ và chuỗi sau thu hoạch). `F15` trong `smoke_test.py` đã thay hằng đúng bằng kiểm tra thật, nhưng chỉ là hồi quy cấu hình.

- **Đầu ra:** script + kết quả chạy (log/bảng) → hai dòng Evidence Board (SD-18): **E3 · C1** = K3, K4, K5, K6 → "4/4 kịch bản đạt trên bộ mock 3 hộ mè + 1 chu kỳ lạc; SQLite + PostgreSQL 18"; **E4 · C2** = K1, K2 + R1, N1, N2, F7 → "2/2 kịch bản truy ngược + 4/4 kiểm tra phần không truy được và tỷ lệ; SQLite + PostgreSQL 18". Dẫn link thẳng tới file trong `db/logs/`.
- **Giới hạn cần ghi:** dữ liệu mock, 1 vụ, 3 hộ; chưa thử với dữ liệu thật.

### Việc 3 — Trang QR (C2) · **bắt buộc (SD-14)** · ngay sau 29/11 · Mạnh Dũng, Claude dựng bản demo, Duy Đan duyệt
- **Thiết kế theo khảo sát người dùng:** màn đầu là tóm tắt (27/50 muốn vậy); đọc trong khoảng 30 giây; vị trí đến cấp huyện/xã; hiện rõ mục thiếu minh chứng bằng nhãn tổng quan + màu; thuốc BVTV (tên, liều, ngày, cách ly) phải có.
- **Đầu ra:** trang web chạy trên dữ liệu mock, mở từ mã QR thật.
- **Thiết kế đã có:** danh sách API A1–A3, sơ đồ tuần tự kèm nhánh lỗi, quy tắc nhãn và "bị từ chối" — `docs/D1_D2_schema_design.md` mục 6A–6D.
- **Đạt khi:** quét QR → thấy tóm tắt → bấm xem từng hộ, từng hoạt động, trạng thái minh chứng; mã sai / không có lô / mất mạng hiện đúng thông báo.
- Ở mốc 29/11: E4 vẫn là kiểm thử truy xuất (SD-18), không bị ảnh hưởng; trên slide ghi trang QR "thiết kế xong, trang chưa có".

### Việc 4 — Kiểm thử S1 bằng tay (nâng E2) · 26/11 · **A + B (bắt buộc người làm)**
- **Trước khi đi (30 phút, cả nhóm):** chốt bảng định nghĩa chấm điểm T1–T7 (Đạt / Một phần / Không).
- **Chọn mẫu:** 8–10 sản phẩm có QR truy xuất. Ưu tiên dầu ăn/dầu mè → nông sản khô → rau quả. Kết hợp:
  - 3–4 sản phẩm thật ở siêu thị (WinMart, Bách Hóa Xanh…);
  - 4–5 mẫu từ ảnh bao bì trên sàn thương mại điện tử;
  - 1–2 sản phẩm trên hệ thống truy xuất của nhà nước (lấy link chính thức từ mae.gov.vn; cổng tỉnh Đồng Nai txng.dongnai.gov.vn);
  - 1 trang sản phẩm có Provenance Proof Points (đối chứng T4).
- **Ghi cho mỗi mẫu:** tên, nguồn mẫu (thật / ảnh online / cổng nhà nước), nơi mua, ngày quét, nền tảng QR dẫn tới, ảnh chụp toàn trang (`SP03_iCheck_2026-11-26_1.png`).
- **Chấm:** A và B chấm độc lập → so sánh → ô lệch thì bàn lại, ghi lý do.
- **Đạt khi:** bảng có cột TL (tài liệu) và KT (kiểm thử); gap được viết lại bằng mẫu số, ví dụ "0/9 trang QR thể hiện phần thiếu minh chứng".
- **Hết 26/11 chưa xong:** giữ E2 mức P với dữ liệu tài liệu, ghi vào "Nội dung cần xác nhận".

### Việc 5 — Kiểm nguồn S1 · 26/11 · C
- Bấm thử 14 link [1]–[14]. Link hỏng → báo số để thay nguồn hoặc xóa nhận định.
- Lưu PDF từng trang nguồn (Ctrl+P → Lưu PDF) vào `S1/nguon/`.
- Đối chiếu mỗi ô trong bảng với đúng câu trong nguồn.

### Việc 6 — Outline báo cáo · 26–27/11 · C viết, Claude hỗ trợ
Khung đề xuất (đi theo mạch P → S → O → D → C):
1. Giới thiệu: bối cảnh, vấn đề (P1), mục đích, mục tiêu O1/O2, phạm vi IN/OUT, ranh giới ĐACN – ĐATN
2. Khảo sát: nhu cầu người tiêu dùng (E1), giải pháp hiện có (E2), chuẩn liên quan (EPCIS, PROV, dữ liệu tối thiểu quốc gia), khoảng trống
3. Phân tích yêu cầu: actor, use case, yêu cầu chức năng/phi chức năng, nghiệp vụ canh tác mè
4. Thiết kế: D1 (lõi + crop profile + trạng thái minh chứng), D2 (sự kiện lô, truy ngược, API, trang QR), lý do chọn phương án
5. Hiện thực và kiểm chứng: bộ mock, kịch bản K1–K6, kết quả (E3, E4)
6. Đánh giá, giới hạn, hướng ĐATN
- **Đầu ra:** doc outline có ghi chú nội dung từng mục và mã minh chứng tương ứng.

### Việc 7 — Chốt lập luận · Tối 27/11 · Cả nhóm
- Đọc lại P1, S1 (sau kiểm thử), Mục đích, O1/O2, IN/OUT.
- Nếu kiểm thử thấy đã có sản phẩm làm được T3 → sửa câu gap (3 vế còn lại vẫn đứng).
- Cập nhật quyết định: QR hiển thị rõ "bị từ chối" (SD-12, đã chốt mức chi tiết). SD-14 đã chốt 28/11: trang QR bắt buộc.

### Việc 8 — Ghép 2 slide DefenseBoard · 28/11 · Duy Quý + Duy Đan, Claude dựng bản nháp
- Tải mẫu gốc của thầy từ Drive (mẫu Fishbone & Evidence Board **phiên bản 3**), dùng slide 2–3 (đề tài phần mềm), giữ nguyên định dạng.
- Evidence Board có 5 cột: ID / Claim · Cách thu thập & phạm vi · Kết quả quan sát (kèm mẫu số) · Chất lượng / giới hạn · Nguồn · Owner · Status. Nguồn phải là link thẳng tới log/tài liệu, không phải trang chính repo (hướng dẫn 3.3).
- Tối đa 2 mục tiêu, 2 đóng góp, 4 minh chứng; mỗi ô 1–2 dòng; chưa có thì ghi "Chưa có".
- Đổi nhãn ô trung tâm thành "Mục đích đề tài".
- Điền: mã nhóm, tên đề tài, link báo cáo, link repo, người phụ trách từng E; kiểm tra quyền truy cập của thầy.
- Tên file: `DACN_<MaNhom>_<TenDeTai>_DefenseBoard.pptx`.
- **Checklist 4.2 của thầy** — đánh dấu từng ô trước khi gửi.

### Việc 9 — Gửi thầy · 29/11 · Duy Quý

## 4. Nội dung cần xác nhận với thầy (đưa vào slide)

Chỉ gồm câu hỏi cần GVHD trả lời. Các quyết định nhóm tự chốt nằm ở `Project_Scope_Decision.txt`, không đưa vào đây. "Phụ trách" là người đưa câu hỏi lên slide và theo dõi câu trả lời. Hướng dẫn 4.2 yêu cầu mỗi mục có **điều kiện xử lý**, người phụ trách và thời hạn. (SD-14 về QR đã chốt 28/11 theo ghi nhận họp, không hỏi lại.)

| Mã | Vấn đề | Điều kiện xử lý (nếu thầy chưa có câu trả lời) | Phụ trách | Hạn |
|---|---|---|---|---|
| P1 | Farm mock ở Tây Ninh, quy trình lấy theo Bình Thuận — có phù hợp không? | Giữ như hiện tại, ghi là giả định trong phạm vi | Duy Quý | Hỏi 29/11; chốt trước khi viết chương 1 |
| D1 | Dung sai ngày cho phép khi so lịch canh tác (`tolerance_days`) — thầy/F&S có con số thực tế không? | Giữ giá trị giả định hiện tại (`is_assumption = 1`), ghi vào giới hạn | Mạnh Dũng | Hỏi 29/11; chốt trước khi làm bộ mock 11 bước |
| E1 | Nhu cầu doanh nghiệp chỉ là thông tin thứ cấp — thầy/F&S có số liệu cụ thể hơn không (số hộ, diện tích, cách ghi chép hiện tại)? | E1 giữ mức P, ghi "thông tin thứ cấp" ở cột giới hạn | Duy Đan | Hỏi 29/11 |
| E1 | Khảo sát người dùng thật (nông hộ, kỹ thuật viên) để ĐATN? | Ghi vào hướng ĐATN, không làm ở ĐACN | Duy Đan | Hỏi 29/11 |

## 5. Sau 29/11 đến bảo vệ

| Giai đoạn | Việc | Đầu ra |
|---|---|---|
| Sau buổi góp ý | Sửa lập luận và thiết kế theo ý thầy | Fishbone bản 2 |
| Ngay sau 29/11 → tuần 1 tháng 12 | **Trang QR (bắt buộc, SD-14)**: view nhãn (SD-13), rút lại liên kết (SD-10), truy vấn một lô, trang theo API A1–A3 | Trang QR chạy trên dữ liệu mock |
| Tuần 1–2 tháng 12 | Bộ mock mè 11 bước; chạy lại K1–K6 trên SQLite + PostgreSQL; thêm kịch bản nếu thầy yêu cầu | E3, E4 lên mức tốt hơn |
| Tuần 2–3 tháng 12 | Viết báo cáo đầy đủ theo outline | Báo cáo ĐACN |
| Tuần 3–4 tháng 12 | Slide bảo vệ, tập trả lời câu hỏi hội đồng | Slide + bộ câu hỏi dự kiến |

**Câu hỏi hội đồng cần chuẩn bị sẵn:**
- Đồ án này để làm gì? (P1 + gap)
- Nhà nước đã có hệ thống truy xuất rồi, làm thêm để làm gì? (bổ sung lớp minh chứng, tương thích dữ liệu tối thiểu)
- Hôm nay là mè, mai là cây khác được không? (crop profile, demo lạc, không hard-code vụ)
- Cây khác hẳn như cây lâu năm thì sao? (chu kỳ canh tác không cố định một lần gieo; để ĐATN)
- Minh chứng do nông dân tự khai thì tin được không? (tách độ đầy đủ khỏi xác minh; nêu giới hạn của kiểm tra số lượng/loại và ý nghĩa xác minh)

**ĐATN (tiếp nối):** nhiều farm/vụ/lô; cây thứ 2 thật và một cây lâu năm; chỉ số độ tin cậy; IoT; AI Story; dashboard Visibility/Predictability cho nhà đầu tư; khảo sát phía nông hộ.

## 6. Rủi ro

| Rủi ro | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Kiểm thử S1 không kịp | E2 chỉ mức P từ tài liệu | Giới hạn 1 ngày; nộp P, ghi vào "cần xác nhận" |
| Kiểm thử phát hiện đã có sản phẩm làm được T3 | Phải sửa câu gap | 3 vế còn lại vẫn đứng; sửa tối 27/11 |
| Link nguồn chết (tên miền tỉnh đã sáp nhập) | Mất minh chứng | Lưu PDF mọi nguồn; tránh tên miền tỉnh cũ |
| Trang QR (bắt buộc) trễ | Thiếu điều kiện nghiệm thu khi bảo vệ | Làm ngay sau 29/11; thiết kế API và sơ đồ tuần tự đã xong; làm theo thứ tự ở D1_D2 mục 6D, không thêm tính năng ngoài A1–A3 |
| Kết quả trên slide lệch log | Hội đồng mở log thấy khác | Chỉ lấy số từ `db/logs/`; chạy lại và commit log mỗi khi sửa schema |
| Scope phình theo yêu cầu nhà đầu tư | Trễ ĐACN | Bám bảng phân lớp tiêu chí ở mục 0 |

## 7. Tài liệu liên quan
- Mô tả đề tài #6, quy trình mè Bình Thuận, tổng hợp giống mè, slide OpenSesame: Project "Đồ Án Chuyên Ngành"
- Khảo sát giải pháp: Project `claude/S1_khao_sat_giai_phap.md`
- Thiết kế D1/D2: **bản chính là `docs/D1_D2_schema_design.md` trong repo** (link artifact cũ https://claude.ai/artifact/AKcGZ5Pnius4VpDeTPL9yL có thể đã lệch)
- Hướng dẫn bảo vệ ĐACN v4 và mẫu Fishbone & Evidence Board phiên bản 3: Google Drive của thầy; bản chép text ở `docs/_tham_khao/` (không đẩy lên GitHub)
- Log kết quả kiểm thử: `db/logs/`
- Khảo sát người tiêu dùng: file CSV "Khảo sát nhu cầu sử dụng thông tin truy xuất nguồn gốc sản phẩm nông nghiệp" (n=50, 20–25/10/2026)
- Website sản phẩm F&S: https://www.foodnseed.vn/vi/dau-me
- Repo code (schema, trigger, view, test): https://github.com/pdiqui-17/DigitalX---Traceability-Core
