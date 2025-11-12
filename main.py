import pandas as pd
import numpy as np
import os
import importlib
import argparse
from acc_matrix import acc

# 只用 find_important_sig 來挑 top-n，避免 per-subindex 門檻搜尋
import find_important_sig as my_module
importlib.reload(my_module)
from find_important_sig import find_important_sig  # 不匯入 calculate_index, make_sheet


# ======== 指標計算（避免重複呼叫 acc，用 NumPy 直接算） ========
def _metric_from_preds(y_pred: np.ndarray, y_true: np.ndarray, mea: str):
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    eps = 1e-12
    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)

    def F(beta, p, r):
        return ((1 + beta**2) * p * r) / ((beta**2) * p + r + eps)

    fscore = F(0.5, precision, recall)
    num_signal = int(np.sum(y_pred))

    if mea == "precision":
        return precision, num_signal
    if mea == "recall":
        return recall, num_signal
    # 預設 fscore
    return fscore, num_signal


def subindex_precision(sub_series: pd.Series, ms: pd.DataFrame, direction: str, sub_min_votes: int, mea: str):
    """
    給每個 subindex 一個固定規則的精準分數：
    - 二值化規則：subindex >= sub_min_votes 視為 1，否則 0
    - 回傳 (score, num_signal)
    """
    y_true = (ms["波段低點區間" if direction == "buy" else "波段高點區間"].to_numpy()).astype(int)
    y_pred = (sub_series.to_numpy() >= int(sub_min_votes)).astype(int)
    return _metric_from_preds(y_pred, y_true, mea)


# ======== 只對 composite 做一次門檻最佳化 ========
def optimize_threshold_on_composite(
    df: pd.DataFrame,
    ms: pd.DataFrame,
    mea: str,
    direction: str,
    min_share: float = 0.05,
    min_count: int | None = None,
):
    """
    只對 composite_index 做一次門檻最佳化，加入最小訊號量限制：
    - min_share：最小觸發占比
    - min_count：最小觸發筆數（若提供，與 min_share 取較大者）
    """
    comp = df["composite_index"].to_numpy()
    y_true = (ms["波段低點區間" if direction == "buy" else "波段高點區間"].to_numpy()).astype(int)

    n = len(comp)
    # 至少要達到的觸發數量
    min_required = int(np.ceil(n * (min_share if min_share is not None else 0)))
    if min_count is not None:
        min_required = max(min_required, int(min_count))

    thresholds = np.unique(comp)
    thresholds.sort()

    best_thres = None
    best_precision = -np.inf
    best_num_signal = None

    for thres in thresholds:
        y_pred = (comp > thres).astype(int)  # 與你原規則一致：>
        num_signal = int(y_pred.sum())
        if num_signal < min_required:
            continue

        score, _ = _metric_from_preds(y_pred, y_true, mea)
        precision = score if mea == "precision" else (_metric_from_preds(y_pred, y_true, "precision")[0])

        # 以 precision 為主，同分偏好多觸發（更穩定）
        if (precision > best_precision) or (
            precision == best_precision and (best_num_signal is None or num_signal > best_num_signal)
        ):
            best_thres = thres
            best_precision = precision
            best_num_signal = num_signal

    # 若完全找不到符合 min_required 的門檻，降級為「剛好達標」的保底策略
    if best_thres is None:
        order = np.argsort(comp)
        kth_index = max(0, n - min_required) if n > 0 else 0
        guard_thres = comp[order][kth_index] if n > 0 else 0
        y_pred = (comp > guard_thres).astype(int)
        num_signal = int(y_pred.sum())
        precision = _metric_from_preds(y_pred, y_true, "precision")[0]

        best_thres = guard_thres
        best_precision = precision
        best_num_signal = num_signal

    return best_thres, best_num_signal, best_precision


