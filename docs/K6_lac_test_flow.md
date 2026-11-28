# K6 — Luồng kiểm tra "đổi cây mè sang cây lạc"

> Đề tài #6 · Traceability Core v0.5 · 26/11/2026 · cập nhật 28/11/2026
>
> **Bằng chứng K6 duy nhất:** hộ D trong `db/seed_lac.sql`, chạy bởi `db/run_scenarios.py` (SD-15). Kết quả 28/11: **đạt trên SQLite và PostgreSQL 18** — log `db/logs/k1_k6_sqlite.txt`, `db/logs/k1_k6_postgres.txt`. Đoạn `F15` (hộ E) trong `smoke_test.py` chỉ là hồi quy cấu hình lạc, không dùng làm K6.

## Cách chạy

```bash
cd db
python run_scenarios.py lac                 # SQLite
python run_scenarios.py lac --pg            # PostgreSQL (cấu hình db/.env)
python run_scenarios.py lac --raw           # kèm câu SQL và dữ liệu thô
```

---

## Câu hỏi đặt ra

> *"Test chứng minh 'thêm cây lạc không cần sửa gì' — nó có chạy thử một vụ lạc từ đầu đến cuối không, hay chỉ thêm vài dòng thông tin rồi báo xong?"*

**Trả lời thẳng:** Có, K6 chạy một vụ lạc đầy đủ từ đầu đến cuối. Không phải chỉ thêm cấu hình rồi trả `True`.

---

## Hai điều cần phân biệt

Khi nói "đổi cây", có hai lớp hoàn toàn khác nhau:

**Lớp 1 — Cấu hình cây trồng:** Mô tả cây lạc "là gì" — có mấy giai đoạn, từng giai đoạn cần làm gì, bắt buộc hay tùy chọn, cần minh chứng gì, thời gian cách ly thuốc bao nhiêu ngày. Lớp này chỉ cần INSERT dữ liệu, không sờ vào cấu trúc bảng.

**Lớp 2 — Thực tế canh tác:** Một nông hộ cụ thể trồng lạc, ghi nhật ký, thu hoạch, ra lô, rồi hệ thống tính toán trạng thái và truy ngược. Lớp này mới chứng minh schema "hiểu" được lạc, không chỉ "biết tên" lạc.

K6 làm **cả hai lớp**, và quan trọng hơn, nó **hỏi kết quả thật** ở cuối thay vì tự trả lời `True`.

---

## Luồng K6 chạy gì

### Giai đoạn 1 — Khai báo cây lạc (không có DDL)

Toàn bộ phần này chỉ dùng `INSERT`, không có `CREATE TABLE`, `ALTER TABLE`, hay `DROP` nào. Hệ thống được thiết kế để quy trình của mỗi cây là dữ liệu, không phải code.

Nhóm khai báo:
- Cây lạc L14 với sơ đồ giai đoạn riêng (làm đất → chăm sóc → thu hoạch)
- Từng hoạt động trong mỗi giai đoạn, loại nào bắt buộc, loại nào tùy chọn
- Minh chứng bắt buộc cho từng loại hoạt động (ảnh cho bón lót, phiếu cân cho thu hoạch)
- Luật thời gian cách ly thuốc BVTV riêng cho cây lạc

Điểm cần lưu ý: thuốc Y được dùng trong cả vụ mè lẫn vụ lạc, nhưng chỉ có luật cách ly cho lạc. Hệ thống sẽ phải phân biệt được: cùng một loại thuốc, hai kết luận khác nhau tùy theo cây.

### Giai đoạn 2 — Vụ canh tác thật của Hộ D

Sau khi có cấu hình, test tạo ra **một vụ canh tác cụ thể** của một nông hộ trồng lạc:

**Bắt đầu vụ:** Hộ đăng ký lô đất, ghi ngày bắt đầu, khai báo mốc gieo. Từ mốc này, hệ thống sẽ tự tính lịch dự kiến cho từng hoạt động bắt buộc.

**Trong vụ — bón lót:** Hộ ghi nhật ký bón lót, khai báo lượng phân, đính kèm ảnh minh chứng. Kỹ thuật viên vào xác minh. Lúc này hệ thống cần phán xét: hoạt động này có đúng lịch không, có đủ minh chứng không, trạng thái xác minh là gì.

