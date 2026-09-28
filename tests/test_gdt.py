import unittest

import pandas as pd

from vor_gdt import config
from vor_gdt.gdt import FeatureControlFrame, build_callout, formulate_scheme, position_zone_diameter
from vor_gdt.hoq import HouseOfQuality, relationship_frame, roof_frame
from vor_gdt.vor import extract_vor, register_to_frame, weight_vor


def demo_ranking():
    vor, _ = weight_vor(extract_vor(register_to_frame(config.PID_REGISTER)))
    return HouseOfQuality(vor, relationship_frame(), roof_frame()).ranking()


class TestFeatureControlFrame(unittest.TestCase):
    def test_position_render(self):
        fcf = FeatureControlFrame("position", 0.6, ("A", "B", "C"), diameter_zone=True)
        self.assertEqual(fcf.render(), "⌖ | ⌀0.60 | A | B | C")
        self.assertEqual(fcf.category, "location")

    def test_flatness_render(self):
        self.assertEqual(FeatureControlFrame("flatness", 0.05).render(), "⏥ | 0.05")

    def test_form_control_rejects_datums(self):
        with self.assertRaises(ValueError):
            FeatureControlFrame("flatness", 0.05, ("A",))

    def test_orientation_requires_datum(self):
        with self.assertRaises(ValueError):
            FeatureControlFrame("perpendicularity", 0.5)

    def test_removed_2018_characteristics(self):
        for name in ("concentricity", "symmetry"):
            with self.assertRaises(ValueError):
                FeatureControlFrame(name, 0.1, ("A",))

    def test_positive_tolerance(self):
        with self.assertRaises(ValueError):
            FeatureControlFrame("flatness", 0.0)

    def test_size_needs_nominal(self):
        with self.assertRaises(ValueError):
            FeatureControlFrame("size", 0.5)
        self.assertEqual(FeatureControlFrame("size", 0.5, nominal=16.0).render(), "16.0 ±0.50 mm")

    def test_position_zone_diameter(self):
        self.assertAlmostEqual(position_zone_diameter(0.3), 0.6)
        with self.assertRaises(ValueError):
            position_zone_diameter(0)


class TestScheme(unittest.TestCase):
    def test_build_callout_position(self):
        fcf = build_callout("nozzle_bore_position", 0.3)
        self.assertEqual(fcf.characteristic, "position")
        self.assertAlmostEqual(fcf.tolerance, 0.6)

    def test_scheme_uses_optimum_and_defaults(self):
        optimum = {"shell_wall_thickness": 0.5, "nozzle_bore_position": 0.3, "flange_face_flatness": 0.05}
        scheme = formulate_scheme(demo_ranking(), optimum).set_index("ec")
        self.assertEqual(len(scheme), 6)
        for ec in optimum:
            self.assertEqual(scheme.loc[ec, "tolerance_source"], "Taguchi optimum")
        self.assertEqual(scheme.loc["surface_roughness", "tolerance_source"], "Default (not optimized)")
        self.assertEqual(scheme.loc["flange_face_flatness", "callout"], "⏥ | 0.05")
        self.assertEqual(scheme.loc["flange_face_flatness", "datums"], "-")

    def test_missing_default_raises(self):
        ranking = pd.DataFrame(
            [{"ec": "shell_wall_thickness", "engineering_characteristic": "Wall", "aic": 1.0, "priority_rank": 1}]
        )
        with self.assertRaises(ValueError):
            formulate_scheme(ranking, {})


if __name__ == "__main__":
    unittest.main()
