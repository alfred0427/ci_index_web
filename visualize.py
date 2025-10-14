import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates




def plot_lowzones_with_price(ms: pd.DataFrame,
                             price_col: str = None,
                             low_zone_col: str = "波段低點區間",
                             low_point_col: str = "波段低點",  # 保留參數，但不再使用畫標記
                             title: str = "波段低點區間",
                             scores_df: pd.DataFrame | None = None,
                             # 新增：門檻相關參數（同高點版）
                             composite_threshold: float | None = None,
                             threshold_line_kwargs: dict | None = None,
                             threshold_marker: str = '^',     # 正三角形
                             threshold_marker_size: int = 80,
                             threshold_marker_color: str = 'purple',
                             threshold_label: str = '門檻觸發(Composite>Threshold)'):
    # 日期處理
    
    plt.rcParams['font.sans-serif'] = ['Taipei Sans TC Beta', 'Microsoft JhengHei', 'SimHei']  
    plt.rcParams['axes.unicode_minus'] = False  # 正常顯示負號
    if not isinstance(ms.index, pd.DatetimeIndex):
        for c in ["日期","Date","date","交易日","datetime"]:
            if c in ms.columns:
                ms = ms.copy()
                ms[c] = pd.to_datetime(ms[c])
                ms = ms.set_index(c).sort_index()
                break
        else:
            raise ValueError("請先把 ms 的 index 設成 DatetimeIndex，或提供『日期/Date』欄位。")

    if scores_df is not None:
        if not isinstance(scores_df.index, pd.DatetimeIndex):
            for c in ["日期","Date","date","交易日","datetime"]:
                if c in scores_df.columns:
                    scores_df = scores_df.copy()
                    scores_df[c] = pd.to_datetime(scores_df[c])
                    scores_df = scores_df.set_index(c).sort_index()
                    break
            else:
                raise ValueError("scores_df 需要 DatetimeIndex 或包含『日期/Date』欄位。")
        common_idx = ms.index.intersection(scores_df.index)
        if len(common_idx) == 0:
            raise ValueError("ms 與 scores_df 沒有重疊日期。")
        ms = ms.loc[common_idx]
        scores_df = scores_df.loc[common_idx]

    # 價格欄
    if price_col is None:
        for c in ["收盤價_調整後","盤價","收盤價","Close","Adj Close","close"]:
            if c in ms.columns:
                price_col = c
                break
        if price_col is None:
            raise ValueError("找不到價格欄，請用 price_col 指定，例如 '收盤價_調整後'。")

    fig, ax = plt.subplots(figsize=(14, 6))

    # 左軸：收盤價
    px = ms[price_col].astype(float)
    ax.plot(px.index, px.values, linewidth=1.6, label="收盤價", color="black")
    ax.set_ylabel('收盤價', fontsize=12)

    # 右軸：只畫「波段低點區間」陰影（綠色）
    ax2 = ax.twinx()
    ax2.set_ylabel("分數 / 區間")

    def draw_zones(mask, color):
        mask = mask.reindex(ms.index).fillna(0).astype(int)
        on = False; start = None
        for i, v in enumerate(mask.values):
            if v == 1 and not on:
                on = True; start = mask.index[i]
            elif v == 0 and on:
                on = False; end = mask.index[i-1]
                ax2.axvspan(start, end, color=color, alpha=0.15)
        if on:
            ax2.axvspan(start, mask.index[-1], color=color, alpha=0.15)

    if low_zone_col in ms:
        draw_zones(ms[low_zone_col], "green")

    # 右軸：scores_df 填色 + 門檻線與觸發三角形
    if scores_df is not None and scores_df.shape[1] >= 1:
        composite_col = scores_df.columns[-1]                # 最後一欄為 composite
        subindex_cols = [c for c in scores_df.columns if c != composite_col]

        # 取不含紅色的 tab10 顏色
        tab10 = list(plt.cm.tab10.colors)
        safe_colors = [c for i, c in enumerate(tab10) if i != 3]  # 紅色通常在 index=3

        # subindex 填色
        for i, col in enumerate(subindex_cols):
            ax2.fill_between(scores_df.index, 0, scores_df[col],
                             alpha=0.75,
                             color=safe_colors[i % len(safe_colors)],
                             label=col)

        # composite 填色
        ax2.fill_between(scores_df.index, 0, scores_df[composite_col],
                         alpha=0.5,
                         color=safe_colors[len(subindex_cols) % len(safe_colors)],
                         label=composite_col)

        # 右軸 y 限：scores_df 最大值 × 3
        max_val = float(scores_df.max().max())
        ax2.set_ylim(0, max_val * 3 if max_val > 0 else 1)

        # 門檻線 + 觸發三角形（畫在價格軸上）
        if composite_threshold is not None:
            # 門檻線（右軸）
            _kw = dict(color='gray', linestyle='--', linewidth=1.5, label=f'Threshold={composite_threshold}')
            if threshold_line_kwargs:
                _kw.update(threshold_line_kwargs)
            ax2.axhline(y=composite_threshold, **_kw)

            # 觸發日期（Composite > Threshold）
            thr_mask = (scores_df[composite_col] > composite_threshold)
            if thr_mask.any():
                idx_thr = scores_df.index[thr_mask]
                ax.scatter(idx_thr, px.reindex(idx_thr),
                           marker=threshold_marker,              # 正三角形
                           s=threshold_marker_size,
                           color=threshold_marker_color,
                           label=threshold_label)

    # 外觀設定
    ax.set_title(title, fontsize=20)
    ax.set_xlabel('日期', fontsize=15)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=1, interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax.get_xticklabels(), rotation=90)

    ax.legend(loc="upper left", frameon=False)
    ax2.legend(loc="upper right", frameon=False)
    plt.tight_layout()
    return fig





