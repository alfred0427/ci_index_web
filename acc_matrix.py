import pandas as pd
import numpy as np

def acc(signals, ms, direction):
        ms = ms.copy()

        if direction == "sell":
            num_signal = (signals.sum())
            tp = ((signals == 1) & (ms["波段高點區間"] == 1).values[:, None])
            fp = (signals == 1) & (ms["波段高點區間"] == 0).values[:, None]
            tn = (signals == 0) & (ms["波段高點區間"] == 0).values[:, None]
            fn = (signals == 0) & (ms["波段高點區間"] == 1).values[:, None]
            
            eps = 1e-12



            accuracy = (tp.sum() + tn.sum()) / (len(tp)+eps)
            precision = tp.sum() / ((tp.sum() + fp.sum())+eps)
            recall = tp.sum() / ((tp.sum() + fn.sum())+eps)

            def F(beta, p, r): return ((1 + beta**2) * r * p) / (((beta**2) * p) + r)
            fscore = F(0.5, precision, recall)

            nearest_dates_h = signals.loc[ms["波段高點"] == 1].index
            ms["最近波段高點時間"] = signals.index.to_series().apply(
                lambda x: nearest_dates_h[np.abs(nearest_dates_h - x).argmin()]
            )
            ms["diff_peak"] = (abs(signals.index - ms["最近波段高點時間"])).dt.days

            eff_diss_h = signals.iloc[:, 4:137].mul((ms["diff_peak"].values), axis=0)
            eff_diss_h = eff_diss_h[eff_diss_h != 0].mean()

            return pd.DataFrame({
                "num_signal": num_signal,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "fscore": fscore,
                "eff_diss": eff_diss_h
            })





  
  
        if direction == "buy":
            num_signal = (signals.sum())
            tp = ((signals == 1) & (ms["波段低點區間"] == 1).values[:, None])
            fp = (signals == 1) & (ms["波段低點區間"] == 0).values[:, None]
            tn = (signals == 0) & (ms["波段低點區間"] == 0).values[:, None]
            fn = (signals == 0) & (ms["波段低點區間"] == 1).values[:, None]

            accuracy = (tp.sum() + tn.sum()) / len(tp)
            precision = tp.sum() / (tp.sum() + fp.sum())
            recall = tp.sum() / (tp.sum() + fn.sum())

            def F(beta, p, r): return ((1 + beta**2) * r * p) / (((beta**2) * p) + r)
            fscore = F(0.5, precision, recall)

            nearest_dates_h = signals.loc[ms["波段低點"] == 1].index
            ms["最近波段低點時間"] = signals.index.to_series().apply(
                lambda x: nearest_dates_h[np.abs(nearest_dates_h - x).argmin()]
            )
            ms["diff_valley"] = (abs(signals.index - ms["最近波段低點時間"])).dt.days

            eff_diss_l = signals.iloc[:, 4:137].mul((ms["diff_valley"].values), axis=0)
            eff_diss_l = eff_diss_l[eff_diss_l != 0].mean()

            return pd.DataFrame({
                "num_signal": num_signal,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "fscore": fscore,
                "eff_diss": eff_diss_l
            })
        







