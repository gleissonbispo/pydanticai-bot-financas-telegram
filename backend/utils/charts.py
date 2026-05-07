from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

matplotlib.use("Agg")  # backend sem display (headless para Docker/Raspberry)

CATEGORY_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
]


def generate_expense_chart(categories: list[dict]) -> bytes:
    """
    Gera gráfico combinado (pizza + barras horizontais) a partir do resumo de categorias.

    Args:
        categories: lista de dicts com chaves 'category', 'total', 'count'

    Returns:
        PNG em bytes pronto para enviar via Telegram reply_photo()
    """
    if not categories:
        return _generate_empty_chart()

    labels = [item["category"].capitalize() for item in categories]
    values = [item["total"] for item in categories]
    counts = [item["count"] for item in categories]
    total = sum(values)
    colors = CATEGORY_COLORS[: len(labels)]

    fig, (ax_pie, ax_bar) = plt.subplots(
        1, 2, figsize=(14, 7), facecolor="#1a1a2e"
    )
    fig.patch.set_facecolor("#1a1a2e")

    # ── Gráfico de pizza ───────────────────────────────────────────────────
    wedges, texts, autotexts = ax_pie.pie(
        values,
        labels=None,
        autopct="%1.1f%%",
        colors=colors,
        startangle=140,
        pctdistance=0.75,
        wedgeprops={"linewidth": 2, "edgecolor": "#1a1a2e"},
    )
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(9)
        autotext.set_fontweight("bold")

    ax_pie.set_facecolor("#1a1a2e")
    ax_pie.set_title(
        f"Gastos do Mês\nTotal: R$ {total:,.2f}",
        color="white", fontsize=13, fontweight="bold", pad=15,
    )

    legend_patches = [
        mpatches.Patch(color=colors[i], label=f"{labels[i]} ({counts[i]}x)")
        for i in range(len(labels))
    ]
    ax_pie.legend(
        handles=legend_patches,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        fontsize=8,
        framealpha=0.2,
        labelcolor="white",
    )

    # ── Gráfico de barras horizontais ──────────────────────────────────────
    sorted_pairs = sorted(zip(values, labels, colors), reverse=True)
    sorted_values, sorted_labels, sorted_colors = zip(*sorted_pairs)

    bars = ax_bar.barh(
        sorted_labels, sorted_values, color=sorted_colors,
        edgecolor="#1a1a2e", linewidth=1.5, height=0.6,
    )
    ax_bar.set_facecolor("#1a1a2e")
    ax_bar.set_title(
        "Por Categoria (R$)",
        color="white", fontsize=13, fontweight="bold", pad=15,
    )
    ax_bar.tick_params(colors="white", labelsize=9)
    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)
    ax_bar.spines["bottom"].set_color("#444")
    ax_bar.spines["left"].set_color("#444")
    ax_bar.xaxis.label.set_color("white")

    for bar, value in zip(bars, sorted_values):
        ax_bar.text(
            bar.get_width() + total * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"R$ {value:,.2f}",
            va="center", color="white", fontsize=8, fontweight="bold",
        )

    ax_bar.set_xlim(right=max(sorted_values) * 1.25)

    plt.tight_layout(pad=2.5)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _generate_empty_chart() -> bytes:
    """Gráfico placeholder quando não há dados."""
    fig, ax = plt.subplots(figsize=(8, 4), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.text(
        0.5, 0.5, "Nenhum gasto registrado\nneste mês",
        ha="center", va="center", color="white",
        fontsize=14, transform=ax.transAxes,
    )
    ax.axis("off")

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
