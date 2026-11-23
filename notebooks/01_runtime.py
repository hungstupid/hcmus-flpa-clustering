# /// script
# requires-python = ">=3.9,<3.13"
# dependencies = [
#   "marimo==0.13.15", "numpy==2.0.2", "scipy==1.13.1", "scikit-learn==1.6.1",
#   "networkx==3.2.1", "pandas==2.2.3", "matplotlib==3.9.4", "igraph==0.11.9", "leidenalg==0.10.2",
# ]
# ///

import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium", app_title="FLPA · E1 runtime")


@app.cell
def _():
    import os
    import sys
    from pathlib import Path

    import marimo as mo
    import pandas as pd

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    from flpa.experiments import iter_runs, load_plan, paired_summary, summarize
    from flpa.plotting import runtime_figure

    return iter_runs, load_plan, mo, os, paired_summary, pd, root, runtime_figure, summarize


@app.cell
def _(mo):
    mo.md(r"""
    # E1 · Thời gian lan truyền nhãn trên đồ thị synthetic

    FLPA tiết kiệm bao nhiêu công việc khi số đỉnh tăng? Tiết kiệm công việc có
    chuyển thành ít thời gian hơn Retention-LPA trên mọi cấu trúc không?

    ER chọn mỗi cạnh với xác suất như nhau. BA sinh các hub bằng đính kèm ưu tiên.
    SBM có 100 khối cùng kích thước và μ = 0,6, tức 60% cạnh kỳ vọng nối khác khối.
    Bậc trung bình đích là 10. Mỗi cặp seed dùng đúng cùng tập đỉnh và cạnh
    cho LPA, Retention-LPA, FLPA FIFO và Leiden modularity.
    [Giao thức](https://github.com/hungstupid/hcmus-flpa-clustering/tree/feat/tv1-algorithms-benchmarks/docs)
    · [Traag và Šubelj, Figure 1](https://lovro.fri.uni-lj.si/papers/flpa.pdf#page=5)
    """)
    return


@app.cell
def _(mo, os, root):
    bundle = root / "results" / "e1"
    default = os.environ.get("FLPA_NOTEBOOK_MODE", "main" if (bundle / "raw.csv").is_file() else "smoke")
    mode = mo.ui.dropdown(["main", "smoke"], value=default, label="Chế độ")
    mo.vstack([mode, mo.md("`main` đọc 600 lượt đã đo. `smoke` sinh lại ba đồ thị 1.000 đỉnh và chạy thật bốn thuật toán.")])
    return bundle, mode


@app.cell
def _(load_plan, mo, mode, pd, root):
    plan = load_plan(root / "configs" / "e1_runtime.json", mode.value)
    mo.vstack([
        mo.md(f"## Cấu hình\n\n**{len(plan['cases'])}** case, **{len(plan['seed_pairs'])}** cặp seed/case. "
              f"Giới hạn **{plan['timeout_seconds']} giây/lượt**. Thời gian tạo đồ thị và chấm điểm được đo ngoài timer thuật toán."),
        mo.ui.table(pd.DataFrame(plan["cases"]), page_size=5, selection=None),
    ])
    return (plan,)


@app.cell
def _(bundle, iter_runs, paired_summary, pd, plan, summarize):
    if plan["profile"] == "main":
        raw = pd.read_csv(bundle / "raw.csv")
    else:
        raw = pd.DataFrame(iter_runs(plan))
    summary = summarize(raw)
    ratios = paired_summary(raw)
    return ratios, raw, summary


@app.cell
def _(mo, raw, summary):
    columns = ["dataset", "n_nodes", "algorithm", "n_ok", "n_timeout", "n_other_failure",
               "runtime_seconds_mean", "runtime_seconds_sd", "node_visits_mean", "label_updates_mean",
               "n_predicted_clusters_mean"]
    mo.vstack([
        mo.md(f"## Kết quả đã đo\n\n**{(raw.status == 'ok').sum()}/{len(raw)}** lượt hoàn thành. "
              "Khoảng biến thiên trong hình là ± một SD mẫu. Ô trống thể hiện chỉ số chưa áp dụng hoặc thiếu mẫu."),
        mo.ui.table(summary[columns].round(5), page_size=12, selection=None),
    ])
    return


