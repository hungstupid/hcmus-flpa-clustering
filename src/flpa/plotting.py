"""Recreate publication figures directly from the experiment summaries."""

from pathlib import Path

from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter


STYLES = {
    "lpa": ("LPA", "#bd412d", "o"),
    "retention_lpa": ("Retention-LPA", "#73539a", "s"),
    "flpa": ("FLPA FIFO", "#156e73", "D"),
    "leiden": ("Leiden", "#493d35", "^"),
    "flpa_lifo": ("FLPA LIFO", "#bd412d", "s"),
    "flpa_all": ("FIFO, mọi láng giềng", "#73539a", "^"),
}


def _series(ax, data, x, metric, algorithm, *, per_node=False):
    name, color, marker = STYLES[algorithm]
    data = data[data.algorithm == algorithm].sort_values(x)
    denominator = data.n_nodes if per_node else 1
    ax.errorbar(data[x], data[f"{metric}_mean"] / denominator,
                yerr=data[f"{metric}_sd"].fillna(0) / denominator,
                label=name, color=color, marker=marker, capsize=3, linewidth=1.4)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)


def runtime_figure(summary, *, metric="runtime_seconds") -> Figure:
    """Plot mean and sample SD against graph size for each synthetic family."""
    fig = Figure(figsize=(10, 3.5), layout="constrained")
    ylabel = "Thời gian (giây)" if metric == "runtime_seconds" else "Lượt xử lý / đỉnh"
    for ax, (dataset, name) in zip(fig.subplots(1, 3), [("er", "ER"), ("ba", "BA"), ("sbm", "SBM, μ = 0,6")]):
        values = summary[summary.dataset == dataset]
        for algorithm in STYLES:
            if algorithm in values.algorithm.values and values.loc[values.algorithm == algorithm, f"{metric}_mean"].notna().any():
                _series(ax, values, "n_nodes", metric, algorithm, per_node=metric == "node_visits")
        ax.set(xscale="log", title=name, xlabel="Số đỉnh", ylim=(0, None))
        ax.set_xticks(sorted(values.n_nodes.unique()))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda n, _: f"{n / 1000:g}k"))
        if dataset == "er":
            ax.set_ylabel(ylabel)
            ax.legend(loc="upper left", frameon=False, fontsize=8)
    return fig


def ablation_figure(summary) -> Figure:
    """Plot time, work per vertex, and NMI for index-paired ablation variants."""
    fig = Figure(figsize=(10, 3.5), layout="constrained")
    for ax, (metric, ylabel) in zip(fig.subplots(1, 3), [
        ("runtime_seconds", "Thời gian (giây)"), ("node_visits", "Lượt xử lý / đỉnh"), ("nmi", "NMI"),
    ]):
        for algorithm in ("flpa", "flpa_lifo", "flpa_all"):
            _series(ax, summary, "mixing_mu", metric, algorithm, per_node=metric == "node_visits")
        ax.set(xlabel="Mixing μ", ylabel=ylabel)
        ax.set_xticks(sorted(summary.mixing_mu.unique()))
        if metric == "runtime_seconds":
            ax.legend(frameon=False, fontsize=8)
    return fig


def save_figures(experiment_type: str, summary, destination: Path) -> None:
    """Write separate vector PDF and PNG copies of applicable figures."""
    destination.mkdir(parents=True, exist_ok=True)
    if experiment_type == "runtime":
        figures = {"runtime": runtime_figure(summary)}
        if summary.node_visits_mean.notna().any():
            figures["work"] = runtime_figure(summary, metric="node_visits")
    elif experiment_type == "ablation":
        figures = {"ablation": ablation_figure(summary)}
    else:
        raise ValueError(f"unknown figure type: {experiment_type}")
    for name, figure in figures.items():
        figure.savefig(destination / f"{name}.pdf")
        figure.savefig(destination / f"{name}.png", dpi=180)
