# Finding Ghosts in Your Data
# Time series anomaly detection
# For more information on this, review chapters 13-14

import pandas as pd
import numpy as np
from pandas.core import base
import ruptures as rpt

def detect_single_timeseries(
    df,
    sensitivity_score,
    max_fraction_anomalies
):
    df_out = df.assign(is_anomaly=False, anomaly_score=0.0)
    return (df_out, [0,0,0], "No ensemble chosen.")

def run_tests(df, max_fraction_anomalies, n_neighbors):
    num_records = df['key'].shape[0]
    if (num_records > 1000):
        run_loci = 0
    else:
        run_loci = 1

    tests_run = {
        "cof": 1,
        "loci": run_loci,
        "copod": 1
    }
    diagnostics = {
        "Number of records": num_records
    }
    # Remove key and vals, leaving the split-out and encoded versions of values.
    # Bring them back in as an array, as that's what our tests will require.
    col_array = df.drop(["key", "vals"], axis=1).to_numpy()

    # Determine numbers of neighbors
    # Ensure we have n_neighbors at least 5 below the number of records.
    # Ensure we have a boundary on number of tests.  100 above n_neighbors is a bit arbitrary
    # if we have extremely large datasets but should be fine for 1k-10k.
    n_neighbor_range = range(n_neighbors, min(num_records - 5, n_neighbors + 100), 5)
    n_neighbor_range_len = len(n_neighbor_range)

    # COF
    labels_cof = np.zeros([num_records, n_neighbor_range_len])
    scores_cof = np.zeros([num_records, n_neighbor_range_len])
    for idx,n in enumerate(n_neighbor_range):
        (labels_cof[:, idx], scores_cof[:, idx], diag_idx) = check_cof(col_array, max_fraction_anomalies=max_fraction_anomalies, n_neighbors=n)
        k = "Neighbors_" + str(n)
        diagnostics[k] = diag_idx


    df["is_raw_anomaly_cof"] = majority_vote(labels_cof)
    anomaly_score = median(scores_cof)
    df["anomaly_score_cof"] = anomaly_score

    # LOCI
    if (run_loci == 1):
        (labels_loci, scores_loci, diag_loci) = check_loci(col_array)
        df["is_raw_anomaly_loci"] = labels_loci
        anomaly_score = anomaly_score + scores_loci
        diagnostics["LOCI"] = diag_loci
        df["anomaly_score_loci"] = scores_loci

    # COPOD
    (labels_copod, scores_copod, diag_copod) = check_copod(col_array)
    df["is_raw_anomaly_copod"] = labels_copod
    diagnostics["COPOD"] = diag_copod
    df["anomaly_score_copod"] = scores_copod
    anomaly_score = anomaly_score + scores_copod

    df["anomaly_score"] = anomaly_score
    return (df, tests_run, diagnostics)


def check_cof(col_array, max_fraction_anomalies, n_neighbors):
    clf = COF(n_neighbors=n_neighbors, contamination=max_fraction_anomalies)
    clf.fit(col_array)
    diagnostics = {
        "COF Contamination": clf.contamination,
        "COF Threshold": clf.threshold_
    }
    return (clf.labels_, clf.decision_scores_, diagnostics)

# LOCI doesn't use contamination and has good defaults of k=3 and alpha=0.5.
def check_loci(col_array):
    clf = LOCI()
    clf.fit(col_array)
    diagnostics = {
        "LOCI Threshold": clf.threshold_
    }
    return (clf.labels_, clf.decision_scores_, diagnostics)

def check_copod(col_array):
    clf = COPOD()
    clf.fit(col_array)
    diagnostics = {
        "COPOD Threshold": clf.threshold_
    }
    return (clf.labels_, clf.decision_scores_, diagnostics)

def determine_outliers(
    df,
    tests_run,
    sensitivity_factors,
    sensitivity_score,
    max_fraction_anomalies
):
    # Need to multiply this because we don't know up-front if we ran, e.g., LOCI.
    tested_sensitivity_factors = {sf: sensitivity_factors.get(sf, 0) * tests_run.get(sf, 0) for sf in set(sensitivity_factors).union(tests_run)}
    # COPOD typically has a fairly consistent spread but the median point may be quite different,
    # so we will start from the median and add our sensitivity factor to it.
    median_copod = df["anomaly_score_copod"].median()
    sensitivity_threshold = sum([tested_sensitivity_factors[w] for w in tested_sensitivity_factors]) + median_copod
    diagnostics = { "Sensitivity threshold": sensitivity_threshold, "COPOD Median": median_copod }
    # Convert sensitivity score to be approximately the same
    # scale as anomaly score.  Note that sensitivity score is "reversed",
    # such that 100 is the *most* sensitive.
    # Multiply this by the second-largest anomaly score to scale appropriately.
    second_largest = df['anomaly_score'].nlargest(2).iloc[1]
    sensitivity_score = (100 - sensitivity_score) * second_largest / 100.0
    diagnostics["Raw sensitivity score"] = sensitivity_score
    # Get the 100-Nth percentile of anomaly score.
    # Ex:  if max_fraction_anomalies = 0.1, get the
    # 90th percentile anomaly score.
    max_fraction_anomaly_score = np.quantile(df['anomaly_score'], 1.0 - max_fraction_anomalies)
    diagnostics["Max fraction anomaly score"] = max_fraction_anomaly_score
    # If the max fraction anomaly score is greater than
    # the sensitivity score, it means that we have MORE outliers
    # than our max_fraction_anomalies supports, and therefore we
    # need to cut it off before we get down to our sensitivity score.
    # Otherwise, sensitivity score stays the same and we operate as normal.
    if max_fraction_anomaly_score > sensitivity_score and max_fraction_anomalies < 1.0:
        sensitivity_score = max_fraction_anomaly_score
    diagnostics["Sensitivity score"] = sensitivity_score
    return (df.assign(is_anomaly=df['anomaly_score'] > np.max([sensitivity_score, sensitivity_threshold])), diagnostics)