@app.cell
def _(mo, runtime_figure, summary):
    mo.vstack([runtime_figure(summary), runtime_figure(summary, metric="node_visits")])
    return


@app.cell
def _(mo, ratios):
    mo.vstack([
        mo.md("## Tỷ lệ ghép cặp\n\nMỗi tỷ lệ chia thời gian của phương pháp so sánh cho FLPA FIFO "
              "trên cùng đồ thị và seed. Giá trị lớn hơn 1 nghiêng về FIFO."),
        mo.ui.table(ratios[["dataset", "n_nodes", "algorithm", "n_paired_ok", "speedup_mean", "speedup_sd",
                            "ratio_of_paired_means"]].round(4), page_size=9, selection=None),
    ])
    return


@app.cell
def _(mo, pd, plan, root):
    comparison = root / "results" / "comparison"
    paper_path = comparison / "e1_figure1.csv"
    author_path = comparison / "e1_author_same_graph.csv"
    if plan["profile"] == "main" and paper_path.exists() and author_path.exists():
        paper = pd.read_csv(paper_path)
        same_graph = pd.read_csv(author_path)
        view = mo.vstack([
            mo.md("## Đối chiếu với Figure 1 và mã C gốc\n\nĐiểm paper được đọc từ hình và làm tròn 0,05 giây. "
                  "Đối chiếu C ghép đúng cạnh và seed số. Mỗi backend có RNG riêng."),
            mo.ui.table(paper.round(4), page_size=6, selection=None),
            mo.ui.table(same_graph[["dataset", "n_nodes", "algorithm", "n_paired_ok", "runtime_seconds_author_mean",
                                    "runtime_seconds_python_mean", "runtime_relative_deviation_pct"]].round(4),
                        page_size=6, selection=None),
        ])
    else:
        view = mo.md("Chọn `main` để xem bảng đối chiếu Figure 1 và mã C gốc trên các cấu hình lớn.")
    view
    return


@app.cell
def _(mo, ratios, summary):
    largest = int(summary.n_nodes.max())
    top = ratios[(ratios.n_nodes == largest) & (ratios.algorithm == "lpa")]
    numbers = ", ".join(f"{row.dataset.upper()} **{row.speedup_mean:.2f}×**" for row in top.itertuples())
    mo.md(f"""
    ## Diễn giải và hạn chế

    Ở *n* = {largest:,}, trung bình tỷ lệ LPA/FLPA là {numbers}.
    Đọc thêm số cụm để nhận ra khi Retention-LPA dừng sớm ở một phân hoạch mịn.
    Mỗi lượt kiểm tra maximality của LPA cũng phải đọc láng giềng. Một lượt
    đưa lại đỉnh vào hàng đợi của FLPA có chi phí riêng, thể hiện qua chênh lệch
    giữa lượt đỉnh và thời gian.

    Figure 1 dùng igraph C, 2.000 lần lặp và thêm các họ đồ thị khác. Các con số
    Python chịu ảnh hưởng của chi phí dict, RNG, thứ tự cạnh và phần cứng. Leiden
    có backend C/C++ và tối ưu mục tiêu khác. Kết quả ER và BA không có nhãn thật.

    ## Tái lập

    Sau khi cài `requirements.txt`, chạy phần smoke ngay trong notebook hoặc
    dùng lệnh sau. Đổi `smoke` thành `main` để chạy lại toàn bộ. Giữ kết quả mới
    trong thư mục riêng và kiểm tra bằng `scripts/verify_results.py`.

    ```bash
    python scripts/run_experiment.py configs/e1_runtime.json --profile smoke --output results/local/e1-smoke
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
