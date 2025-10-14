import pandas as pd
import numpy as np
from acc_matrix import acc


def find_important_sig(acc,measurement="precision",top_n=5):
    """
    找出在 acc 績效矩陣中，指定 measurement（如 fscore）前 top_n 名的訊號名稱
    並回傳這些訊號名稱的列表
    """

    
    # 根據指定的 measurement 欄位排序，取前 top_n 名
    top_signals = acc[measurement].sort_values(ascending=False).head(top_n)
    
    # 回傳這些訊號的名稱列表
    return top_signals

def calculate_index(acc1,signals,ms,subness,measurement="precision",top_n=5):
    top_series = find_important_sig(acc1, measurement, top_n)
    important_name = list(top_series.index)

    # 與 signals 欄位取交集，避免 KeyError
    present_cols = [c for c in important_name if c in signals.columns]
    missing_cols = [c for c in important_name if c not in signals.columns]
    if len(present_cols) == 0:
        raise KeyError(
            f"Top-{top_n} signals by '{measurement}' 不在 signals.columns 中；缺少：{missing_cols}"
        )
    if len(missing_cols) > 0:
        print(f"[warn] {len(missing_cols)} 個 top signals 不在 signals.columns：{missing_cols[:5]} ...")

    df = signals[present_cols].copy()

    df[f"subindex_{subness}"] = df.sum(axis=1)
    
    
    def optimze_threshold(df, subness, ms,mea):
        best_thres = None
        best_precision = -np.inf
        n = len(df)
        min_required = int(np.ceil(n * 0.02))  # 4% 下限

        for thres in range(1, top_n):
            subindex_binary = (df[f"subindex_{subness}"] > thres).astype(int)
            acc_res = acc(pd.DataFrame(subindex_binary), ms=ms, direction="buy")
            precision = acc_res[mea].values[0]
            num_signal = acc_res["num_signal"].values[0]

            # 必須達到門檻才考慮
            if num_signal >= min_required:
                if best_thres is None or precision > best_precision:
                    best_thres = thres
                    best_precision = precision

        return best_thres

    best_thres = optimze_threshold(df,subness,ms,measurement)

    df[f"subindex_{subness}_binary"] = (df[f"subindex_{subness}"]>best_thres).astype(int)

    

    return df



def make_sheet(acc1,signals,subness,ms,direction,measurement ="precision",top_n =5,show_days = 5):
    df =  calculate_index(acc1,signals,ms,subness,measurement=measurement,top_n=top_n)
    df.sort_index(ascending=False,inplace=True)

    sheets = df.T
    sheets[[f"{measurement}","num_signal"]] = acc(df,ms,direction)[[measurement,"num_signal"]]
    cols = sheets.columns.tolist()

# 把最後兩個欄位移到最前面
    new_order = cols[-2:] + cols[:-2]

    sheets = sheets[new_order]
    sheets = sheets.iloc[:,:show_days+2]  # 只顯示前 show_days 天的資料加上兩個績效欄位
    return sheets






    
