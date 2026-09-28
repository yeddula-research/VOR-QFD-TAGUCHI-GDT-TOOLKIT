import unittest

from vor_gdt import config
from vor_gdt.gdt import formulate_scheme
from vor_gdt.hoq import HouseOfQuality, relationship_frame, roof_frame
from vor_gdt.reporting import to_markdown
from vor_gdt.traceability import build_traceability_matrix, coverage
from vor_gdt.vor import extract_vor, register_to_frame, weight_vor

OPTIMUM = {"shell_wall_thickness": 0.5, "nozzle_bore_position": 0.3, "flange_face_flatness": 0.05}


class TestTraceability(unittest.TestCase):
    def setUp(self):
        self.vor, _ = weight_vor(extract_vor(register_to_frame(config.PID_REGISTER)))
        self.rel = relationship_frame()
        ranking = HouseOfQuality(self.vor, self.rel, roof_frame()).ranking()
        self.scheme = formulate_scheme(ranking, OPTIMUM)

    def test_demo_full_coverage(self):
        trace = build_traceability_matrix(self.scheme, self.vor, self.rel)
        cov = coverage(trace, self.scheme, self.vor)
        self.assertEqual(cov["vor_coverage_pct"], 100.0)
        self.assertEqual(cov["callout_coverage_pct"], 100.0)
        self.assertTrue((trace["relationship"] >= config.TRACE_RELATIONSHIP_THRESHOLD).all())

    def test_links_carry_pid_tags(self):
        trace = build_traceability_matrix(self.scheme, self.vor, self.rel)
        wall = trace[trace["ec"] == "shell_wall_thickness"]
        self.assertIn("Design pressure", set(wall["vor_parameter"]))
        self.assertTrue(wall["pid_tag"].notna().all())

    def test_untraced_callout_detected(self):
        rel = self.rel.copy()
        rel["surface_roughness"] = 0
        trace = build_traceability_matrix(self.scheme, self.vor, rel)
        self.assertIn("surface_roughness", coverage(trace, self.scheme, self.vor)["untraced_callouts"])

    def test_untraced_vor_detected(self):
        rel = self.rel.copy()
        rel.loc["R09"] = 0
        trace = build_traceability_matrix(self.scheme, self.vor, rel)
        self.assertIn("R09", coverage(trace, self.scheme, self.vor)["untraced_vor"])


class TestReporting(unittest.TestCase):
    def test_markdown_table(self):
        import pandas as pd

        md = to_markdown(pd.DataFrame({"a": [1.234], "b": ["x"]}))
        self.assertEqual(md, "| a | b |\n|---|---|\n| 1.23 | x |\n")

    def test_markdown_escapes_pipes(self):
        import pandas as pd

        md = to_markdown(pd.DataFrame({"callout": ["⏥ | 0.05"]}))
        self.assertIn("⏥ \\| 0.05", md)


if __name__ == "__main__":
    unittest.main()
