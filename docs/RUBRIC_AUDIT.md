# Kiểm tra rubric HCMUS

Phạm vi cá nhân là Track B (TV1). Kết quả ở đây đánh giá bằng chứng của nhánh bàn giao. Mỗi hàng đánh giá theo yêu cầu của [rubric chính thức](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/clustering-paper/).

| Yêu cầu | Điểm | Owner | Bằng chứng và cách kiểm tra | Kết quả | Trạng thái |
|---|---:|---|---|---|---|
| Bối cảnh và đóng góp | 10 | TV1 | Đọc `report/sections/introduction.tex` | Có ví dụ mạng cộng tác, LPA, retention, Louvain và Leiden. Đóng góp kỹ thuật, lý thuyết, thực nghiệm được giải thích riêng. | PASS |
| Phương pháp | 20 | TV1 | `report/sections/methods.tex`, `src/flpa/algorithms.py` và `python -m pytest -q tests/test_algorithms.py` | Có phương trình, pipeline, mã giả, ví dụ phá hoà, chứng minh bất biến và chi phí theo số lần quét hay lượt hàng đợi. | PASS |
| Phê bình | 15 | TV1 và TV2 | Đọc `report/sections/critical_analysis.tex` và kết quả E1/E3 | Có ba điểm mạnh, giả định topology, hạn chế maximality và thời gian, cùng hướng thử seed lồng nhau và FLPA khởi tạo Leiden. | PASS cho bản TV1 |
| Cài đặt và tái hiện ≥2 thí nghiệm chính | 20 | TV1 E1, TV2 E2 | `python -m pytest -q` và `python scripts/verify_results.py results/e1 results/author/e1` | E1 có 600 lượt hoàn thành, ba panel tăng kích thước, ba thuật toán tự cài và Leiden. Figure 4 thuộc E2 của TV2. | BLOCKED cấp nhóm |
| Sai lệch và ablation | 15 | TV1 E1/E3, TV2 E2 | `python scripts/verify_results.py results/e3` và `python scripts/compare_results.py` | So sánh Figure 1, đối chiếu cùng topology với nhánh C của tác giả, kiểm FIFO/LIFO và enqueue-all. E3 đủ 90 lượt hoàn thành. Cần thảo luận sai lệch E2 khi TV2 bàn giao. | PASS cho phần TV1 |
| Dataset mới | 15 | TV2 | So sánh bảng/phần Methods của paper với nguồn [SNAP email-Eu-core](https://snap.stanford.edu/data/email-Eu-core.html) | Paper dùng các mạng thực khác. Kết quả, notebook và phân tích E4 thuộc TV2. | BLOCKED |
| Chất lượng kết quả và sản phẩm | 5 | TV1 và TV2 | Kiểm tra từng gate trong bảng dưới | Mã nguồn, bằng chứng TV1 và báo cáo nháp đã có trên nhánh. Bản nhóm và W&B public còn phụ thuộc dữ liệu hoặc tài khoản. | BLOCKED cấp nhóm |

## Kiểm tra sản phẩm

| Gate | Cách kiểm tra | Owner | Trạng thái |
|---|---|---|---|
| PDF bài báo nguyên vẹn | Mở `paper/paper.pdf`, kiểm tiêu đề, DOI, 11 trang và SHA-256 `da7f79cbe958d456d14c2817ddd420fbdcb02f54fe672d0be7c133ba646865ad`. | TV1 | PASS |
| Marimo | Export HTML thực thi tất cả ô, với cả `main` và `FLPA_NOTEBOOK_MODE=smoke` trên hai notebook. | TV1 E1/E3, TV2 E2/E4 | PASS E1/E3 |
| Molab | Mở các link trong README bằng phiên chưa đăng nhập. Kiểm tiêu đề, mã notebook và snapshot kết quả ở iframe preview. | TV1 E1/E3, TV2 E2/E4 | PASS E1/E3 |
| Tracking W&B | Kiểm `tracking.json` trong năm bundle, bản ghi `.wandb` và các bảng/artifact cục bộ. | TV1 E1/E3, TV2 E2/E4 | PASS offline với năm run. BLOCKED public. Cần đăng nhập, sync vào entity của nhóm và bật Public. |
| IEEE | `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex` trong `report/`. Kiểm layout hai cột, hình, bảng, công thức và tài liệu tham khảo. | TV1 và TV2 | PASS build bản nháp TV1 dài 7 trang. BLOCKED `Report.pdf` và số trang bản nhóm chờ E2/E4. |
| Repository và tái lập | Clean clone nhánh GitHub vào thư mục tạm, cài lại requirements, chạy `pip check`, `pytest`, smoke, verifier và các notebook theo [hướng dẫn tái lập](REPRODUCIBILITY.md). | TV1 | PASS cho phần TV1 |
| Danh sách thành viên | Đối chiếu tên, MSSV và vai trò trong `README.md` với thông tin thành viên đã xác nhận. | Chung | PASS |

Clean clone dùng hai venv. `pip check` báo không có dependency hỏng. `python -m pytest -q` có **69 PASS, 0 FAIL** trên cả Python 3.9.25 và 3.12.15. Hai smoke CLI trên Python 3.12 hoàn thành **12/12 (E1)** và **3/3 (E3)**, rồi qua `verify_results.py`. Cả 12 lượt E1 có cùng hash graph, số cụm, bộ đếm và metrics với các lượt main trùng cấu hình và cặp seed. Cảnh báo pytest đến từ API pyparsing cũ trong Matplotlib.

Verifier đã kiểm **600 E1**, **90 E3**, **54 lượt C tham chiếu** và **99 lượt pilot**. Các bundle này có 0 lỗi và 0 timeout. Hai main truy về commit `8d5bbb93c97fb69821c23876981a921c4ec6b6f7`. Ở lần E1 chính, lớp bọc `/usr/bin/time -l` báo thiếu quyền đọc `kern.clockrate` sau khi runner đã ghi đủ kết quả và manifest. CSV, thống kê và hash đã được xác minh độc lập.

Trên clean clone của commit số liệu `b75ee23c195404827d041fc65b41deeecd9e9d8a`, cả bốn lượt export notebook (hai notebook × hai chế độ) hoàn thành. Hai CSV đối chiếu và `report/tables.tex` tái tạo khớp từng byte. LaTeX build được PDF 7 trang. Hai link Molab công khai trả HTTP 200 và phần preview nhúng có ảnh cùng số liệu 600/600 và 90/90.

## Ước lượng điểm cấp nhóm ở trạng thái hiện tại

Ước lượng thận trọng **61–73/100** nếu chỉ xét bằng chứng hiện có. A1 khoảng 8–9/10, A2 17–19/20 và A3 12–14/15 dựa trên bản nháp Methods và phần phê bình. B1 khoảng 11–14/20 vì E2 đang thiếu, B2 khoảng 12–14/15 với E1/E3 đã đo, B3 chưa có số liệu nên tính 0/15 và chất lượng khoảng 1–3/5 vì báo cáo nhóm và W&B public đang chờ. Đây là ước lượng theo rubric, điểm chính thức do giảng viên quyết định. Sau khi có E2/E4, cần kiểm định mức bám sát paper, chất lượng trên dữ liệu mới và page count trước khi đánh giá lại.
