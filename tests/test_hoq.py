import unittest

import numpy as np
import pandas as pd

from vor_gdt import config
from vor_gdt.hoq import HouseOfQuality, absolute_importance, relationship_frame, roof_frame
from vor_gdt.vor import extract_vor, register_to_frame, weight_vor


def demo_hoq():
    vor, _ = weight_vor(extract_vor(register_to_frame(config.PID_REGISTER)))
    return HouseOfQuality(vor, relationship_frame(), roof_frame())


def tiny_hoq(relationships=((9, 3), (1, 0)), roof=()):
    vor = pd.DataFrame({"item_id": ["A", "B"], "parameter": ["pa", "pb"], "weight": [1.0, 2.0]})
    rel = pd.DataFrame(list(relationships), index=["A", "B"], columns=["x", "y"])
    rel.index.name = "item_id"
    return HouseOfQuality(vor, rel, roof_frame(list(roof)), ec_labels={"x": "X", "y": "Y"})


class TestEquation2(unittest.TestCase):
    def test_hand_example(self):
        # AIC_x = 1*9 + 2*1 = 11 ; AIC_y = 1*3 + 2*0 = 3
        np.testing.assert_allclose(absolute_importance([1, 2], [[9, 3], [1, 0]]), [11, 3])

    def test_shape_mismatch(self):
        with self.assertRaises(ValueError):
            absolute_importance([1, 2, 3], [[9, 3], [1, 0]])


class TestHouseOfQuality(unittest.TestCase):
    def test_ranking_sorted_with_ranks(self):
        rk = demo_hoq().ranking()
        self.assertTrue(rk["aic"].is_monotonic_decreasing)
        self.assertEqual(list(rk["priority_rank"]), list(range(1, len(rk) + 1)))
        self.assertAlmostEqual(rk["relative_importance_pct"].sum(), 100.0)

    def test_relationship_sums(self):
        hoq = tiny_hoq()
        self.assertEqual(list(hoq.relationship_sums()), [10, 3])

    def test_invalid_relationship_score(self):
        with self.assertRaises(ValueError):
            tiny_hoq(relationships=((5, 3), (1, 0)))

    def test_rows_must_match_vor(self):
        vor = pd.DataFrame({"item_id": ["A"], "parameter": ["pa"], "weight": [1.0]})
        rel = pd.DataFrame([[9], [1]], index=["A", "B"], columns=["x"])
        with self.assertRaises(ValueError):
            HouseOfQuality(vor, rel)

    def test_roof_unknown_ec(self):
        with self.assertRaises(ValueError):
            tiny_hoq(roof=[("x", "zzz", -1)])

    def test_select_top_k(self):
        hoq = demo_hoq()
        self.assertEqual(len(hoq.select_for_optimization(2)), 2)
        with self.assertRaises(ValueError):
            hoq.select_for_optimization(0)

    def test_demo_selection(self):
        self.assertEqual(
            demo_hoq().select_for_optimization(3),
            ["shell_wall_thickness", "nozzle_bore_position", "flange_face_flatness"],
        )

    def test_influencing_vor_strong(self):
        names = demo_hoq().influencing_vor("shell_wall_thickness", 9)
        self.assertIn("Design pressure", names)
        self.assertIn("Corrosion allowance", names)

    def test_conflicts_are_negative(self):
        conflicts = demo_hoq().conflicts()
        self.assertTrue(len(conflicts) > 0)
        self.assertTrue((conflicts["correlation"] < 0).all())

    def test_conflicts_filter(self):
        hoq = tiny_hoq(roof=[("x", "y", -1)])
        self.assertEqual(len(hoq.conflicts(["x"])), 1)
        self.assertEqual(len(hoq.conflicts(["nothing"])), 0)


if __name__ == "__main__":
    unittest.main()
