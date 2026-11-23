# Tái lập trên clean clone

## Môi trường

Chọn Python 3.12 để khớp môi trường đo. Bộ tests đã chạy với Python 3.9.25 và 3.12.15. Venv và file W&B sinh ra ở máy cục bộ nằm ngoài Git. Có thể chạy tests, đo số liệu, thực thi notebook và đọc báo cáo hoàn toàn cục bộ.

```bash
git clone --branch feat/tv1-algorithms-benchmarks https://github.com/hungstupid/hcmus-flpa-clustering.git
cd hcmus-flpa-clustering
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q
```

Trên môi trường hạn chế ghi cache, đặt `XDG_CACHE_HOME`, `XDG_CONFIG_HOME` và `MPLCONFIGDIR` tới thư mục tạm có quyền ghi. `marimo export html` khởi chạy kernel local, có thể cần cấp quyền loopback.

## Smoke và benchmark

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python scripts/run_experiment.py configs/e1_runtime.json --profile smoke --output results/local/e1-smoke
python scripts/run_experiment.py configs/e3_ablation.json --profile smoke --output results/local/e3-smoke
python scripts/verify_results.py results/local/e1-smoke results/local/e3-smoke
python scripts/verify_results.py results/e1 results/e3 results/pilot/e1 results/pilot/e3 results/author/e1
```

Mỗi đường dẫn đầu ra cho runner cần là thư mục mới. Đổi profile sang `pilot` hoặc `main` và đổi đường dẫn đầu ra để tăng kích thước. Benchmark chính E1 có 600 lượt trên ba họ, gồm graph 100.000 đỉnh. E3 có 90 lượt và nhẹ hơn. Hash graph, metrics và bộ đếm cần tái lập trong cùng môi trường. Wall time và SD thay đổi theo máy, nhiệt và tải nền. Cùng thuật toán, dùng một seed cho nhiều graph giữ cặp so sánh giữa họ. Để ước lượng phương sai theo từng nguồn ngẫu nhiên cần thiết kế lồng nhau.

### Đối chiếu C của tác giả

Dùng CMake, compiler C/C++, Bison và Flex. Các tuỳ chọn của bản legacy tắt GraphML và GLPK vì bài này chỉ gọi label propagation. Cho phép warning từ header C cũ trên compiler mới. Mã nguồn tác giả ở ngoài repo đồ án.

```bash
reference_dir=$(mktemp -d)
git clone --branch flpa https://github.com/vtraag/igraph.git "$reference_dir/igraph"
git -C "$reference_dir/igraph" checkout b89649877e15a2a4d3ca199c9190fe3dc181c643
cmake -S "$reference_dir/igraph" -B "$reference_dir/build" \
  -DCMAKE_BUILD_TYPE=Release -DIGRAPH_WARNINGS_AS_ERRORS=OFF -DBUILD_TESTING=OFF \
  -DIGRAPH_GLPK_SUPPORT=OFF -DIGRAPH_GRAPHML_SUPPORT=OFF -DIGRAPH_USE_INTERNAL_GMP=ON \
  -DIGRAPH_USE_INTERNAL_ARPACK=ON -DIGRAPH_USE_INTERNAL_BLAS=ON -DIGRAPH_USE_INTERNAL_LAPACK=ON
cmake --build "$reference_dir/build" --parallel 4
cmake --install "$reference_dir/build" --prefix "$reference_dir/prefix"
cmake -S scripts/author_reference -B "$reference_dir/cli" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$reference_dir/prefix"
cmake --build "$reference_dir/cli"
python scripts/run_experiment.py configs/e1_runtime.json --profile reference \
  --author-reference "$reference_dir/cli/flpa-author-reference" --output results/local/author-e1
