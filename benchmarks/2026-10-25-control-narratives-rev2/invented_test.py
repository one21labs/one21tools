import unittest

from invented import absent, values


class AbsentTest(unittest.TestCase):
    def test_invented_trip_value_counts(self):
        self.assertEqual(absent("LT-201 normal level 50%", "trip at 85% and alarm at 50%"), [85.0])

    def test_tags_and_ids_are_not_values(self):
        self.assertEqual(absent("pump P-101", "SP-07 on LT-201, FR-K100-003, ISA-106"), [])

    def test_ordinals_skipped(self):
        self.assertEqual(values("Step 3. Step 12."), set())

    def test_thousands_separator_matches_plain(self):
        self.assertEqual(absent("rated 1500 rpm", "trip above 1,500 rpm"), [])

    def test_decimal_from_task_not_counted(self):
        self.assertEqual(absent("setpoint 3.5 barg", "hold at 3.5 barg, trip at 4.2 barg"), [4.2])


if __name__ == "__main__":
    unittest.main()
