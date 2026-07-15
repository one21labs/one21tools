#!/usr/bin/env python3
"""Test-class reachability guard (#194 item 1). Stdlib only, pure core + thin CLI.

gates.yml runs *_test.py files in SCRIPT mode (`python3 <file>`), so a test class defined
below the `if __name__ == "__main__": unittest.main()` block is never collected — the file
reads green forever while its tests silently don't run. check-gate-tests.mjs verifies a
test FILE is wired, not that its contents are reachable; this guard closes that gap.

Rule: in a *_test.py file, no top-level class definition may appear after the first
`unittest.main()` call. Parsed with `ast` (a string literal containing the call text never
false-positives); a file that fails to parse is reported as a failure (fail closed — the
test step would fail on it anyway).

Usage: python3 check_reachability.py <dir> [<dir> ...]   (scans <dir>/*_test.py)
Exit 1 listing every unreachable class; exit 0 otherwise.
"""
import ast


def unreachable_classes(source):
    """Return [(lineno, name)] for top-level classes defined after the first unittest.main() call."""
    tree = ast.parse(source)
    main_line = None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "main" and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "unittest"):
            main_line = node.lineno if main_line is None else min(main_line, node.lineno)
    if main_line is None:
        return []
    return [(n.lineno, n.name) for n in tree.body
            if isinstance(n, ast.ClassDef) and n.lineno > main_line]


def main(argv):
    import glob
    import os
    import sys
    dirs = argv[1:]
    if not dirs:
        sys.exit("usage: check_reachability.py <dir> [<dir> ...]")
    failures, checked = [], 0
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*_test.py"))):
            checked += 1
            with open(path, encoding="utf-8") as f:
                source = f.read()
            try:
                bad = unreachable_classes(source)
            except SyntaxError as e:
                failures.append(f"{path}: does not parse ({e.msg}, line {e.lineno})")
                continue
            failures.extend(
                f"{path}:{lineno}: class {name} is below unittest.main() — never collected "
                f"when CI runs the file in script mode" for lineno, name in bad)
    if failures:
        print("check_reachability: unreachable test classes:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)
    print(f"check_reachability: {checked} test file(s) scanned, every class reachable")


if __name__ == "__main__":
    import sys
    main(sys.argv)
