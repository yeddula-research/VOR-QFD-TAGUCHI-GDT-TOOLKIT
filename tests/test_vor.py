import unittest

import numpy as np

from vor_gdt import config
from vor_gdt.vor import (
    extract_vor,
    parameter_weights,
    register_to_frame,
    regulatory_criticality_weight,
    summarize_by_source,
    validate_register,
    weight_vor,
)


class TestEquation1(unittest.TestCase):
    def test_hand_example(self):
        # (9*5 + 5*3) / (5 + 3) = 60 / 8
        self.assertAlmostEqual(regulatory_criticality_weight([9, 5], [5, 3]), 7.5)

    def test_equal_criticality_gives_mean_severity(self):
        self.assertAlmostEqual(regulatory_criticality_weight([2, 4, 9], [1, 1, 1]), 5.0)

    def test_parameter_weights_sum_to_aggregate(self):
        s, c = [9, 7, 8, 5], [5, 5, 4, 3]
        self.assertAlmostEqual(parameter_weights(s, c).sum(), regulatory_criticality_weight(s, c))

    def test_parameter_weights_values(self):
        np.testing.assert_allclose(parameter_weights([9, 5], [5, 3]), [45 / 8, 15 / 8])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            regulatory_criticality_weight([9, 5], [5])
        with self.assertRaises(ValueError):
            regulatory_criticality_weight([9], [0])
        with self.assertRaises(ValueError):
            parameter_weights([], [])


class TestExtraction(unittest.TestCase):
    def setUp(self):
        self.register = register_to_frame(config.PID_REGISTER)

    def test_only_regulatory_items_extracted(self):
        vor = extract_vor(self.register)
        self.assertTrue(set(vor["source"]) <= set(config.REGULATORY_SOURCES))
        excluded = self.register[~self.register["source"].isin(config.REGULATORY_SOURCES)]
        self.assertTrue(len(excluded) > 0)
        self.assertFalse(set(excluded["item_id"]) & set(vor["item_id"]))

    def test_demo_register_yields_eleven_vor_parameters(self):
        self.assertEqual(len(extract_vor(self.register)), 11)

    def test_source_names_attached(self):
        vor = extract_vor(self.register)
        self.assertTrue(vor["source_name"].notna().all())

    def test_weight_vor_adds_weights(self):
        vor, w_r = weight_vor(extract_vor(self.register))
        self.assertAlmostEqual(vor["weight"].sum(), w_r)
        self.assertTrue((vor["weight"] > 0).all())

    def test_summary_counts(self):
        vor, _ = weight_vor(extract_vor(self.register))
        self.assertEqual(summarize_by_source(vor)["parameters"].sum(), len(vor))

    def test_validation_rejects_bad_severity(self):
        bad = self.register.copy()
        bad.loc[0, "severity"] = 10
        with self.assertRaises(ValueError):
            validate_register(bad)

    def test_validation_rejects_unknown_source(self):
        bad = self.register.copy()
        bad.loc[0, "source"] = "SOMETHING_ELSE"
        with self.assertRaises(ValueError):
            validate_register(bad)

    def test_validation_rejects_duplicate_ids(self):
        bad = self.register.copy()
        bad.loc[1, "item_id"] = bad.loc[0, "item_id"]
        with self.assertRaises(ValueError):
            validate_register(bad)


if __name__ == "__main__":
    unittest.main()