# ======== 依你需求輸出 sub_<cat>.csv 的形狀 ========
def write_subindex_csv(
    cat_df: pd.DataFrame,
    ms: pd.DataFrame,
    cat: str,
    direction: str,
    mea: str,
    top_n: int,
    show_days: int,
    sub_min_votes: int,
    out_dir: str,
):
    """
    產出你要的 subindex CSV 格式：
    第一欄為列名（訊號名或 subindex_{cat}），其後依序為 <mea>, num_signal, 最近 N 天（由新到舊）。
    """
    # 用 acc() 計算各欄位績效，挑出 top-n
    acc_cat = acc(cat_df, ms, direction=direction)
    top_series = find_important_sig(acc_cat, measurement=mea, top_n=top_n)
    top_cols = [c for c in top_series.index if c in cat_df.columns]
    if not top_cols:
        return None, (0.0, 0)

    # 真值
    y_true = (ms["波段低點區間" if direction == "buy" else "波段高點區間"].to_numpy()).astype(int)

    # 逐欄計算單一訊號的分數（fscore/precision/recall）與 num_signal（整段期間）
    per_signal_score = {}
    per_signal_count = {}
    for col in top_cols:
        y_pred = cat_df[col].to_numpy().astype(int)
        score, num_sig = _metric_from_preds(y_pred, y_true, mea)
        per_signal_score[col] = score
        per_signal_count[col] = num_sig

    # 建 subindex（票數加總，不做最佳化）
    subindex_series = cat_df[top_cols].sum(axis=1)
    sub_y_pred = (subindex_series.to_numpy() >= int(sub_min_votes)).astype(int)
    sub_score, sub_num = _metric_from_preds(sub_y_pred, y_true, mea)

    # 最近 N 天欄位（新→舊）
    lastN_idx = cat_df.index.sort_values(ascending=False)[:show_days]
    date_cols = [str(d) for d in lastN_idx]

    # 組裝表格：每個 top 訊號一列
    out_rows = []
    for name in top_cols:
        row_vals = [int(v) for v in cat_df.loc[lastN_idx, name].to_numpy()]
        out_rows.append([name, per_signal_score[name], per_signal_count[name]] + row_vals)

    # 最後加上 subindex_列（這列的最後 N 天是「票數和（未二值化）」）
    sub_vals = [int(v) for v in subindex_series.loc[lastN_idx].to_numpy()]
    out_rows.append([f"subindex_{cat}", sub_score, sub_num] + sub_vals)

    df_out = pd.DataFrame(out_rows, columns=["", mea, "num_signal"] + date_cols)
    os.makedirs(out_dir, exist_ok=True)
    df_out.to_csv(os.path.join(out_dir, f"sub_{cat}.csv"), index=False)

    return subindex_series, (sub_score, sub_num)


# ======== 主流程 ========
def run_main(
    direction: str,
    mea: str,
    top_n: int = 10,
    show_days: int = 5,
    sub_min_votes: int = 1,
    comp_min_share: float = 0.05,
    comp_min_count: int | None = None,
    market: str = "TW",                 # ★ 新增：市場代碼，讀 data/{market}/...
    out_dir: str | None = None          # ★ 新增：輸出資料夾，預設 {market}_{direction}_data
):
    print(f"\n=== Running {direction.upper()} mode, measurement = {mea}, market = {market} ===")

    # === 讀取資料（改成依市場路徑）===
    base = f"data/{market}"
    signals = pd.read_csv(f"{base}/sn.csv", parse_dates=["日期"], index_col=["日期"])
    sn_dir  = pd.read_csv(f"{base}/sn_dir.csv", index_col=["indicator_id"])
    ms      = pd.read_csv(f"{base}/ms.csv", parse_dates=["日期"], index_col=["日期"])

    # === 輸出資料夾（依市場 + 方向）===
    if out_dir is None:
        out_dir = f"{market}_{direction}_data"
    os.makedirs(out_dir, exist_ok=True)

    # === 動態抓所有類別 ===
    categories = sn_dir.loc["訊號類型"].dropna().unique().tolist()
    print(f"偵測到訊號類別: {categories}")

    # 每個類別：挑 top-n → subindex = 逐列相加（不做門檻最佳化），並輸出你要的 CSV 形狀
    subindex_matrix = pd.DataFrame(index=signals.index)

    for cat in categories:
        print(f"\n[處理類別] {cat}")
        try:
            cat_cols = sn_dir.loc[:, sn_dir.loc["訊號類型"] == cat].loc["name"].tolist()
        except Exception:
            print(f"⚠️ 類別 {cat} 無法在 sn_dir 正確索引，略過。")
            continue

        present_cols = [c for c in cat_cols if c in signals.columns]
        if not present_cols:
            print(f"⚠️ 類別 {cat} 沒有任何欄位存在於 sn.csv，略過。")
            continue

        cat_df = signals[present_cols].copy()

        # 產出 sub_<cat>.csv（含每個訊號的 <mea> & num_signal、最後一列 subindex_<cat>）
        result = write_subindex_csv(
            cat_df=cat_df,
            ms=ms,
            cat=cat,
            direction=direction,
            mea=mea,
            top_n=top_n,
            show_days=show_days,
            sub_min_votes=sub_min_votes,
            out_dir=out_dir,  # ★ 路徑改這裡
        )
        if result is None:
            print(f"⚠️ 類別 {cat} 找不到可用的 top-n 訊號，略過。")
            continue

        sub_series, _ = result
        subindex_matrix[f"subindex_{cat}"] = sub_series

    # === 整合：composite = 各 subindex 直接加總 ===
    if subindex_matrix.shape[1] == 0:
        raise RuntimeError("沒有任何子指數可供合成，請檢查 sn_dir 與 sn.csv 欄位是否對應。")

    subindex_matrix["composite_index"] = subindex_matrix.sum(axis=1)

    # === 只對 composite 做一次門檻最佳化（含最小訊號量限制） ===
    best_thres, best_num_signal, best_precision = optimize_threshold_on_composite(
        subindex_matrix, ms, mea, direction, min_share=comp_min_share, min_count=comp_min_count
    )

    # === 主表（最近幾天 + 指標） ===
    main_sheet = subindex_matrix.sort_index(ascending=False).iloc[:show_days].T
    main_sheet[[f"{mea}", "num_signal"]] = np.nan
    main_sheet.loc["composite_index", [f"{mea}", "num_signal"]] = [best_precision, best_num_signal]

    cols = main_sheet.columns.tolist()
    new_order = cols[-2:] + cols[:-2]
    main_sheet = main_sheet[new_order]
    main_sheet.to_csv(os.path.join(out_dir, "main_chart.csv"), index=True)  # ★ 改路徑

    # === 視覺化（沿用你的 visualize） ===
    import visualize
    importlib.reload(visualize)
    from visualize import plot_highzones_with_price, plot_lowzones_with_price

    if direction == "buy":
        fig = plot_lowzones_with_price(
            ms,
            price_col="收盤價",
            scores_df=subindex_matrix,
            title=f"收盤價 × 波段低點 × 指標 ({direction.upper()} · {market})",
            composite_threshold=best_thres + 1,   # 顯示提示
            threshold_marker="^",
            threshold_marker_color="purple",
            threshold_label=f"門檻觸發(Composite>{best_thres})",
        )
    else:
        fig = plot_highzones_with_price(
            ms,
            price_col="收盤價",
            scores_df=subindex_matrix,
            title=f"收盤價 × 波段高點 × 指標 ({direction.upper()} · {market})",
            composite_threshold=best_thres + 1,
            threshold_marker="v",
            threshold_marker_color="purple",
            threshold_label=f"門檻觸發(Composite>{best_thres})",
        )

    fig.savefig(os.path.join(out_dir, "plot.png"), dpi=180, bbox_inches="tight")  # ★ 改路徑
    print(f"✅ {direction.upper()} 完成：已輸出 {out_dir}/ 下的 sub_*.csv、main_chart.csv、plot.png")


