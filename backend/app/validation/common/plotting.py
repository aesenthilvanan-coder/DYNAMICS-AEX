"""Publication-style matplotlib plots (sample counts in titles)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_roc_curve(
    fpr: List[float],
    tpr: List[float],
    title: str,
    out_path: Path,
    n_pos: int,
    n_neg: int,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, lw=2, label="Model")
    plt.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title(f"{title}\n(n_pos={n_pos}, n_neg={n_neg})")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_pr_curve(
    prec: List[float],
    rec: List[float],
    title: str,
    out_path: Path,
    n_pos: int,
    n: int,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 5))
    plt.plot(rec, prec, lw=2)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"{title}\n(n={n}, n_pos={n_pos})")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_calibration(
    diagram: List[Dict],
    title: str,
    out_path: Path,
    n: int,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    confs, freqs, ns = [], [], []
    for b in diagram:
        if b.get("n", 0) == 0:
            continue
        confs.append(b["pred_mean"])
        freqs.append(b["obs_freq"])
        ns.append(b["n"])
    plt.figure(figsize=(5, 5))
    plt.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    if confs:
        plt.plot(confs, freqs, "o-", lw=2, markersize=8)
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Observed frequency")
    plt.title(f"{title}\n(n={n})")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_bar(
    labels: List[str],
    values: List[float],
    title: str,
    ylabel: str,
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(max(8, len(labels) * 0.35), 4))
    x = np.arange(len(labels))
    plt.bar(x, values, color="steelblue", edgecolor="black", linewidth=0.5)
    plt.xticks(x, labels, rotation=45, ha="right", fontsize=8)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_histogram_two(
    a: np.ndarray,
    b: np.ndarray,
    label_a: str,
    label_b: str,
    title: str,
    out_path: Path,
    xlabel: str = "Value",
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.hist(a, bins=30, alpha=0.6, label=f"{label_a} (n={len(a)})", density=True)
    plt.hist(b, bins=30, alpha=0.6, label=f"{label_b} (n={len(b)})", density=True)
    plt.xlabel(xlabel)
    plt.ylabel("Density")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
