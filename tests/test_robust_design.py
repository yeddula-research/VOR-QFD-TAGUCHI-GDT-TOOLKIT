import unittest

from vor_gdt import config
from vor_gdt.data_generation import generate_dataset, simulate_confirmation
from vor_gdt.robust_design import analyze_experiment, confirmation_sn, design_from_measurements, format_level


class TestRobustDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ds = generate_dataset(config.RANDOM_SEED)
        cls.ecs = ds["selected"]
        cls.m = ds["measurements"]
        cls.res = analyze_experiment(cls.m, cls.ecs)

    def test_design_recovered(self):
        d = design_from_measurements(self.m, self.ecs)
        self.assertEqual(d.shape, (9, 3))
        self.assertEqual(list(d.columns), self.ecs)

    def test_sn_table_shape(self):
        self.assertEqual(self.res["sn"].shape, (9, 3))

    def test_optimum_is_tightest_tolerance(self):
        self.assertEqual(self.res["optimum_levels"], {ec: 0 for ec in self.ecs})
        for ec in self.ecs:
            self.assertEqual(self.res["optimal_tolerance"][ec], config.CONTROL_FACTORS[ec]["levels"][0])

    def test_own_factor_dominates_anova(self):
        for ec in self.ecs:
            tab = self.res["anova"][ec].set_index("source")
            own = tab.loc[ec, "contribution_pct"]
            others = tab.loc[[e for e in self.ecs if e != ec], "contribution_pct"]
            self.assertTrue((own > others).all())

    def test_confirmation_close_to_prediction(self):
        confirm = simulate_confirmation(self.ecs, self.res["optimum_levels"])
        observed = confirmation_sn(confirm, self.ecs)
        for ec in self.ecs:
            self.assertLess(abs(observed[ec] - self.res["predicted_sn"][ec]), 2.0)

    def test_format_level(self):
        self.assertEqual(format_level("shell_wall_thickness", 0), "±0.5 mm")
        self.assertEqual(format_level("flange_face_flatness", 2), "0.15 mm")


if __name__ == "__main__":
    unittest.main()
