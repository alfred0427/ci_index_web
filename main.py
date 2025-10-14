
from acc_matrix import acc
import pandas as pd
import numpy as np
import os

import find_important_sig as my_module
import importlib

importlib.reload(my_module)  

from find_important_sig import find_important_sig, calculate_index, make_sheet


def main(mea):
    top_nn = 10 # 你可以根據需要調整 top_n 的值
    print(f"Running main with measurement = {mea}")
    def main_buy(mea):
        # 讀取資料
        signals = pd.read_csv("data/sn.csv", parse_dates=["日期"], index_col=["日期"])
        sn_dir = pd.read_csv("data/sn_dir.csv", index_col=["indicator_id"])

        ms = pd.read_csv("data/ms.csv", parse_dates=["日期"], index_col=['日期'])

        sig = sn_dir.loc[:, (sn_dir.loc["訊號類型"] == "signal")].loc["name"]
        va = sn_dir.loc[:, (sn_dir.loc["訊號類型"] == "valuation")].loc["name"]
        st = sn_dir.loc[:, (sn_dir.loc["訊號類型"] == "status")].loc["name"]

        sig = signals[sig]
        va = signals[va]
        st = signals[st]

        acc1 = acc(sig, ms, direction="buy")
        acc2 = acc(va, ms, direction="buy")
        acc3 = acc(st, ms, direction="buy")

        # 產生各個子指標的績效表
        sub1 = make_sheet(acc1, sig, "signal", ms, direction="buy", measurement=mea, top_n=top_nn, show_days=5)
        sub2 = make_sheet(acc2, va, "valuation", ms, direction="buy", measurement=mea, top_n=top_nn, show_days=5)
        sub3 = make_sheet(acc3, st, "status", ms, direction="buy", measurement=mea, top_n=top_nn, show_days=5)

        # 確保資料夾存在
        os.makedirs("buy_data", exist_ok=True)
        sub1.to_csv("buy_data/sub1.csv")
        sub2.to_csv("buy_data/sub2.csv")
        sub3.to_csv("buy_data/sub3.csv")

        # 產生綜合指標
        signal = calculate_index(acc1, sig, ms, subness="signal", measurement=mea)
        value = calculate_index(acc2, va, ms, subness="valuation", measurement=mea)
        status = calculate_index(acc3, st, ms, subness="sta", measurement=mea)

        subindex_matrix = pd.DataFrame({
            signal.iloc[:, -2].name: signal.iloc[:, -2],
            value.iloc[:, -2].name: value.iloc[:, -2],
            status.iloc[:, -2].name: status.iloc[:, -2]
        })

        subindex_matrix["composite_index"] = subindex_matrix.sum(axis=1)
        measurement = mea

        def optimze_threshold(df, ms, mea):
            best_thres = None
            best_precision = -np.inf
            best_num_signal = None
            n = len(df)
            top_n = int(df["composite_index"].max() + 1)
            min_required = int(np.ceil(n * 0.02))  # 2% 下限

            for thres in range(1, top_n):
                subindex_binary = (df["composite_index"] > thres).astype(int)
                acc_res = acc(pd.DataFrame(subindex_binary), ms=ms, direction="buy")
                precision = acc_res[mea].values[0]
                num_signal = acc_res["num_signal"].values[0]

                if num_signal >= min_required:
                    if best_thres is None or precision > best_precision:
                        best_thres = thres
                        best_precision = precision
                        best_num_signal = num_signal

            return best_thres, best_num_signal, best_precision

        best_thres, best_num_signal, best_precision = optimze_threshold(subindex_matrix, ms=ms, mea=measurement)

        main_sheet = (subindex_matrix.sort_index(ascending=False).iloc[:5].T)
        # 建立兩欄，先填 NaN
        main_sheet[[f"{measurement}", "num_signal"]] = np.nan  

        # 只填 composite_index 這一列
        main_sheet.loc["composite_index", [f"{measurement}", "num_signal"]] = [best_precision, best_num_signal]

        cols = main_sheet.columns.tolist()
        new_order = cols[-2:] + cols[:-2]
        main_sheet = main_sheet[new_order]

        main_sheet.to_csv("buy_data/main_chart.csv")

        import visualize
        importlib.reload(visualize)  
        from visualize import plot_highzones_with_price, plot_lowzones_with_price

        fig = plot_lowzones_with_price(
            ms,
            price_col="收盤價",
            scores_df=subindex_matrix,
            title="收盤價 × 低點區間 × 分數指標",
            composite_threshold=best_thres + 1,
            threshold_marker='^',
            threshold_marker_color='purple',
            threshold_label='門檻觸發(Composite>2)'
        )



        fig.savefig("buy_data/plot.png")





    from acc_matrix import acc
    import pandas as pd
    import numpy as np
    import os

    import find_important_sig as my_module
    import importlib

    importlib.reload(my_module)

    from find_important_sig import find_important_sig, calculate_index, make_sheet


    def main_sell(mea):
        # 讀取資料
        signals = pd.read_csv("data/sn.csv", parse_dates=["日期"], index_col=["日期"])
        sn_dir = pd.read_csv("data/sn_dir.csv", index_col=["indicator_id"])

        ms = pd.read_csv("data/ms.csv", parse_dates=["日期"], index_col=['日期'])

        sig = sn_dir.loc[:, (sn_dir.loc["訊號類型"] == "signal")].loc["name"]
        va = sn_dir.loc[:, (sn_dir.loc["訊號類型"] == "valuation")].loc["name"]
        st = sn_dir.loc[:, (sn_dir.loc["訊號類型"] == "status")].loc["name"]

        sig = signals[sig]
        va = signals[va]
        st = signals[st]

        # === sell 方向 ===
        acc1 = acc(sig, ms, direction="sell")
        acc2 = acc(va, ms, direction="sell")
        acc3 = acc(st, ms, direction="sell")

        # 產生各個子指標的績效表（sell）
        sub1 = make_sheet(acc1, sig, "signal", ms, direction="sell", measurement=mea, top_n=top_nn, show_days=5)
        sub2 = make_sheet(acc2, va, "valuation", ms, direction="sell", measurement=mea, top_n=top_nn, show_days=5)
        sub3 = make_sheet(acc3, st, "status", ms, direction="sell", measurement=mea, top_n=top_nn, show_days=5)

        # 確保資料夾存在（sell）
        os.makedirs("sell_data", exist_ok=True)
        sub1.to_csv("sell_data/sub1.csv")
        sub2.to_csv("sell_data/sub2.csv")
        sub3.to_csv("sell_data/sub3.csv")

        # 產生綜合指標（sell）
        signal = calculate_index(acc1, sig, ms, subness="signal", measurement=mea)
        value = calculate_index(acc2, va, ms, subness="valuation", measurement=mea)
        status = calculate_index(acc3, st, ms, subness="sta", measurement=mea)

        subindex_matrix = pd.DataFrame({
            signal.iloc[:, -2].name: signal.iloc[:, -2],
            value.iloc[:, -2].name: value.iloc[:, -2],
            status.iloc[:, -2].name: status.iloc[:, -2]
        })

        subindex_matrix["composite_index"] = subindex_matrix.sum(axis=1)
        measurement = mea

        def optimze_threshold(df, ms, mea):
            best_thres = None
            best_precision = -np.inf
            best_num_signal = None
            n = len(df)
            top_n = int(df["composite_index"].max() + 1)
            min_required = int(np.ceil(n * 0.02))  # 2% 下限

            for thres in range(1, top_n):
                subindex_binary = (df["composite_index"] > thres).astype(int)
                acc_res = acc(pd.DataFrame(subindex_binary), ms=ms, direction="sell")
                precision = acc_res[mea].values[0]
                num_signal = acc_res["num_signal"].values[0]

                if num_signal >= min_required:
                    if best_thres is None or precision > best_precision:
                        best_thres = thres
                        best_precision = precision
                        best_num_signal = num_signal

            return best_thres, best_num_signal, best_precision

        best_thres, best_num_signal, best_precision = optimze_threshold(subindex_matrix, ms=ms, mea=measurement)

        # 主表只在 composite_index 那列填入 (measurement, num_signal)
        main_sheet = (subindex_matrix.sort_index(ascending=False).iloc[:5].T)
        main_sheet[[f"{measurement}", "num_signal"]] = np.nan
        main_sheet.loc["composite_index", [f"{measurement}", "num_signal"]] = [best_precision, best_num_signal]

        cols = main_sheet.columns.tolist()
        new_order = cols[-2:] + cols[:-2]
        main_sheet = main_sheet[new_order]

        main_sheet.to_csv("sell_data/main_chart.csv")

        # 視覺化（假設 visualize 回傳的是 Matplotlib Figure）
        import visualize
        importlib.reload(visualize)
        from visualize import plot_highzones_with_price, plot_lowzones_with_price

        fig = plot_highzones_with_price(
            ms,
            price_col="收盤價",
            scores_df=subindex_matrix,
            title="收盤價 × 低點區間 × 分數指標（SELL）",
            composite_threshold=best_thres + 1,     # 若你的門檻解讀是 > thres，圖上顯示可 +1 作為提示
            threshold_marker='v',                   # sell 用向下三角（可自行調整）
            threshold_marker_color='purple',
            threshold_label=f'門檻觸發(Composite>{best_thres})'
        )

        # 存圖（Matplotlib）
        os.makedirs("sell_data", exist_ok=True)
        fig.savefig("sell_data/plot.png", dpi=180, bbox_inches="tight")
    
    
    main_buy(mea)
    main_sell(mea)

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="執行 main 函數並指定 measurement")
    parser.add_argument("mea", type=str, help="指定 measurement，例如 fscore, precision")
    args = parser.parse_args()

    main(args.mea)






