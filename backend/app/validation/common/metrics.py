"""Classification, regression, and ranking metrics with explicit sample counts (n)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
)


@dataclass
class ClassificationMetricsResult:
    n: int
    n_positive: int
    n_negative: int
    auroc: Optional[float]
    auprc: Optional[float]
    accuracy: float
    balanced_accuracy: float
    precision: float
    recall: float
    f1: float
    specificity: float
    mcc: float
    confusion_matrix: List[List[int]]
    threshold: float = 0.5
    notes: str = ""


def _safe_auroc(y_true: np.ndarray, y_score: np.ndarray) -> Optional[float]:
    y_true = np.asarray(y_true).astype(int)
    if len(np.unique(y_true)) < 2:
        return None
    try:
        return float(roc_auc_score(y_true, y_score))
    except Exception:
        return None


def _safe_auprc(y_true: np.ndarray, y_score: np.ndarray) -> Optional[float]:
    y_true = np.asarray(y_true).astype(int)
    if y_true.sum() == 0 or y_true.sum() == len(y_true):
        return None
    try:
        return float(average_precision_score(y_true, y_score))
    except Exception:
        return None


def classification_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    *,
    threshold: float = 0.5,
) -> ClassificationMetricsResult:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=np.float64)
    n = int(len(y_true))
    n_pos = int(y_true.sum())
    n_neg = n - n_pos
    y_pred = (y_score >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    return ClassificationMetricsResult(
        n=n,
        n_positive=n_pos,
        n_negative=n_neg,
        auroc=_safe_auroc(y_true, y_score),
        auprc=_safe_auprc(y_true, y_score),
        accuracy=float(accuracy_score(y_true, y_pred)),
        balanced_accuracy=float(balanced_accuracy_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        specificity=spec,
        mcc=float(matthews_corrcoef(y_true, y_pred)) if n > 0 else 0.0,
        confusion_matrix=cm.tolist(),
        threshold=threshold,
    )


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray, mask: Optional[np.ndarray] = None) -> Dict[str, Any]:
    if mask is not None:
        y_true = np.asarray(y_true)[mask]
        y_pred = np.asarray(y_pred)[mask]
    else:
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
    valid = np.isfinite(y_true) & np.isfinite(y_pred)
    yt = y_true[valid].astype(np.float64)
    yp = y_pred[valid].astype(np.float64)
    n = int(len(yt))
    if n < 2:
        return {"n": n, "pearson_r": None, "spearman_r": None, "mae": None, "rmse": None, "r2": None}
    pearson_r, _ = stats.pearsonr(yt, yp)
    spearman_r, _ = stats.spearmanr(yt, yp)
    mae = float(np.mean(np.abs(yt - yp)))
    rmse = float(np.sqrt(np.mean((yt - yp) ** 2)))
    ss_res = float(np.sum((yt - yp) ** 2))
    ss_tot = float(np.sum((yt - np.mean(yt)) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 1e-12 else None
    return {
        "n": n,
        "pearson_r": float(pearson_r),
        "spearman_r": float(spearman_r),
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }


def brier_score_binary(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    y_true = np.asarray(y_true).astype(np.float64)
    y_prob = np.asarray(y_prob, dtype=np.float64)
    return float(np.mean((y_prob - y_true) ** 2))


def calibration_ece_mce(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    *,
    n_bins: int = 10,
) -> Tuple[float, float, List[Dict[str, float]]]:
    """Expected calibration error (ECE), max calibration error (MCE), bin-wise data for reliability diagram."""
    y_true = np.asarray(y_true).astype(np.float64)
    y_prob = np.asarray(y_prob, dtype=np.float64)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    diagram: List[Dict[str, float]] = []
    n = len(y_true)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        m = (y_prob >= lo) & (y_prob < hi if i < n_bins - 1 else y_prob <= hi)
        cnt = int(m.sum())
        if cnt == 0:
            diagram.append({"bin_lo": float(lo), "bin_hi": float(hi), "n": 0, "pred_mean": float("nan"), "obs_freq": float("nan")})
            continue
        conf = float(y_prob[m].mean())
        acc = float(y_true[m].mean())
        gap = abs(conf - acc)
        ece += (cnt / max(n, 1)) * gap
        mce = max(mce, gap)
        diagram.append({"bin_lo": float(lo), "bin_hi": float(hi), "n": cnt, "pred_mean": conf, "obs_freq": acc})
    return float(ece), float(mce), diagram


def roc_enrichment(y_true: np.ndarray, y_score: np.ndarray, top_fracs: Tuple[float, ...] = (0.01, 0.05, 0.10)) -> Dict[str, Any]:
    """Fraction of positives captured in top-k% by score (descending)."""
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=np.float64)
    n = len(y_true)
    pos_total = max(int(y_true.sum()), 1)
    order = np.argsort(-y_score)
    out: Dict[str, Any] = {"n": n, "n_positive": int(y_true.sum())}
    for frac in top_fracs:
        k = max(1, int(np.ceil(n * frac)))
        top = y_true[order[:k]]
        out[f"enrichment_top_{int(frac * 100)}pct"] = float(top.sum() / pos_total)
        out[f"precision_at_top_{int(frac * 100)}pct"] = float(top.sum() / k)
    return out


def precision_recall_at_k(y_true: np.ndarray, y_score: np.ndarray, k_list: Tuple[int, ...] = (5, 10, 20)) -> Dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=np.float64)
    order = np.argsort(-y_score)
    out: Dict[str, float] = {}
    n = len(y_true)
    for k in k_list:
        kk = min(k, n)
        if kk < 1:
            continue
        top = y_true[order[:kk]]
        out[f"precision@{k}"] = float(top.sum() / kk)
        out[f"recall@{k}"] = float(top.sum() / max(int(y_true.sum()), 1))
    return out


def ndcg_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int = 10) -> float:
    """Binary relevance nDCG@k."""
    y_true = np.asarray(y_true).astype(float)
    y_score = np.asarray(y_score, dtype=np.float64)
    order = np.argsort(-y_score)[:k]
    rel = y_true[order]
    dcg = np.sum(rel / np.log2(np.arange(2, len(rel) + 2)))
    ideal = np.sort(y_true)[::-1][:k]
    idcg = np.sum(ideal / np.log2(np.arange(2, len(ideal) + 2)))
    return float(dcg / idcg) if idcg > 1e-12 else 0.0


def roc_curve_dict(y_true: np.ndarray, y_score: np.ndarray) -> Optional[Dict[str, List[float]]]:
    y_true = np.asarray(y_true).astype(int)
    if len(np.unique(y_true)) < 2:
        return None
    fpr, tpr, thr = roc_curve(y_true, y_score)
    return {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "thresholds": thr.tolist()}


def pr_curve_dict(y_true: np.ndarray, y_score: np.ndarray) -> Optional[Dict[str, List[float]]]:
    y_true = np.asarray(y_true).astype(int)
    if y_true.sum() == 0:
        return None
    prec, rec, thr = precision_recall_curve(y_true, y_score)
    return {"precision": prec.tolist(), "recall": rec.tolist(), "thresholds": thr.tolist()}