def main(mea, top_n, show_days, sub_min_votes, comp_min_share, comp_min_count, market: str = "TW"):
    # ★ 依市場自動決定 out_dir：{market}_{direction}_data
    run_main(
        direction="buy",
        mea=mea,
        top_n=top_n,
        show_days=show_days,
        sub_min_votes=sub_min_votes,
        comp_min_share=comp_min_share,
        comp_min_count=comp_min_count,
        market=market,
        out_dir=f"{market}_buy_data",
    )
    run_main(
        direction="sell",
        mea=mea,
        top_n=top_n,
        show_days=show_days,
        sub_min_votes=sub_min_votes,
        comp_min_share=comp_min_share,
        comp_min_count=comp_min_count,
        market=market,
        out_dir=f"{market}_sell_data",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="通用版（subindex 不最佳化但保留 precision），composite 僅最佳化一次")
    parser.add_argument("mea", type=str, help="指定 measurement，例如 fscore, precision, recall")
    parser.add_argument("--top_n", type=int, default=10, help="每個類別挑選的 top-n 訊號數")
    parser.add_argument("--show_days", type=int, default=5, help="子表與主表顯示最近天數（新→舊）")
    parser.add_argument(
        "--sub_min_votes", type=int, default=1, help="subindex 二值化的票數門檻（不做搜尋，用於計 subindex 的 <mea> & num_signal）"
    )
    parser.add_argument(
        "--comp_min_share", type=float, default=0.05, help="composite 門檻搜尋的最小觸發占比（與 comp_min_count 取較大者）"
    )
    parser.add_argument(
        "--comp_min_count", type=int, default=None, help="composite 門檻搜尋的最小觸發筆數（與 comp_min_share 取較大者）"
    )
    parser.add_argument("--market", type=str, default="TW", help="市場代碼（例如 TW、US 等）")  # ★ 新增
    args = parser.parse_args()

    main(
        args.mea,
        args.top_n,
        args.show_days,
        args.sub_min_votes,
        args.comp_min_share,
        args.comp_min_count,
        market=args.market,  # ★ 傳入
    )
