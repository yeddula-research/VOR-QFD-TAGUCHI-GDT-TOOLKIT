import unittest

import numpy as np

from vor_gdt import config, published
from vor_gdt.data_generation import generate_dataset
from vor_gdt.hoq import HouseOfQuality, relationship_frame, roof_frame
from vor_gdt.robust_design import analyze_experiment
from vor_gdt.vor import extract_vor, register_to_frame, weight_vor


class TestPublishedValues(unittest.TestCase):
    def test_table_shapes(self):
        self.assertEqual(published.TABLE1.shape, (6, 5))
        self.assertEqual(published.TABLE2.shape, (10, 7))
        self.assertEqual(published.TABLE3.shape, (3, 4))

    def test_table2_is_standard_l9(self):
        self.assertTrue(published.table2_is_l9())

    def test_optimal_row_repeats_run1(self):
        t2 = published.TABLE2.set_index("Experiment run")
        self.assertEqual(list(t2.loc["Optimal"]), list(t2.loc["Run 1"]))

    def test_main_effects_optimum_matches_reported_optimum(self):
        self.assertEqual(published.table2_optimum(), published.table2_reported_optimum())

    def test_table1_ranks_follow_aic(self):
        self.assertTrue(published.table1_ranks_follow_aic())

    def test_table2_as_printed_formatting(self):
        printed = published.table2_as_printed().set_index("Experiment run")
        self.assertEqual(printed.loc["Run 7", "Wall thickness tolerance (mm)"], "±1.2")
        self.assertEqual(printed.loc["Run 2", "Flange flatness (mm)"], "0.10")
        self.assertEqual(printed.loc["Run 6", "S/N ratio — flatness (dB)"], "20.0")

    def test_main_effects_levels(self):
        me = published.table2_main_effects()
        self.assertEqual(len(me), 9)
        wall = me[me["Factor"] == "Wall thickness tolerance"]["Mean published S/N (dB)"].tolist()
        self.assertAlmostEqual(wall[0], (18.2 + 17.8 + 17.1) / 3)
        self.assertTrue(wall[0] > wall[1] > wall[2])


class TestDemonstrationIsIndependentOfThePaper(unittest.TestCase):
    """The demonstration dataset is the toolkit's own; none of its values come from the paper."""

    @classmethod
    def setUpClass(cls):
        vor, _ = weight_vor(extract_vor(register_to_frame(config.PID_REGISTER)))
        cls.ranking = HouseOfQuality(vor, relationship_frame(), roof_frame()).ranking()
        ds = generate_dataset()
        cls.sn = analyze_experiment(ds["measurements"], ds["selected"])["sn"]

    def test_relationship_sums_and_aic_differ_from_table1(self):
        demo = self.ranking.set_index("engineering_characteristic")
        paper = published.TABLE1.set_index("Engineering characteristic")
        for ec in paper.index:
            self.assertNotEqual(int(demo.loc[ec, "relationship_sum"]), int(paper.loc[ec, "Relationship sum"]), ec)
            self.assertGreater(abs(float(demo.loc[ec, "aic"]) - float(paper.loc[ec, "Wr-weighted AIC"])), 1.0, ec)

    def test_sn_ratios_differ_from_table2(self):
        paper = published.table2_runs()
        pairs = {
            "shell_wall_thickness": "S/N ratio — wall (dB)",
            "nozzle_bore_position": "S/N ratio — bore (dB)",
            "flange_face_flatness": "S/N ratio — flatness (dB)",
        }
        for ec, col in pairs.items():
            gap = np.abs(self.sn[ec].to_numpy() - paper[col].to_numpy())
            self.assertGreater(gap.mean(), 2.0, ec)


if __name__ == "__main__":
    unittest.main()