python scripts/verify_results.py results/local/author-e1
python scripts/compare_results.py --reference results/local/author-e1 --output results/local/comparison
```

Các dòng đối chiếu dùng những topology và seed đầu cùng E1. Wrapper kiểm phiên bản git nhúng trong thư viện. Phương pháp đọc Figure 1 nằm trong [data/README.md](../data/README.md).

## Notebook marimo và Molab

```bash
marimo edit notebooks/01_runtime.py
marimo edit notebooks/03_ablation.py
```

Trong editor dùng **Run All**. `main` đọc raw của lần đo đã lưu và tái tổng hợp bảng và hình. Chọn `smoke` để chạy thuật toán từ đầu trên cấu hình nhỏ. Kiểm tra chạy tất cả ô ở terminal qua export HTML. `FLPA_NOTEBOOK_MODE=smoke` buộc chạy toàn bộ ô theo chế độ smoke.

```bash
marimo export html notebooks/01_runtime.py -o /tmp/flpa-e1.html
marimo export html notebooks/03_ablation.py -o /tmp/flpa-e3.html
FLPA_NOTEBOOK_MODE=smoke marimo export html notebooks/01_runtime.py -o /tmp/flpa-e1-smoke.html
FLPA_NOTEBOOK_MODE=smoke marimo export html notebooks/03_ablation.py -o /tmp/flpa-e3-smoke.html
```

Molab có thể xem notebook qua GitHub mirror công khai. Snapshot trong `notebooks/__marimo__/session/` lưu output đã chạy để hiển thị ngay trong preview. Khi cập nhật số liệu, dùng marimo 0.25.2 trong môi trường xuất riêng để chạy `marimo export session` rồi cập nhật snapshot và kiểm link bằng phiên không đăng nhập. Đọc [tài liệu Molab](https://docs.marimo.io/guides/publishing/github/).

## Weights & Biases

Chạy lại bước log từ CSV đã kiểm mà không cần đo lại. Mỗi bundle tạo một W&B run và bảng `trials`, `summary`, `paired`. Dòng `trials` giữ tên, seed, backend, runtime, metrics, trạng thái và fingerprint. `manifest.json` mang cấu hình và SHA source. Artifact chứa CSV và hình. Lưu record `tracking.json` cho ID và chế độ. `url` là `null` khi offline.

```bash
mkdir -p wandb/cache wandb/data
export WANDB_DIR=. WANDB_CACHE_DIR=./wandb/cache WANDB_DATA_DIR=./wandb/data
python -m flpa.tracking results/e1 --mode offline
python -m flpa.tracking results/e3 --mode offline
```

Để công bố, đăng nhập `wandb login` trên máy có các thư mục offline, đặt `WANDB_ENTITY` thành tài khoản hoặc team được phép ghi, rồi sync vào cùng project. Giữ cache/data artifact tại đường dẫn đã dùng khi log. Dùng tuỳ chọn `--id` để giữ ID run nếu đồng bộ từng thư mục. W&B API key chỉ nhập vào CLI.

```bash
wandb login
wandb sync --entity "$WANDB_ENTITY" --project hcmus-flpa-clustering wandb/offline-run-*
```

Trong project W&B, mở phần Settings và đặt visibility Public. Kiểm tra project và các run bằng một phiên chưa đăng nhập rồi cập nhật bảng README. Có thể tái log online từ CSV bằng `python -m flpa.tracking results/e1 --mode online` nếu máy sync thiếu file offline. [Tài liệu CLI W&B](https://github.com/wandb/wandb)

## Build báo cáo IEEE

```bash
python scripts/compare_results.py
python scripts/report_tables.py
cd report
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
cp build/main.pdf Report-draft.pdf
```

TeX Live cần `IEEEtran`, `vntex`, `algpseudocode`, TikZ và BibTeX. Bản nháp chứa số liệu của TV1 và vị trí tích hợp phần thực nghiệm TV2. Báo cáo nhóm cần hoàn thiện E2 và E4 và kiểm lại yêu cầu 10–15 trang nội dung trước khi đặt `Report.pdf` ở root.
