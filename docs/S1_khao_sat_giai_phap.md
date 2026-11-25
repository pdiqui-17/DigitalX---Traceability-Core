# S1 — Khảo sát giải pháp truy xuất nguồn gốc & quản lý canh tác (bản 4, 25/11/2026)

Trạng thái: **P** (khảo sát tài liệu công bố; chưa kiểm thử trực tiếp)
Phụ trách: [điền] · Hạn hoàn thiện: 27/11
Bản 4: bỏ các nguồn trên tên miền cũ của tỉnh đã sáp nhập (không còn truy cập được) và nguồn bị chuyển hướng/paywall; nhận định nào mất nguồn đã bị xóa. **Nhóm cần tự bấm thử từng link trước khi đưa vào Evidence Board.**

## 1. Cách khảo sát
- Nguồn: website, tài liệu sản phẩm, app store, báo chí, văn bản của cơ quan quản lý; tra cứu 22/11 và 25/11/2026.
- 5 nhóm đối tượng:
  - (A) Nền tảng nhà nước: Hệ thống TXNG nông sản (Bộ NN&MT), hệ thống TXNG tỉnh An Giang
  - (B) Nền tảng TXNG thương mại Việt Nam: iCheck Trace
  - (C) TXNG blockchain toàn chuỗi: TE-FOOD
  - (D) Quản lý canh tác first-mile / theo quy trình (PoP): Cropin, Farmforce
  - (E) Công bố tuyên bố có minh chứng cho người mua: Provenance
  - (F) Chuẩn: GS1 EPCIS 2.0, W3C PROV
- Tiêu chí (từ khảo sát người tiêu dùng n=50 và yêu cầu doanh nghiệp F&S):
  - T1 Nhật ký hoạt động canh tác gắn lô
  - T2 Minh chứng gắn từng hoạt động
  - T3 Hiển thị phần thiếu minh chứng cho người tiêu dùng
  - T4 Phân biệt "tự khai" và "đã xác minh"
  - T5 Lịch sử chỉnh sửa / chống sửa ngầm
  - T6 Truy ngược qua gộp/tách lô và chuyển hóa (hạt mè → dầu mè)
  - T7 Cấu hình quy trình theo loại cây

Ký hiệu: Có = tài liệu nêu rõ · ? = tài liệu không đề cập (không có nghĩa là không có) · — = ngoài phạm vi giải pháp

## 2. Bảng so sánh

| Giải pháp | T1 | T2 | T3 | T4 | T5 | T6 | T7 | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| (A) Hệ thống TXNG nông sản Bộ NN&MT | Một phần (mã vùng trồng gắn nhật ký sản xuất) [1] | ? | ? | Một phần (UBND xã hậu kiểm đăng ký mã vùng trồng; dữ liệu do DN/nông hộ cập nhật) [1] | ? | Cơ quan quản lý thừa nhận thông tin ở khâu thu gom, giao nhận, **chia/ghép lô** chưa được chuyển đầy đủ theo hàng hóa [2] | ? | Dữ liệu tối thiểu: nông hộ, vùng/cơ sở sản xuất, thời gian sản xuất–thu hoạch, các khâu, tem, QR [3] |
| (A) Hệ thống TXNG tỉnh An Giang | ? | ? | ? | Một phần (Sở KH&CN duyệt tài khoản đơn vị, không phải từng hoạt động) [4] | ? | ? | ? | |
| (B) iCheck Trace | Có (nhật ký điện tử) [5] | ? | ? | ? | ? | Có quản lý lô [5]; gộp/chuyển hóa ? | ? | Báo chí ghi nhận tình trạng tem "đối phó" [6] |
| (C) TE-FOOD | ? | ? | ? | ? | Có (blockchain) [7] | ? | ? | Mỗi hộp sữa Vinamilk có QR riêng để người tiêu dùng xem lịch sử sản phẩm [7] |
| (D) Cropin, Farmforce | Có (Farmforce: quản lý hoạt động đồng ruộng) [9] | ? | ? | ? | ? | ? | **Có** (Cropin: lịch hoạt động riêng theo cây, khuyến nghị PoP) [8] | B2B, hướng doanh nghiệp nông nghiệp |
| (E) Provenance | — | Có (minh chứng đi kèm tuyên bố) [11] | ? | **Có** (Evidenced: Provenance duyệt minh chứng; Verified: bên thứ ba xác nhận) [11] | ? | — | — | Ở cấp **tuyên bố sản phẩm/thương hiệu**, không ở cấp hoạt động canh tác |
| (F1) GS1 EPCIS 2.0 | — | Có (dữ liệu sensor, chi tiết chứng nhận) [12] | — | — | — | **Có** (sự kiện Aggregation, Transformation) [13] | — | Chuẩn sự kiện truy xuất |
| (F2) W3C PROV | — | — | — | Hỗ trợ (Agent) [14] | Hỗ trợ [14] | Hỗ trợ [14] | — | Mô hình provenance: entity, activity, agent |

