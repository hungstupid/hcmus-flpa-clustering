#!/usr/bin/env python3
"""Render the report's numeric tables from the verified CSV bundles."""

from pathlib import Path

import pandas as pd


NAMES = {
    "flpa": "FLPA FIFO", "lpa": "LPA", "retention_lpa": "Retention-LPA", "leiden": "Leiden",
    "flpa_all": "FIFO toàn bộ", "flpa_lifo": "FLPA LIFO",
}


def number(value, digits):
    """Round displayed values without changing the source CSV precision."""
    return "--" if pd.isna(value) else f"${value:.{digits}f}$"


def mean_sd(mean, sd, digits=3):
    """Render a mean with its sample standard deviation."""
    if pd.isna(mean):
        return "--"
    if pd.isna(sd):
        return number(mean, digits)
    return f"${mean:.{digits}f}\\pm{sd:.{digits}f}$"


def table(name, spec, headings, rows):
    """Return a LaTeX command wrapping a formatted table."""
    body = "\n".join(" & ".join(row) + r" \\" for row in [headings, *rows])
    header, lines = body.split("\n", 1)
    return (
        f"\\newcommand{{\\{name}}}{{%\n\\begin{{tabular}}{{{spec}}}\n\\toprule\n"
        f"{header}\n\\midrule\n{lines}\n\\bottomrule\n\\end{{tabular}}}}\n"
    )


def main():
    root = Path(__file__).resolve().parents[1]
    e1 = pd.read_csv(root / "results/e1/summary.csv")
    e3 = pd.read_csv(root / "results/e3/summary.csv")
    figure1 = pd.read_csv(root / "results/comparison/e1_figure1.csv")
    author = pd.read_csv(root / "results/comparison/e1_author_same_graph.csv")
    e1_rows = [
        [row.dataset.upper(), NAMES[row.algorithm], mean_sd(row.runtime_seconds_mean, row.runtime_seconds_sd),
         number(row.node_visits_mean / row.n_nodes, 1), number(row.n_predicted_clusters_mean, 1)]
        for row in e1[e1.n_nodes == e1.n_nodes.max()].itertuples()
    ]
    e3_rows = [
        [number(row.mixing_mu, 2), NAMES[row.algorithm],
         mean_sd(row.runtime_seconds_mean, row.runtime_seconds_sd), number(row.node_visits_mean, 0),
         number(row.label_updates_mean, 0), mean_sd(row.nmi_mean, row.nmi_sd),
         mean_sd(row.ari_mean, row.ari_sd), mean_sd(row.acc_mean, row.acc_sd),
         number(row.n_predicted_clusters_mean, 1)]
        for row in e3.itertuples()
    ]
    paper_rows = [
        [row.dataset.upper(), NAMES[row.algorithm], number(row.mean_seconds_approx, 2),
         mean_sd(row.runtime_seconds_mean, row.runtime_seconds_sd), number(row.relative_deviation_pct, 0)]
        for row in figure1[figure1.n_nodes == 50_000].itertuples()
    ]
    same_graph_rows = [
        [row.dataset.upper(), NAMES[row.algorithm], str(row.n_paired_ok),
         mean_sd(row.runtime_seconds_author_mean, row.runtime_seconds_author_sd),
         mean_sd(row.runtime_seconds_python_mean, row.runtime_seconds_python_sd),
         number(row.runtime_relative_deviation_pct, 0)]
        for row in author[author.n_nodes == 100_000].itertuples()
    ]
    latex = "% Sinh bởi scripts/report_tables.py từ CSV.\n"
    latex += table("EoneTable", "llrrr", ["Họ", "Thuật toán", "Giây", "Lượt/đỉnh", "Cụm"], e1_rows)
    latex += table("EthreeTable", "rlrrrrrrr", ["$\\mu$", "Biến thể", "Giây", "Lượt", "Đổi nhãn",
                   "NMI", "ARI", "ACC", "Cụm"], e3_rows)
    latex += table("PaperTable", "llrrr", ["Họ", "Thuật toán", "Paper (s)", "Python (s)", r"$\Delta$ (\%)"], paper_rows)
    latex += table("AuthorTable", "llrrrr", ["Họ", "Thuật toán", "Cặp", "C (s)", "Python (s)", r"$\Delta$ (\%)"], same_graph_rows)
    (root / "report/tables.tex").write_text(latex, encoding="utf-8")


if __name__ == "__main__":
    main()