**Trong vụ — phun thuốc:** Hộ ghi phun thuốc Y vào một ngày cụ thể. Hệ thống cần kiểm tra: ngày phun cách ngày thu hoạch bao nhiêu ngày, có vi phạm thời gian cách ly của lạc không (không vi phạm, vì phun đủ sớm). Đây là điểm đối chiếu trực tiếp với bên mè: cùng thuốc Y đó, bên mè vi phạm vì không có luật cách ly, bên lạc thì không vi phạm vì có luật và đủ ngày cách ly.

**Thu hoạch:** Hộ ghi thu hoạch, có phiếu cân. Hệ thống sinh ra một lô thu hoạch lạc.

### Giai đoạn 3 — Chuỗi sau thu hoạch (trong run_scenarios.py)

Lô thu hoạch đi qua rang (transformation), có mốc vận chuyển, rồi đóng gói túi zip. Cuối cùng có một lô thành phẩm mang mã QR để truy ngược.

### Giai đoạn 4 — Hỏi kết quả, không tự trả lời

Đây là phần cốt lõi phân biệt "kiểm tra thật" với "kiểm tra giả". Sau khi toàn bộ dữ liệu được nạp, test hỏi hệ thống sáu câu độc lập (câu 5–6 là điều kiện thêm trong `run_scenarios.py`):

**Câu 1:** Truy ngược từ lô thành phẩm lạc — hệ thống có tìm đúng về lô thu hoạch nguồn không? Tỷ trọng có phải 100% không (vì chỉ có một hộ)?

**Câu 2:** Độ đầy đủ của chu kỳ — hệ thống có nhận ra chu kỳ lạc này là `complete` không (vì đã ghi đủ hoạt động bắt buộc và có minh chứng)?

**Câu 3:** Trạng thái bón lót — hệ thống có trả `complete / verified` đúng không?

**Câu 4:** Có bảng mới nào được tạo ra không? (Không được có — toàn bộ phải chạy trong cùng schema gốc.)

**Câu 5:** Có đủ 2 crop profile (mè + lạc) trong cùng một CSDL không?

**Câu 6:** Phun thuốc Y của hộ D có vi phạm thời gian cách ly của lạc không? (Phải = 0 vi phạm: cách ly 5 ngày, phun trước thu hoạch đủ lâu.)

Chỉ khi cả sáu câu trả lời đúng, K6 mới được tính là đạt. Nếu thiếu một câu, test trả về `❌`.

---

## Vì sao cách này chứng minh được "không cần sửa schema"

Nếu schema chỉ "biết tên" lạc mà không thực sự hiểu luồng canh tác lạc, thì:
- Câu 1 sẽ trả về rỗng hoặc sai tỷ trọng
- Câu 2 sẽ trả về `incomplete` hoặc `undetermined` dù đã ghi đủ
- Câu 3 sẽ không có trạng thái `verified`

Tất cả ba câu này đều dùng cùng view và cùng logic tính toán mà bên mè dùng. Không có đường tắt nào. Hệ thống xử lý lạc bằng đúng cơ chế nó dùng cho mè, chỉ khác nhau ở dữ liệu cấu hình đầu vào.

---

## Điều test này KHÔNG chứng minh

Để trả lời trung thực, K6 không phải là một vụ lạc "thật" theo đủ quy trình canh tác lạc. Nhóm chỉ mô phỏng hai hoạt động bắt buộc (bón lót và thu hoạch) và một hoạt động có điều kiện (phun thuốc) để đủ minh chứng cho mục đích kiểm tra schema. (Bên mè hiện cũng mới có 3 loại hoạt động trong `seed_me.sql`; bộ mock mè đủ 11 bước theo quy trình Bình Thuận là việc sau 29/11.) Quy trình canh tác lạc thật có thể phức tạp hơn — nhưng điều đó là vấn đề của dữ liệu cấu hình, không phải của schema.

Nói cách khác: schema đã sẵn sàng cho lạc (và bất kỳ cây nào khác), còn việc điền đúng quy trình canh tác lạc đầy đủ vào là công việc ngoài phạm vi ĐACN.

---

## Tóm tắt cho câu trả lời hội đồng

> K6 chạy một vụ lạc từ khai báo cây → đăng ký vụ → ghi nhật ký canh tác → thu hoạch → ra lô → rang → đóng gói → truy ngược, trên cả SQLite và PostgreSQL. Cuối cùng hệ thống được hỏi sáu câu độc lập và phải trả lời đúng mới tính là đạt. Không có dòng nào trong sáu câu hỏi đó được viết cứng kết quả. Toàn bộ quá trình này chạy trong cùng schema mà bên mè dùng, không có bảng mới hay cột mới nào được tạo ra.
