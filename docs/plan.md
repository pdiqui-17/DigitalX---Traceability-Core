# Plan ĐACN — Lõi truy xuất có minh chứng cho chuỗi mè → dầu mè

> Đề tài #6 — Agricultural Digital Thread & Evidence-aware Traceability
> Cập nhật: 25/11/2026 · Nhóm 3 người (A, B, C — điền tên)
> Mốc gần nhất: **29/11/2026 gửi thầy Fishbone & Evidence Board** · Bảo vệ ĐACN: cuối năm (chờ lịch)

---

## 0. Những gì đã chốt

| Hạng mục | Quyết định | Nguồn |
|---|---|---|
| Đề tài | Vẫn là đề tài #6; ĐACN giới hạn ở cây mè vì đã có quy trình và dữ liệu | Họp với thầy |
| Phạm vi canh tác | Mè đen 2 vỏ, quy trình Bình Thuận làm khung; farm mock đặt ở Tây Ninh | Tài liệu trong Project, website F&S |
| Sản phẩm | Dầu mè rang chai 80ml / 250ml (F&S). Can 25kg bán sỉ: ngoài phạm vi | foodnseed.vn |
| Thu mua, vận chuyển | Chỉ ghi ngày | Họp với thầy |
| Dữ liệu demo | Mock | Họp với thầy |
| QR | Bắt buộc, làm trước (nhà đầu tư yêu cầu) | Họp với thầy |
| Mở rộng | Lõi dùng chung + crop profile; cây thứ 2 để demo là **lạc (mock)**; không hard-code "một vụ = một lần gieo" | Nhóm chốt 25/11 |
| Trạng thái minh chứng | 4 trạng thái: thiếu / tự khai / đã xác minh / bị từ chối | Nhóm chốt 25/11 |
| Lớp tiêu chí | ĐACN chứng minh Assurance + QR; Visibility, Predictability để ĐATN nhưng schema lưu sẵn dữ liệu | Đối chiếu slide công ty |
| Khung báo cáo | Hướng dẫn bảo vệ ĐACN v4 + mẫu Fishbone & Evidence Board v4 (slide 2–3, đề tài phần mềm) | Drive của thầy |

## 1. Lập luận đề tài (bản nháp)

- **P1 — Vấn đề:** Doanh nghiệp đầu tư vùng trồng mè phân tán nhưng không kiểm chứng được hoạt động canh tác; QR trên chai dầu không chứng minh được nguồn gốc. Hệ thống quốc gia: 821.734 sản phẩm đăng ký nhưng chỉ 161.324 (≈19,6%) có dữ liệu truy xuất.
- **S1 — Khảo sát:** Giải pháp hiện có làm từng mảnh; chưa thấy giải pháp nào kết hợp (1) quy trình theo cây làm khung kỳ vọng, (2) minh chứng và trạng thái xác minh theo từng hoạt động, (3) truy qua gộp lô và chuyển hóa, (4) trang QR thể hiện trung thực độ đầy đủ.
- **Mục đích:** Lõi dữ liệu truy xuất có minh chứng cho chuỗi mè – dầu mè, cho phép truy ngược từ lô dầu về từng hoạt động canh tác và mức độ minh chứng của hoạt động đó.
- **O1:** Mô hình dữ liệu canh tác có minh chứng, cấu hình theo loại cây.
  *Tiêu chí:* biểu diễn đủ 11 bước quy trình mè; mỗi hoạt động có 1 trong 4 trạng thái; thêm cây lạc chỉ bằng cấu hình, không sửa schema; xuất được dữ liệu tối thiểu của hệ thống quốc gia.
- **O2:** Khả năng truy ngược từ QR lô dầu, qua gộp lô, về minh chứng.
  *Tiêu chí:* trên bộ mock (3 hộ → 1 lô ép → 2 lô chai) mọi chai truy đúng tập hộ nguồn kèm tỷ lệ; chỉ số đầy đủ tính đúng ở các kịch bản thiếu minh chứng cài sẵn.
- **D1 → O1:** Lõi entity chung + crop profile; sự kiện chỉ ghi thêm, sửa tạo bản mới kèm lý do (tham chiếu W3C PROV).
- **D2 → O2:** Sự kiện lô theo EPCIS (Aggregation, Transformation), đồ thị nguồn gốc lô, Traceability API, trang QR (tóm tắt trước, chi tiết sau).
- **C1:** Traceability core (E3) · **C2:** Trang QR truy ngược (E4)

