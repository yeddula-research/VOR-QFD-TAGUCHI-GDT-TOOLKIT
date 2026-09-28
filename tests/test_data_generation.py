import unittest

import numpy as np
import pandas as pd

from vor_gdt import config
from vor_gdt.data_generation import (
    generate_dataset,
    inner_design,
    noise_conditions,
    selected_characteristics,
    simulate_confirmation,
    simulate_response,
)

EXPECTED_COLUMNS = {
    "run",
    "noise_condition",
    "replicate",
    *config.NOISE_FACTORS,
    *[f"{ec}_level" for ec in config.CONTROL_FACTORS],
    *[f"{ec}_tolerance_mm" for ec in config.CONTROL_FACTORS],
    *config.CONTROL_FACTORS,
}


class TestDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = generate_dataset(config.RANDOM_SEED)
        cls.m = cls.ds["measurements"]

    def test_deterministic_for_seed(self):
        again = generate_dataset(config.RANDOM_SEED)["measurements"]
        pd.testing.assert_frame_equal(self.m, again)

    def test_different_seed_differs(self):
        other = generate_dataset(config.RANDOM_SEED + 100)["measurements"]
        self.assertFalse(np.allclose(self.m["shell_wall_thickness"], other["shell_wall_thickness"]))

    def test_shape(self):
        n_outer = len(noise_conditions())
        self.assertEqual(n_outer, 8)
        self.assertEqual(len(self.m), 9 * n_outer * config.REPLICATES_PER_NOISE_CONDITION)
        self.assertEqual(set(self.m.columns), EXPECTED_COLUMNS)

    def test_register_and_hoq_shapes(self):
        self.assertEqual(len(self.ds["register"]), len(config.PID_REGISTER))
        self.assertEqual(self.ds["relationships"].shape, (11, 6))
        self.assertEqual(self.ds["inner_array"], "L9")

    def test_tolerances_match_levels(self):
        for ec, cf in config.CONTROL_FACTORS.items():
            expected = self.m[f"{ec}_level"].map(lambda k, lv=cf["levels"]: lv[k])
            np.testing.assert_allclose(self.m[f"{ec}_tolerance_mm"], expected)

    def test_noise_coding_balanced(self):
        nc = noise_conditions()
        for f in config.NOISE_FACTORS:
            self.assertEqual(sorted(nc[f].unique()), [-1, 1])
            self.assertEqual(int(nc[f].sum()), 0)

    def test_responses_physical(self):
        self.assertTrue((self.m["nozzle_bore_position"] >= 0).all())
        self.assertTrue((self.m["flange_face_flatness"] >= config.SIMULATION["flange_face_flatness"]["floor"]).all())
        wall = self.m["shell_wall_thickness"]
        nominal = config.CONTROL_FACTORS["shell_wall_thickness"]["nominal_mm"]
        self.assertLess(abs(wall.mean() - nominal), 0.1)

    def test_looser_tolerance_means_more_spread(self):
        g = self.m.groupby("shell_wall_thickness_level")["shell_wall_thickness"].std()
        self.assertTrue(g.is_monotonic_increasing)

    def test_selected_characteristics(self):
        self.assertEqual(
            selected_characteristics(),
            ["shell_wall_thickness", "nozzle_bore_position", "flange_face_flatness"],
        )

    def test_inner_design_is_l9(self):
        name, design = inner_design(["a", "b", "c"])
        self.assertEqual(name, "L9")
        self.assertEqual(design.shape, (9, 3))

    def test_confirmation_single_run(self):
        levels = {ec: 0 for ec in config.CONTROL_FACTORS}
        c = simulate_confirmation(list(config.CONTROL_FACTORS), levels)
        self.assertEqual(c["run"].nunique(), 1)
        self.assertEqual(len(c), 8 * config.REPLICATES_PER_NOISE_CONDITION)

    def test_unknown_characteristic(self):
        with self.assertRaises(ValueError):
            simulate_response("surface_roughness", {"surface_roughness": 0}, {}, np.random.default_rng(0))


if __name__ == "__main__":
    unittest.main()
