#!/usr/bin/env python3
"""Decision-logic tests for check_reachability.py (#194 item 1)."""
import textwrap
import unittest

from check_reachability import unreachable_classes


def src(body):
    return textwrap.dedent(body)


class UnreachableClasses(unittest.TestCase):
    def test_class_below_main_is_flagged_with_line_and_name(self):
        found = unreachable_classes(src("""\
            import unittest

            class Reachable(unittest.TestCase):
                pass

            if __name__ == "__main__":
                unittest.main()

            class CarveOut(unittest.TestCase):
                pass
        """))
        self.assertEqual(found, [(9, "CarveOut")])

    def test_all_classes_above_main_pass(self):
        found = unreachable_classes(src("""\
            import unittest

            class A(unittest.TestCase):
                pass

            class B(unittest.TestCase):
                pass

            if __name__ == "__main__":
                unittest.main()
        """))
        self.assertEqual(found, [])

    def test_no_unittest_main_passes(self):
        found = unreachable_classes(src("""\
            class HelperOnly:
                pass

            print("assert-style test file with no unittest runner")
        """))
        self.assertEqual(found, [])

    def test_nested_class_below_main_not_flagged(self):
        found = unreachable_classes(src("""\
            import unittest

            if __name__ == "__main__":
                unittest.main()

            def factory():
                class Local:
                    pass
                return Local
        """))
        self.assertEqual(found, [])

    def test_call_text_inside_string_literal_ignored(self):
        found = unreachable_classes(src("""\
            import unittest

            FIXTURE = 'if __name__ == "__main__":\\n    unittest.main()'

            class StillReachable(unittest.TestCase):
                pass

            if __name__ == "__main__":
                unittest.main()
        """))
        self.assertEqual(found, [])

    def test_multiple_classes_below_main_all_flagged(self):
        found = unreachable_classes(src("""\
            import unittest

            if __name__ == "__main__":
                unittest.main()

            class First(unittest.TestCase):
                pass

            class Second(unittest.TestCase):
                pass
        """))
        self.assertEqual([name for _, name in found], ["First", "Second"])


if __name__ == "__main__":
    unittest.main()