## 2. Trạng thái hiện tại

| Mã | Nội dung | Trạng thái | Ở đâu |
|---|---|---|---|
| E1 · P1 | Khảo sát người tiêu dùng n=50 + số liệu hệ thống quốc gia | Có bản phân tích, mức **P** | Chat 22/11; file CSV khảo sát |
| E2 · S1 | Khảo sát giải pháp, 8 giải pháp, 7 tiêu chí | Bản 4, mức **P**, **chưa kiểm thử trực tiếp** | Project: `claude/S1_khao_sat_giai_phap.md` |
| D1/D2 | Thiết kế lõi, crop profile, luồng lô | **Mới ở mức khái niệm** — chưa có ERD, thuộc tính, khóa, DDL, API | Whiteboard: https://claude.ai/artifact/AKcGZ5Pnius4VpDeTPL9yL |
| E3 · C1 | Chuỗi mock + kiểm tra truy ngược | **Chưa có (M)** | — |
| E4 · C2 | Trang QR | **Chưa có (M)** | — |
| Outline báo cáo | | **Chưa có** | — |
| 2 slide DefenseBoard | | **Chưa có** | — |

## 3. Kế hoạch chi tiết đến 29/11

> Thứ tự đúng: **thiết kế dữ liệu (Việc 0) → dữ liệu mock theo schema (Việc 1) → prototype kiểm tra (Việc 2)**. Đây là lõi của đề tài #6 ("canonical schema, provenance model, traceability API"), nên phải có trước khi sinh dữ liệu.

### Việc 0 — Canonical data model & DB design (D1/D2) · 25–26/11 · Claude dựng bản nháp, B + C phản biện
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
  | K6 | Thêm crop profile lạc | Không đổi cấu trúc bảng |

- **Đầu ra:** script + kết quả chạy (log/bảng) → dòng **E3 · C1** với mẫu số, ví dụ "6/6 kịch bản đạt trên bộ mock 3 hộ".
- **Giới hạn cần ghi:** dữ liệu mock, 1 vụ, 3 hộ; chưa thử với dữ liệu thật.

### Việc 3 — Trang QR (E4 → C2) · 25–27/11 · Claude dựng bản demo, C duyệt
- **Thiết kế theo khảo sát người dùng:** màn đầu là tóm tắt (27/50 muốn vậy); đọc trong khoảng 30 giây; vị trí đến cấp huyện/xã; hiện rõ mục thiếu minh chứng bằng nhãn tổng quan + màu; thuốc BVTV (tên, liều, ngày, cách ly) phải có.
- **Đầu ra:** trang web chạy trên dữ liệu mock, mở từ mã QR thật.
- **Đạt khi:** quét QR → thấy tóm tắt → bấm xem từng hộ, từng hoạt động, trạng thái minh chứng.
- Nếu không kịp trước 29/11: E4 ghi **M** kèm kế hoạch; không ảnh hưởng mức sẵn sàng của các phần khác.

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
- Chốt 2 câu hỏi mở trên Whiteboard (hiện "bị từ chối" trên QR? sai lệch mốc ngày cho phép?) hoặc đưa vào "Nội dung cần xác nhận".

### Việc 8 — Ghép 2 slide DefenseBoard · 28/11 · A, Claude dựng bản nháp
- Tải mẫu gốc của thầy từ Drive, dùng slide 2–3 (đề tài phần mềm), giữ nguyên định dạng.
- Tối đa 2 mục tiêu, 2 đóng góp, 4 minh chứng; mỗi ô 1–2 dòng; chưa có thì ghi "Chưa có".
- Đổi nhãn ô trung tâm thành "Mục đích đề tài".
- Điền: mã nhóm, tên đề tài, link báo cáo, link repo, người phụ trách từng E; kiểm tra quyền truy cập của thầy.
- Tên file: `DACN_<MaNhom>_<TenDeTai>_DefenseBoard.pptx`.
- **Checklist 4.2 của thầy** — đánh dấu từng ô trước khi gửi.

### Việc 9 — Gửi thầy · 29/11 · Dũng

