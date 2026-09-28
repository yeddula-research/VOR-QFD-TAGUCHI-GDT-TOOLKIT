import unittest

import numpy as np

from vor_gdt.orthogonal_arrays import ARRAYS, assign_columns, get_array, is_orthogonal, select_inner_array


class TestArrays(unittest.TestCase):
    def test_shapes(self):
        expected = {"L4": (4, 3), "L8": (8, 7), "L9": (9, 4), "L18": (18, 8)}
        for name, shape in expected.items():
            self.assertEqual(get_array(name).shape, shape)

    def test_all_arrays_orthogonal(self):
        for name in ARRAYS:
            self.assertTrue(is_orthogonal(get_array(name)), name)

    def test_levels_coded_from_zero(self):
        l9 = get_array("L9")
        self.assertEqual(sorted(np.unique(l9)), [0, 1, 2])
        l18 = get_array("L18")
        self.assertEqual(sorted(np.unique(l18[:, 0])), [0, 1])

    def test_non_orthogonal_detected(self):
        bad = np.array([[0, 0], [0, 0], [1, 1], [1, 0]])
        self.assertFalse(is_orthogonal(bad))

    def test_unknown_array(self):
        with self.assertRaises(ValueError):
            get_array("L27")


class TestSelection(unittest.TestCase):
    def test_l9_up_to_four_factors(self):
        for n in range(1, 5):
            self.assertEqual(select_inner_array(n), "L9")

    def test_l18_for_five_to_seven(self):
        for n in range(5, 8):
            self.assertEqual(select_inner_array(n), "L18")

    def test_too_many_factors(self):
        with self.assertRaises(ValueError):
            select_inner_array(8)

    def test_only_three_levels(self):
        with self.assertRaises(ValueError):
            select_inner_array(3, n_levels=2)

    def test_assign_columns(self):
        self.assertEqual(assign_columns("L9", 3), [0, 1, 2])
        self.assertEqual(assign_columns("L18", 2), [1, 2])
        with self.assertRaises(ValueError):
            assign_columns("L9", 5)


if __name__ == "__main__":
    unittest.main()