def plot_highzones_with_price(ms: pd.DataFrame,
                              price_col: str = None,
                              high_zone_col: str = "波段高點區間",
                              title: str = "波段高點區間",
                              scores_df: pd.DataFrame | None = None,
                              # 門檻相關參數
                              composite_threshold: float | None = None,
                              threshold_line_kwargs: dict | None = None,
                              threshold_marker: str = 'v',   # ★ 改成倒三角
                              threshold_marker_size: int = 80,
                              threshold_marker_color: str = 'purple',
                              threshold_label: str = '門檻觸發(Composite>Threshold)'):



    plt.rcParams['font.sans-serif'] = ['Taipei Sans TC Beta', 'Microsoft JhengHei', 'SimHei']  
    plt.rcParams['axes.unicode_minus'] = False  # 正常顯示負號
   # 日期處理
    if not isinstance(ms.index, pd.DatetimeIndex):
        for c in ["日期","Date","date","交易日","datetime"]:
            if c in ms.columns:
                ms = ms.copy()
                ms[c] = pd.to_datetime(ms[c])
                ms = ms.set_index(c).sort_index()
                break
        else:
            raise ValueError("請先把 ms 的 index 設成 DatetimeIndex，或提供『日期/Date』欄位。")

    if scores_df is not None:
        if not isinstance(scores_df.index, pd.DatetimeIndex):
            for c in ["日期","Date","date","交易日","datetime"]:
                if c in scores_df.columns:
                    scores_df = scores_df.copy()
                    scores_df[c] = pd.to_datetime(scores_df[c])
                    scores_df = scores_df.set_index(c).sort_index()
                    break
            else:
                raise ValueError("scores_df 需要 DatetimeIndex 或包含『日期/Date』欄位。")
        common_idx = ms.index.intersection(scores_df.index)
        if len(common_idx) == 0:
            raise ValueError("ms 與 scores_df 沒有重疊日期。")
        ms = ms.loc[common_idx]
        scores_df = scores_df.loc[common_idx]

    # 價格欄
    if price_col is None:
        for c in ["收盤價_調整後","盤價","收盤價","Close","Adj Close","close"]:
            if c in ms.columns:
                price_col = c
                break
        if price_col is None:
            raise ValueError("找不到價格欄，請用 price_col 指定，例如 '收盤價_調整後'。")

    fig, ax = plt.subplots(figsize=(14, 6))

    # 左軸：收盤價
    px = ms[price_col].astype(float)
    ax.plot(px.index, px.values, linewidth=1.6, label="收盤價", color="black")

    ax.set_ylabel('收盤價', fontsize=12)

    # 右軸：波段高點區間 & scores
    ax2 = ax.twinx()
    ax2.set_ylabel("分數 / 區間")

    def draw_zones(mask, color):
        mask = mask.reindex(ms.index).fillna(0).astype(int)
        on = False; start = None
        for i, v in enumerate(mask.values):
            if v == 1 and not on:
                on = True; start = mask.index[i]
            elif v == 0 and on:
                on = False; end = mask.index[i-1]
                ax2.axvspan(start, end, color=color, alpha=0.15)
        if on:
            ax2.axvspan(start, mask.index[-1], color=color, alpha=0.15)

    if high_zone_col in ms:
        draw_zones(ms[high_zone_col], "red")

    composite_col = None
    if scores_df is not None and scores_df.shape[1] >= 1:
        composite_col = scores_df.columns[-1]  # 最後一欄作為 composite
        subindex_cols = [c for c in scores_df.columns if c != composite_col]

        # 避開紅色
        all_colors = list(plt.cm.tab10.colors)
        safe_colors = [c for i, c in enumerate(all_colors) if i != 3]

        # 畫 subindex 填色（無框線）
        for i, col in enumerate(subindex_cols):
            ax2.fill_between(scores_df.index, 0, scores_df[col],
                             alpha=0.75,
                             color=safe_colors[i % len(safe_colors)],
                             label=col)

        # 畫 composite 填色（無框線）
        ax2.fill_between(scores_df.index, 0, scores_df[composite_col],
                         alpha=0.5,
                         color=safe_colors[len(subindex_cols) % len(safe_colors)],
                         label=composite_col)

        # 設定右軸 y 限
        max_val = scores_df.max().max()
        ax2.set_ylim(0, max_val * 3)

        # 門檻線 + 觸發三角形
        if composite_threshold is not None:
            # 門檻線
            _kw = dict(color='gray', linestyle='--', linewidth=1.5, label=f'Threshold={composite_threshold}')
            if threshold_line_kwargs:
                _kw.update(threshold_line_kwargs)
            ax2.axhline(y=composite_threshold, **_kw)

            # 觸發日期（Composite > Threshold）
            thr_mask = (scores_df[composite_col] > composite_threshold)
            if thr_mask.any():
                idx_thr = scores_df.index[thr_mask]
                ax.scatter(idx_thr, px.reindex(idx_thr),
                           marker=threshold_marker,
                           s=threshold_marker_size,
                           color=threshold_marker_color,
                           label=threshold_label)

    # 外觀設定
    ax.set_title(title, fontsize=20)
    ax.set_xlabel('日期', fontsize=15)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=1, interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax.get_xticklabels(), rotation=90)

    ax.legend(loc="upper left", frameon=False)
    ax2.legend(loc="upper right", frameon=False)
    plt.tight_layout()
    return fig