## 4. Nội dung cần xác nhận (đưa vào slide)

| Mã | Vấn đề | Phụ trách | Hạn |
|---|---|---|---|
| E1 | Nhu cầu doanh nghiệp chỉ là thông tin thứ cấp ("theo thông tin khách hàng") — thầy/F&S có số liệu cụ thể hơn không (số hộ, diện tích, cách ghi chép hiện tại)? | Dũng | Buổi góp ý |
| D1 | Trang QR có hiện trạng thái "bị từ chối" không, hay gộp thành "chưa xác minh được"? | Dũng | Buổi góp ý |
| P1 | Farm mock ở Tây Ninh, quy trình lấy theo Bình Thuận — có phù hợp không? | Dũng | Buổi góp ý |
| E1 | Khảo sát người dùng thật (nông hộ, kỹ thuật viên) để ĐATN? | Dũng | Buổi góp ý |

## 5. Sau 29/11 đến bảo vệ

| Giai đoạn | Việc | Đầu ra |
|---|---|---|
| Sau buổi góp ý | Sửa lập luận và thiết kế theo ý thầy | Fishbone bản 2 |
| Tuần 1–2 tháng 12 | Hoàn thiện schema, Traceability API, trang QR; chạy lại K1–K6; thêm kịch bản nếu thầy yêu cầu | E3, E4 lên mức tốt hơn |
| Tuần 2–3 tháng 12 | Viết báo cáo đầy đủ theo outline | Báo cáo ĐACN |
| Tuần 3–4 tháng 12 | Slide bảo vệ, tập trả lời câu hỏi hội đồng | Slide + bộ câu hỏi dự kiến |

**Câu hỏi hội đồng cần chuẩn bị sẵn:**
- Đồ án này để làm gì? (P1 + gap)
- Nhà nước đã có hệ thống truy xuất rồi, làm thêm để làm gì? (bổ sung lớp minh chứng, tương thích dữ liệu tối thiểu)
- Hôm nay là mè, mai là cây khác được không? (crop profile, demo lạc, không hard-code vụ)
- Cây khác hẳn như cây lâu năm thì sao? (chu kỳ canh tác không cố định một lần gieo; để ĐATN)
- Minh chứng do nông dân tự khai thì tin được không? (4 trạng thái, phân biệt tự khai và đã xác minh)

**ĐATN (tiếp nối):** nhiều farm/vụ/lô; cây thứ 2 thật và một cây lâu năm; chỉ số độ tin cậy; IoT; AI Story; dashboard Visibility/Predictability cho nhà đầu tư; khảo sát phía nông hộ.

## 6. Rủi ro

| Rủi ro | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Kiểm thử S1 không kịp | E2 chỉ mức P từ tài liệu | Giới hạn 1 ngày; nộp P, ghi vào "cần xác nhận" |
| Kiểm thử phát hiện đã có sản phẩm làm được T3 | Phải sửa câu gap | 3 vế còn lại vẫn đứng; sửa tối 27/11 |
| Link nguồn chết (tên miền tỉnh đã sáp nhập) | Mất minh chứng | Lưu PDF mọi nguồn; tránh tên miền tỉnh cũ |
| Trang QR không kịp trước 29/11 | E4 mức M | Thầy chấp nhận M với kế hoạch rõ ràng |
| Scope phình theo yêu cầu nhà đầu tư | Trễ ĐACN | Bám bảng phân lớp tiêu chí ở mục 0 |

## 7. Tài liệu liên quan
- Mô tả đề tài #6, quy trình mè Bình Thuận, tổng hợp giống mè, slide OpenSesame: Project "Đồ Án Chuyên Ngành"
- Khảo sát giải pháp: Project `claude/S1_khao_sat_giai_phap.md`
- Thiết kế D1/D2: https://claude.ai/artifact/AKcGZ5Pnius4VpDeTPL9yL
- Hướng dẫn bảo vệ ĐACN v4 và mẫu Fishbone & Evidence Board v4: Google Drive của thầy
- Khảo sát người tiêu dùng: file CSV "Khảo sát nhu cầu sử dụng thông tin truy xuất nguồn gốc sản phẩm nông nghiệp" (n=50, 20–25/10/2026)
- Website sản phẩm F&S: https://www.foodnseed.vn/vi/dau-me
