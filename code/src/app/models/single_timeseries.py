# Finding Ghosts in Your Data
# Time series anomaly detection
# For more information on this, review chapters 13-15

import pandas as pd

def detect_single_timeseries(
    df,
    sensitivity_score,
    max_fraction_anomalies,
    n_neighbors
):
    df_out = df.assign(is_anomaly=False, anomaly_score=0.0)
    return (df_out, [0,0,0], "No ensemble chosen.")