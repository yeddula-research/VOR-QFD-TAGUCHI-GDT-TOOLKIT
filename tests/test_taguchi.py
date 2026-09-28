import math
import unittest

import numpy as np
import pandas as pd

from vor_gdt.orthogonal_arrays import get_array
from vor_gdt.taguchi import (
    anova,
    main_effects,
    optimal_levels,
    predicted_sn,
    sn_by_run,
    sn_larger_the_better,
    sn_nominal_the_best,
    sn_ratio,
    sn_smaller_the_better,
)


def l9_design():
    return pd.DataFrame(get_array("L9")[:, :3], columns=["A", "B", "C"])


class TestSignalToNoise(unittest.TestCase):
    def test_nominal_the_best_equation3(self):
        # ybar = 11, s^2 (ddof=1) = 2  ->  10*log10(121/2)
        self.assertAlmostEqual(sn_nominal_the_best([10, 12]), 10 * math.log10(121 / 2))

    def test_nominal_the_best_rewards_lower_variance(self):
        self.assertGreater(sn_nominal_the_best([10.0, 10.1, 9.9]), sn_nominal_the_best([10.0, 11.0, 9.0]))

    def test_nominal_the_best_errors(self):
        with self.assertRaises(ValueError):
            sn_nominal_the_best([5.0])
        with self.assertRaises(ValueError):
            sn_nominal_the_best([5.0, 5.0])

    def test_smaller_the_better(self):
        self.assertAlmostEqual(sn_smaller_the_better([0.1, 0.1]), 20.0)

    def test_larger_the_better(self):
        self.assertAlmostEqual(sn_larger_the_better([10.0, 10.0]), 20.0)
        with self.assertRaises(ValueError):
            sn_larger_the_better([0.0, 1.0])

    def test_dispatch(self):
        self.assertAlmostEqual(sn_ratio([0.1, 0.1], "smaller_the_better"), 20.0)
        with self.assertRaises(ValueError):
            sn_ratio([1, 2], "bogus")

    def test_sn_by_run(self):
        m = pd.DataFrame({"run": [1, 1, 2, 2], "y": [0.1, 0.1, 0.01, 0.01]})
        out = sn_by_run(m, {"y": "smaller_the_better"})
        np.testing.assert_allclose(out["y"].to_numpy(), [20.0, 40.0])


class TestMainEffectsAndAnova(unittest.TestCase):
    def test_main_effects_and_optimum(self):
        d = l9_design()
        y = 30 - 4.0 * d["A"] + 1.0 * d["B"]
        me = main_effects(d, y)
        np.testing.assert_allclose(me["A"].to_numpy(), [31.0, 27.0, 23.0])
        best = optimal_levels(d, y)
        self.assertEqual((best["A"], best["B"]), (0, 2))
        # C has no effect: every level mean is equal.
        np.testing.assert_allclose(me["C"].to_numpy(), [27.0, 27.0, 27.0])

    def test_additive_prediction_exact(self):
        d = l9_design()
        a, b, c = [0.0, -3.0, -7.0], [2.0, 0.0, -1.0], [0.5, 0.0, 0.2]
        y = [20 + a[i] + b[j] + c[k] for i, j, k in d.to_numpy()]
        self.assertAlmostEqual(predicted_sn(d, y, {"A": 0, "B": 0, "C": 0}), 22.5)

    def test_anova_single_factor(self):
        d = l9_design()
        y = 10.0 * d["A"].to_numpy()
        tab = anova(d, y).set_index("source")
        self.assertAlmostEqual(tab.loc["A", "contribution_pct"], 100.0)
        self.assertAlmostEqual(tab.loc["B", "contribution_pct"], 0.0)
        self.assertEqual(tab.loc["Error", "dof"], 2)
        self.assertEqual(tab.loc["Total", "dof"], 8)

    def test_anova_contributions_sum(self):
        d = l9_design()
        rng = np.random.default_rng(0)
        y = 3 * d["A"] + d["B"] + rng.normal(0, 0.5, 9)
        tab = anova(d, y).set_index("source")
        self.assertAlmostEqual(tab.loc[["A", "B", "C", "Error"], "contribution_pct"].sum(), 100.0)
        self.assertAlmostEqual(tab.loc["Total", "contribution_pct"], 100.0)
        self.assertTrue(0 <= tab.loc["A", "p_value"] <= 1)

    def test_anova_length_mismatch(self):
        with self.assertRaises(ValueError):
            anova(l9_design(), [1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
