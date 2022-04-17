# Finding Ghosts in Your Data
# Multivariate anomaly detection
# For more information on this, review chapters 10-12

import pandas as pd
import numpy as np
from pandas.core import base
from pyod.models.cof import COF
from pyod.utils.data import evaluate_print
from sklearn.preprocessing import OrdinalEncoder

def detect_multivariate_statistical(
    df,
    sensitivity_score,
    max_fraction_anomalies,
    n_neighbors
):
    weights = {"cof": 1.0}

    num_data_points = df['vals'].count()
    if (num_data_points < 15):
        return (df.assign(is_anomaly=False, anomaly_score=0.0), weights, f"Must have a minimum of at least fifteen data points for anomaly detection.  You sent {num_data_points}.")
    elif (max_fraction_anomalies <= 0.0 or max_fraction_anomalies > 1.0):
        return (df.assign(is_anomaly=False, anomaly_score=0.0), weights, "Must have a valid max fraction of anomalies, 0 < x <= 1.0.")
    elif (sensitivity_score <= 0 or sensitivity_score > 100 ):
        return (df.assign(is_anomaly=False, anomaly_score=0.0), weights, "Must have a valid sensitivity score, 0 < x <= 100.")
    elif (df['vals'].count() < (n_neighbors - 5)):
        return (df.assign(is_anomaly=False, anomaly_score=0.0), weights, f"You sent in {num_data_points} data points, so n_neighbors should be no more than {num_data_points - 5}--that is, n_neighbors should be at least 5 less than the number of observations.")
    else:
        (df_encoded, diagnostics) = encode_string_data(df)
        (df_tested, tests_run, diagnostics) = run_tests(df_encoded, n_neighbors)
        df_out = determine_outliers(df_tested, sensitivity_score, max_fraction_anomalies)
        return (df_out, weights, { "message": "Result of multivariate statistical tests.", "Tests run": tests_run, "Test diagnostics": diagnostics})

def encode_string_data(df):
    # df comes in with two columns:  key and vals.
    # We want to break out the list in vals and turn it into a set of columns.
    # Column names don't matter here.
    df2 = pd.DataFrame([pd.Series(x) for x in df.vals])
    string_cols = df2.select_dtypes(include=[object]).columns.values
    diagnostics = { "Number of string columns in input": len(string_cols) }
    if (len(string_cols) > 0):
        diagnostics["Encoding Operation"] = "Encoding performed on string columns."
        # If there are any string columns in our list, convert them to ordinals.
        # CRITICAL NOTE:  this is not a great practice!  We don't have a mechanism (here)
        # to determine string nearness, so "cat" might get a value of 1.0 and "cats" may be 900.0.
        # Our outlier detection engine really depends on numeric inputs, though, so the options
        # are to avoid encoding altogether and simply fail on string inputs or perform the
        # encoding and potentially lose information if the strings are not truly ordinal.
        enc = OrdinalEncoder()
        # Look for any inputs of type object; numeric values will come in as float64 or int64.
        # Generate a float value for each unique string in the input dataset.
        enc.fit(df2[string_cols])
        # Transform any string columns into their encoded values.
        df2[string_cols] = enc.transform(df2[string_cols])
    else:
        diagnostics["Encoding Operation"] = "No encoding necessary because all columns are numeric."
    # Merge together the two DataFrames.  They will have the same number of rows and will
    # remain in the same order.

    return (pd.concat([df, df2], axis=1), diagnostics)

def run_tests(df, n_neighbors):
    tests_run = {
        "cof": 1
    }
    (df_cof, diagnostics) = check_cof(df, n_neighbors)
    return (df_cof, tests_run, diagnostics)


def check_cof(df, n_neighbors):
    # Remove key and vals, leaving the split-out and encoded versions of values.
    # Bring them back in as an array, as that's what our tests will require.
    col_array = df.drop(["key", "vals"], axis=1).to_numpy()
    clf = COF(n_neighbors=n_neighbors)
    clf.fit(col_array)
    diagnostics = {
        "COF Contamination": clf.contamination,
        "COF Threshold": clf.threshold_
    }
    df["is_raw_anomaly"] = clf.labels_
    df["anomaly_score"] = clf.decision_scores_
    return (df, diagnostics)

def determine_outliers(
    df,
    sensitivity_score,
    max_fraction_anomalies
):
    # Convert sensitivity score to be approximately the same
    # scale as anomaly score.  Note that sensitivity score is "reversed",
    # such that 100 is the *most* sensitive.
    sensitivity_score = (100 - sensitivity_score) / 100.0
    # Get the 100-Nth percentile of anomaly score.
    # Ex:  if max_fraction_anomalies = 0.1, get the
    # 90th percentile anomaly score.
    max_fraction_anomaly_score = np.quantile(df['anomaly_score'], 1.0 - max_fraction_anomalies)
    # If the max fraction anomaly score is greater than
    # the sensitivity score, it means that we have MORE outliers
    # than our max_fraction_anomalies supports, and therefore we
    # need to cut it off before we get down to our sensitivity score.
    # Otherwise, sensitivity score stays the same and we operate as normal.
    if max_fraction_anomaly_score > sensitivity_score and max_fraction_anomalies < 1.0:
        sensitivity_score = max_fraction_anomaly_score
    return df.assign(is_anomaly=(df['anomaly_score'] > sensitivity_score))