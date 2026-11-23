# FLPA — Phát hiện cộng đồng bằng lan truyền nhãn nhanh

Đồ án Khai thác dữ liệu, Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM. Nhóm tái hiện nghiên cứu của Vincent A. Traag và Lovro Šubelj về phát hiện cộng đồng trên đồ thị. [Đề bài và rubric HCMUS](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/clustering-paper/)

Bài báo *Large network community detection by fast label propagation*, *Scientific Reports*, 13, 2701 (2023), DOI `10.1038/s41598-023-29610-z`. Repo lưu bản PDF nguyên vẹn từ trang của đồng tác giả. Giấy phép CC BY 4.0, © các tác giả 2023. [PDF trong repo](paper/paper.pdf) · [Nguồn PDF](https://lovro.fri.uni-lj.si/papers/flpa.pdf) · [Giấy phép](https://creativecommons.org/licenses/by/4.0/)

## Phân công

| Thành viên | MSSV | Vai trò | Phần việc |
|---|---|---|---|
| Nguyễn Đức Hưng | 24127174 | **TV1 · Track B** | Tự cài LPA, Retention-LPA và FLPA. Kiểm thử hội tụ, đo E1, làm ablation E3 và viết phương pháp. |
| Trần Thiên Phúc | 24127506 | **TV2 · Track A** | Tái hiện Figure 4 qua E2, kiểm tra dữ liệu email-Eu-core ở E4 và viết phân tích chất lượng. |

Bản này bàn giao phần TV1. Giao diện `Graph` và `detect_communities` có thể dùng cho các experiment TV2. [Phân công và tích hợp](docs/CONTRIBUTIONS.md)

## Chạy nhanh

```bash
git clone --branch feat/tv1-algorithms-benchmarks https://github.com/hungstupid/hcmus-flpa-clustering.git
cd hcmus-flpa-clustering
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/run_experiment.py configs/e1_runtime.json --profile smoke --output results/local/e1-smoke
python scripts/run_experiment.py configs/e3_ablation.json --profile smoke --output results/local/e3-smoke
python scripts/verify_results.py results/local/e1-smoke results/local/e3-smoke
```

Dùng Python 3.12 để khớp môi trường benchmark. `--profile main` chạy cấu hình đủ 10 cặp seed mỗi case. [Giao thức và định nghĩa metric](docs/EXPERIMENT_PROTOCOL.md) · [Lệnh tái lập, bản C và report](docs/REPRODUCIBILITY.md)

## Kết quả và notebook

| Thực nghiệm | Phạm vi | Bằng chứng |
|---|---|---|
| E1 | ER, BA, SBM, 5 kích thước đến 100.000 đỉnh và 4 thuật toán | [Raw CSV](results/e1/raw.csv) · [Summary](results/e1/summary.csv) · [Speedup ghép cặp](results/e1/paired.csv) · [Thời gian](results/e1/figures/runtime.pdf) · [Lượt đỉnh](results/e1/figures/work.pdf) |
| E3 | SBM 5.000 đỉnh với μ ∈ {0,30, 0,45, 0,60}, FIFO, LIFO và FIFO enqueue-all | [Raw CSV](results/e3/raw.csv) · [Summary](results/e3/summary.csv) · [Chênh lệch ghép cặp](results/e3/paired.csv) · [Biểu đồ](results/e3/figures/ablation.pdf) |
| Đối chiếu E1 | Đọc xấp xỉ Figure 1 và chạy nhánh C gốc trên cùng các đồ thị | [Bảng Figure 1](results/comparison/e1_figure1.csv) · [Bảng C/Python](results/comparison/e1_author_same_graph.csv) · [Raw C](results/author/e1/raw.csv) |

E1 có 600/600 lượt hoàn thành. Ở 100.000 đỉnh, trung bình tỷ lệ LPA/FLPA trên cùng cặp seed lần lượt là 1,58× trên ER, 1,30× trên BA và 1,40× trên SBM. Retention-LPA chạy nhanh hơn ở kích thước này, đồng thời tạo khoảng 27.000–31.000 cụm.

E3 có 90/90 lượt hoàn thành và qua maximality. Ở μ = 0,60, LIFO chạy lâu gấp 4,82 lần FIFO theo trung bình tỷ lệ ghép cặp và kết thúc với một cụm trong cả 10 lượt. Bỏ lọc láng giềng làm tăng lượt xử lý ở cả ba mức μ.

Notebook chế độ `main` tái tổng hợp từ CSV. Chế độ `smoke` chạy lại thuật toán trên đồ thị nhỏ. W&B lưu bảng trials, summary và artifact trong run offline. Công bố W&B cần đăng nhập và sync vào entity của nhóm. [Hướng dẫn sync](docs/REPRODUCIBILITY.md#weights--biases)

| Experiment | Notebook | Molab công khai | W&B URL |
|---|---|---|---|
| E1 | [01_runtime.py](notebooks/01_runtime.py) | [Preview E1 với kết quả](https://molab.marimo.io/github/hungstupid/hcmus-flpa-clustering/blob/b75ee23c195404827d041fc65b41deeecd9e9d8a/notebooks/01_runtime.py) | BLOCKED · [record offline](results/e1/tracking.json) |
| E3 | [03_ablation.py](notebooks/03_ablation.py) | [Preview E3 với kết quả](https://molab.marimo.io/github/hungstupid/hcmus-flpa-clustering/blob/9fd916a4a284bed17618f0006064a49b8a157447/notebooks/03_ablation.py) | BLOCKED · [record offline](results/e3/tracking.json) |

Project W&B dự kiến `hcmus-flpa-clustering`. Năm run gồm hai main, hai pilot và một lần đối chiếu C đã được ghi offline. Link project public chờ thông tin entity và xác thực W&B.

## Báo cáo và nghiệm thu

- [Bản nháp IEEE tiếng Việt của TV1](report/Report-draft.pdf) dài 7 trang, có phương pháp và số liệu E1/E3. `Report.pdf` cấp nhóm chờ tích hợp E2/E4.
- [Ma trận 100 điểm](docs/RUBRIC_MATRIX.md) và [audit của từng tiêu chí](docs/RUBRIC_AUDIT.md).
- [Câu hỏi và đáp án vấn đáp](docs/VIVA_PREPARATION.md).