## 3. Phát hiện
1. **Đăng ký ≠ có dữ liệu.** Đến 31/10/2026 Hệ thống TXNG nông sản quốc gia có 821.734 sản phẩm đăng ký nhưng chỉ 161.324 sản phẩm (≈19,6%) thuộc 20 dòng có dữ liệu truy xuất [1]. Cơ quan quản lý nói mã QR chỉ là phương tiện truy cập thông tin [2].
2. **Chia/ghép lô là chỗ đứt gãy** được chính cơ quan quản lý thừa nhận [2]. Đây đúng là bước hạt mè từ nhiều hộ → một lô ép dầu.
3. **Phân biệt mức xác minh đã tồn tại (Provenance)** [11], nhưng cho tuyên bố cấp sản phẩm/thương hiệu, không cho từng hoạt động canh tác.
4. **Cấu hình theo cây (PoP)** đã có ở Cropin [8], nhưng là công cụ cho doanh nghiệp; tài liệu không mô tả việc đưa trạng thái minh chứng ra trang QR cho người tiêu dùng.
5. Không tài liệu nào khảo sát mô tả **hiển thị phần còn thiếu minh chứng (T3)** cho người tiêu dùng.

## 4. Khoảng trống (giả thuyết, chưa xác nhận)
Chưa thấy giải pháp nào kết hợp: (1) quy trình theo cây làm "khung kỳ vọng" → (2) minh chứng và trạng thái xác minh **theo từng hoạt động** → (3) giữ provenance qua **gộp lô và chuyển hóa** → (4) trang QR thể hiện trung thực độ đầy đủ so với quy trình — cho chuỗi khép kín quy mô vừa như mè → dầu mè, và **tương thích dữ liệu tối thiểu của hệ thống quốc gia**.

## 5. Hệ quả cho thiết kế
- Schema xuất được bộ dữ liệu tối thiểu của Hệ thống TXNG nông sản quốc gia → bổ sung lớp minh chứng, không cạnh tranh.
- Mô hình sự kiện tham chiếu EPCIS (Object/Aggregation/Transformation) và provenance tham chiếu PROV (Entity/Activity/Agent).
- Trạng thái theo từng hoạt động: thiếu / tự khai / đã xác minh / bị từ chối.

## 6. Giới hạn
- Chỉ dựa trên tài liệu công bố; "?" có thể là tính năng có nhưng không quảng bá.
- Chưa kiểm thử trực tiếp ứng dụng nào; chưa tra cứu thử một mã QR trên Hệ thống TXNG nông sản quốc gia.
- Số liệu hệ thống quốc gia lấy từ báo chí dẫn lời Bộ NN&MT (thứ cấp).
- Nguồn [13] là bản nháp xem trước; nên đối chiếu thêm với văn bản chuẩn EPCIS 2.0 của GS1.
- TCVN 12850:2019 (yêu cầu chung đối với hệ thống TXNG) nên được dẫn trong báo cáo, nhưng hiện chưa có link mở được — nhóm cần tìm bản văn bản để dẫn.

## 7. Việc cần làm để nâng E2 (trước 27/11)
- Bấm thử từng link [1]–[14].
- Quét QR trên 5–10 sản phẩm nông sản/dầu ăn thật, chấm T1–T7, chụp màn hình.
- Tra cứu thử 1–2 sản phẩm trên Hệ thống TXNG nông sản quốc gia, ghi lại màn hình người tiêu dùng thấy gì.

## Nguồn
[1] Thời báo Tài chính VN — số liệu Hệ thống TXNG nông sản đến 31/10/2026: https://thoibaotaichinhvietnam.vn/truy-xuat-nguon-goc-nong-san-minh-bach-du-lieu-de-kiem-soat-toan-chuoi-207416-207416.html
[2] Tiền Phong — phỏng vấn Vụ trưởng Vụ KH&CN (chia/ghép lô; QR chỉ là phương tiện): https://tienphong.vn/truy-xuat-nguon-goc-nong-san-ro-trach-nhiem-tung-khau-post1893961.tpo
[3] Báo Đầu tư — dữ liệu tối thiểu theo kế hoạch của Bộ NN&MT: https://baodautu.vn/xay-dung-he-thong-truy-xuat-nguon-goc-nong-san-quy-mo-quoc-gia-d487046.html
[4] Hướng dẫn Hệ thống TXNG tỉnh An Giang (PDF): https://longxuyen.angiang.gov.vn/sites/default/files/2026/09/filedinhkembaiviet/huong-dan-tham-gia-he-thong-truy-xuat-nguon-goc.pdf
[5] iCheck Trace (App Store): https://apps.apple.com/vn/app/id1579441923
[6] VnBusiness — tem đối phó: https://vnbusiness.vn/vi-sao-htx-phai-minh-bach-san-pham.html
[7] TE-FOOD (Medium) — Vinamilk Organic Milk: https://medium.com/te-food/the-largest-dairy-company-in-vietnam-implements-te-food-for-organic-milk-ea9765f1c48f
[8] Cropin — lịch hoạt động theo cây, PoP: https://www.cropin.com/smartsales/
[9] FAO AgriTech Observatory — Farmforce: https://agritechobservatory.review.fao.org/fr/farmforce
[10] TraceX — chuỗi cung ứng mè (bối cảnh): https://tracextech.com/sesame-supply-chain-smallholder-farms-to-global-markets/
[11] Provenance — Evidenced/Verified Proof Points: https://www.provenance.org/r/cult-beauty
[12] GS1 — EPCIS/CBV 2.0: https://www.gs1.org/epcis
[13] Dublin Core MSI — các loại sự kiện EPCIS (bản nháp xem trước): https://msi.dublincore.org/standards/epcis
[14] Wikipedia — W3C PROV: https://en.wikipedia.org/wiki/W3C_Prov
