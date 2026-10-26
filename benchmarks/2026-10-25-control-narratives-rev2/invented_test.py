import unittest

from invented import absent, new_cites, values


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

    def test_citations_and_dates_are_not_values(self):
        for cite in ("per IEC 61511 SRS", "ISO 9001:2015", "IEC 61508-2:2010", "ISA 18.2",
                     "ANSI/ISA 84.00.01-2004", "ASD-STE100 Issue 9 (Jan 2025)",
                     "by 30 Nov 2026", "by Nov 30, 2026"):
            with self.subTest(cite):
                self.assertEqual(absent("pump P-101", f"Write it {cite}; trip at 2030 rpm."),
                                 [2030.0])

    def test_document_structure_numbers_are_not_values(self):
        self.assertEqual(values("See Section 4.2, Table 3.1, Rev 2.1, Fig. 2.3 and § 5.3."), set())
        self.assertEqual(values("## 3.2 Interlocks\n4.1.2 Start\nTrip at 3.2 bar."), {3.2})

    def test_negative_value_counts(self):
        self.assertEqual(absent("hold at -20 degC", "trip at -40 degC, hold at -20 degC"), [-40.0])
        self.assertEqual(absent("low limit -40 degC", "trip at \u221240 degC"), [])

    def test_tolerance_is_unsigned(self):
        self.assertEqual(absent("deadband \u00b12%", "deadband +/-2%, accuracy +/-0.5 degC"), [0.5])

    def test_range_counts_both_ends(self):
        self.assertEqual(absent("normal level 50%", "operate within 85-95%"), [85.0, 95.0])
        self.assertEqual(absent("high alarm 95%", "operate within 85-95%"), [85.0])

    def test_clock_time_is_one_value(self):
        self.assertEqual(absent("start at 06:00", "start at 6:00, purge ends 10:30"), ["10:30"])
        self.assertEqual(absent("purge for 30 min", "purge ends 10:30"), ["10:30"])

    def test_treatment_values_count_in_neither_arm(self):
        given = frozenset(values("Procedural sentences 20 words max; descriptive 25 max."))
        self.assertEqual(absent("pump P-101", "Keep sentences under 25 words; trip at 85%.", given),
                         [85.0])


class CitesTest(unittest.TestCase):
    def test_lists_citations_the_task_and_treatment_did_not_give(self):
        reply = ("Per IEC 61511-1:2016, ANSI/ISA-5.06.01-2007, ISA-18.2, ASD-STE100 and "
                 "NAMUR NE 107; trip at 85%.")
        self.assertEqual(new_cites("Follow ISA-18.2.", reply, frozenset({"ASD-STE100"})),
                         ["ANSI/ISA-5.06.01-2007", "IEC 61511-1:2016", "NAMUR NE 107"])

    def test_tags_are_not_citations(self):
        self.assertEqual(new_cites("", "LT-201 above SP-07 trips P-101; see FR-K100-003."), [])


if __name__ == "__main__":
    unittest.main()
