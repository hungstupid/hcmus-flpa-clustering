# /// script
# requires-python = ">=3.9,<3.13"
# dependencies = [
#   "marimo==0.13.15", "numpy==2.0.2", "scipy==1.13.1", "scikit-learn==1.6.1",
#   "networkx==3.2.1", "pandas==2.2.3", "matplotlib==3.9.4",
# ]
# ///

import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium", app_title="FLPA · E3 ablation")


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
    from flpa.plotting import ablation_figure

    return ablation_figure, iter_runs, load_plan, mo, os, paired_summary, pd, root, summarize


@app.cell
def _(mo):
    mo.md(r"""
    # E3 · Hàng đợi và quy tắc đưa lại đỉnh

    Hàng đợi FIFO có lợi gì so với LIFO? Việc lọc láng giềng cùng nhãn có giảm
    số lượt xử lý và duy trì chất lượng trong thực tế không?

    SBM có 100 khối giống nhau về kích thước, bậc kỳ vọng 10, nhiều mức mixing μ.
    Cả ba biến thể dùng cùng seed và cùng biểu diễn. So sánh FIFO và LIFO giữ
    nguyên thứ tự chèn, chỉ đổi đầu lấy đỉnh. Biến thể `flpa_all` giữ FIFO và
    đưa lại mọi láng giềng chưa xếp hàng sau mỗi thay đổi nhãn.
    [Algorithm 3 trong bài báo](https://lovro.fri.uni-lj.si/papers/flpa.pdf#page=9)
    """)
    return


@app.cell
def _(mo, os, root):
    bundle = root / "results" / "e3"
    default = os.environ.get("FLPA_NOTEBOOK_MODE", "main" if (bundle / "raw.csv").is_file() else "smoke")
    mode = mo.ui.dropdown(["main", "smoke"], value=default, label="Chế độ")
    mo.vstack([mode, mo.md("`main` đọc 90 lượt đã đo. `smoke` chạy ba biến thể trên một đồ thị 1.000 đỉnh.")])
    return bundle, mode


@app.cell
def _(load_plan, mo, mode, pd, root):
    plan = load_plan(root / "configs" / "e3_ablation.json", mode.value)
    mo.vstack([
        mo.md(f"## Cấu hình\n\n**{len(plan['cases'])}** case, **{len(plan['seed_pairs'])}** cặp seed/case, "
              f"**{plan['timeout_seconds']} giây/lượt**. So sánh kết quả theo đúng từng cặp seed."),
        mo.ui.table(pd.DataFrame(plan["cases"]), selection=None),
    ])
    return (plan,)


@app.cell
def _(bundle, iter_runs, paired_summary, pd, plan, summarize):
    if plan["profile"] == "main":
        raw = pd.read_csv(bundle / "raw.csv")
    else:
        raw = pd.DataFrame(iter_runs(plan))
    summary = summarize(raw)
    pairs = paired_summary(raw)
    return pairs, raw, summary


@app.cell
def _(ablation_figure, mo, raw, summary):
    columns = ["mixing_mu", "algorithm", "n_ok", "completion_rate", "n_final_maximal", "runtime_seconds_mean",
               "node_visits_mean", "label_updates_mean", "nmi_mean", "ari_mean", "acc_mean", "n_predicted_clusters_mean"]
    mo.vstack([
        mo.md(f"## Công việc, chất lượng và hội tụ\n\n**{(raw.status == 'ok').sum()}/{len(raw)}** lượt hoàn thành. "
              "Mỗi nhãn cuối của đỉnh có láng giềng được kiểm tra lại ngoài timer."),
        ablation_figure(summary),
        mo.ui.table(summary[columns].round(4), page_size=9, selection=None),
    ])
    return


@app.cell
def _(mo, pairs):
    mo.vstack([
        mo.md("## Chênh lệch ghép cặp so với FIFO\n\nTỷ lệ thời gian > 1 nghĩa là biến thể chạy lâu hơn FIFO. "
              "Delta dương ở `node_visits` nghĩa là biến thể xử lý nhiều đỉnh hơn."),
        mo.ui.table(pairs[["mixing_mu", "algorithm", "n_paired_ok", "speedup_mean", "speedup_sd",
                           "node_visits_delta_mean", "nmi_delta_mean", "ari_delta_mean"]].round(4),
                    page_size=6, selection=None),
    ])
    return


@app.cell
def _(mo, pairs):
    hard = pairs[pairs.mixing_mu == pairs.mixing_mu.max()]
    details = "\n    ".join(
        f"- `{row.algorithm}` có tỷ lệ thời gian **{row.speedup_mean:.2f}×** và ΔNMI **{row.nmi_delta_mean:+.3f}**."
        for row in hard.itertuples()
    )
    mo.md(f"""
    ## Diễn giải và hạn chế

    Đối chiếu từng biến thể với FIFO ở mức mixing cao nhất trong bảng.

    {details}

    LIFO ưu tiên đỉnh vừa được đưa lại, cho phép nhãn mới lan sâu trước khi
    một số đỉnh trong hoán vị ban đầu được xử lý. FIFO cho đỉnh chờ lâu hơn đi
    trước. Cả hai thứ tự có thể hội tụ đến phân hoạch maximal khác nhau.
    Biến thể enqueue-all cũng có thể thay đổi quỹ đạo khi lấy mẫu lại giữa các nhãn hoà.
    Các con số phụ thuộc vào cấu hình SBM và mười cặp seed. NMI cao cần được
    đọc cùng ARI, ACC và số cụm để đánh giá hiện tượng phân mảnh hoặc gộp cụm.

    ## Tái lập

    ```bash
    python scripts/run_experiment.py configs/e3_ablation.json --profile smoke --output results/local/e3-smoke
    ```

    Đổi `smoke` thành `main` để tái đo tất cả μ. Kiểm tra CSV và SHA-256
    bằng `python scripts/verify_results.py results/local/e3-smoke`.
    """)
    return


if __name__ == "__main__":
    app.run()
