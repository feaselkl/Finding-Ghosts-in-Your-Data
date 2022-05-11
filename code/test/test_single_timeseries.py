from numpy import number
from src.app.models.multivariate import *
import pandas as pd
import pytest
import ruptures as rpt
from ruptures.metrics import precision_recall

# Generate artificial test data with Gaussian noise and 4 breakpoints
# https://centre-borelli.github.io/ruptures-docs/getting-started/basic-usage/
n_samples, n_dims, sigma = 1000, 3, 2
n_bkps = 4
signal, bkps = rpt.pw_constant(n_samples, n_dims, n_bkps, noise_std=sigma)

# Perform test and get results.  Should be within 2% of the actual change for 1000 points.
def test_detect_single_time_series_basic_usage():
    # Arrange - Happened above.
    # Act
    algo = rpt.Pelt(model="rbf").fit(signal)
    result = algo.predict(pen=10)
    # Assert
    # Test one:  no single element is more than 2% off
    max_difference = n_samples * 0.02
    differences = [abs(r-b) for (r,b) in zip(result, bkps)]
    num_differences = len([i for i in differences if i > max_difference])
    assert(num_differences == 0)
    # Test 2:  we correctly detect every change point (within 2%) and have zero spurious detections.
    p, r = precision_recall(result, bkps, margin=max_difference)
    assert(p == 1.0)
    assert(r == 1.0)

    

# todo:  smoke testing data frame counts

# todo:  one anomaly

# todo:  multiple anomalies

# todo:  no anomalies
