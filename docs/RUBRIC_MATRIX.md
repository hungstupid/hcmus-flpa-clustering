# Ma trận rubric HCMUS

Đã đối chiếu toàn bộ trang đề bài và rubric. Các phần 45 + 50 + 5 áp dụng cho cả nhóm. TV1 là Track B, theo xác nhận của người dùng. Tham chiếu chuẩn là [rubric chính thức HCMUS](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/clustering-paper/).

| Tiêu chí | Điểm | Yêu cầu cụ thể | Owner | File hoặc thực nghiệm chứng minh | Trạng thái |
|---|---:|---|---|---|---|
| A1 · Bối cảnh và đóng góp | 10 | Ví dụ ứng dụng, phân tích ≥2 tiền nhiệm, phân biệt đóng góp kỹ thuật, lý thuyết và thực nghiệm | TV1, rà soát nhóm | `report/sections/introduction.tex` | PASS cho bản TV1 |
| A2 · Phương pháp | 20 | Ký hiệu, pipeline, quy tắc đa số, mã giả, bất biến maximality, thời gian và không gian | TV1 | `report/sections/methods.tex`, `src/flpa/algorithms.py`, `tests/test_algorithms.py` | PASS cho bản TV1 |
| A3 · Phê bình | 15 | ≥3 điểm mạnh, ≥2 hạn chế, giả định và ≥2 hướng mở | TV1 và TV2 | `report/sections/critical_analysis.tex`, thảo luận thực nghiệm | PASS cho văn bản TV1, cần thảo luận E2/E4 khi tích hợp |
| B1 · Cài đặt và tái hiện | 20 | Tự cài từ paper, tái hiện ≥2 thí nghiệm cốt lõi, đối chiếu số liệu, ≥3 metrics phù hợp | TV1 E1, TV2 E2 | `src/flpa/`, `results/e1/`, `results/author/e1/`, `results/comparison/` | PASS E1, BLOCKED B1 của nhóm chờ E2 |
| B2 · Sai lệch và ablation | 15 | So sánh với paper và bản gốc nếu công khai. Giải thích sai lệch. Ablation có kiểm soát | TV1 E1/E3, TV2 E2 | `results/e3/`, `results/comparison/`, `notebooks/03_ablation.py`, báo cáo | PASS E1/E3, còn phân tích sai lệch E2 |
| B3 · Dataset mới | 15 | Dữ liệu khác paper, phân tích nhóm và hạn chế, NMI/ARI/ACC | TV2 | E4 email-Eu-core và báo cáo tương ứng | BLOCKED chờ TV2 |
| Chất lượng kết quả và sản phẩm | 5 | W&B project công khai, marimo Run All, Molab công khai, IEEE 10–15 trang, PDF paper, README và tái lập | Chung. TV1 phụ trách E1/E3, TV2 phụ trách E2/E4 | `README.md`, `notebooks/`, `report/Report-draft.pdf`, `paper/paper.pdf`, `docs/REPRODUCIBILITY.md`, manifest | PASS cục bộ cho E1/E3. BLOCKED W&B public và bản nộp nhóm |
| **Tổng** | **100** | **Mục tiêu cấp nhóm** | **TV1 + TV2** | [Audit](RUBRIC_AUDIT.md) | Bản nháp Track B |
