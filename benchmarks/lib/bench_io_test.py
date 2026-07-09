#!/usr/bin/env python3
"""Unit tests for bench_io's decision logic (ADR 0026): dump_records/load_records round-trip
records losslessly for both formats; csv/tsv flatten nested values into columns so no field ever
needs quoting; sample_and_archive_raw keeps exactly keep_per_group files per group and
gzip-archives (not silently discards) the rest. Run: python -m unittest bench_io_test.
"""
import os
import tarfile
import tempfile
import unittest

from bench_io import dump_records, load_records, sample_and_archive_raw

RECORDS = [
    {"bid": "1", "skill": "building-skills", "arm": "with"},
    {"bid": "2", "skill": "building-skills", "arm": "without"},
    {"bid": "3", "skill": "code-standards", "arm": "with"},
]


class DumpLoadRoundTripTest(unittest.TestCase):
    def test_default_fmt_is_csv(self):
        # ADR 0026: CSV is the default for flat records. dump/load with no fmt arg must round-trip.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.csv")
            dump_records(RECORDS, path)
            self.assertEqual(load_records(path), [dict(r) for r in RECORDS])

    def test_csv_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.csv")
            dump_records(RECORDS, path, fmt="csv")
            self.assertEqual(load_records(path, fmt="csv"), [dict(r) for r in RECORDS])

    def test_tsv_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.tsv")
            dump_records(RECORDS, path, fmt="tsv")
            self.assertEqual(load_records(path, fmt="tsv"), [dict(r) for r in RECORDS])

    def test_jsonl_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.jsonl")
            dump_records(RECORDS, path, fmt="jsonl")
            self.assertEqual(load_records(path, fmt="jsonl"), RECORDS)

    def test_jsonl_is_one_record_per_line_minified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.jsonl")
            dump_records(RECORDS, path, fmt="jsonl")
            with open(path, encoding="utf-8") as fh:
                lines = fh.readlines()
            self.assertEqual(len(lines), len(RECORDS))
            self.assertNotIn(" ", lines[0].rstrip("\n"))  # minified: no space after ':' or ','

    def test_jsonl_bytes_contain_no_cr(self):
        # The jsonl writer lacked newline="" — on Windows that silently CRLF-corrupted every JSONL
        # artifact (git's recurring CRLF-warning noise). Assert the raw bytes stay LF-only.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.jsonl")
            dump_records(RECORDS, path, fmt="jsonl")
            with open(path, "rb") as fh:
                raw = fh.read()
            self.assertNotIn(b"\r", raw)

    def test_empty_records_tsv_writes_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.tsv")
            dump_records([], path, fmt="tsv")
            self.assertEqual(load_records(path, fmt="tsv"), [])

    def test_unknown_fmt_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.yaml")
            with self.assertRaises(ValueError):
                dump_records(RECORDS, path, fmt="yaml")
            with self.assertRaises(ValueError):
                load_records(path, fmt="yaml")


class FlattenNestedValuesTest(unittest.TestCase):
    # ADR 0026: csv/tsv flatten nested values into columns (a CI list -> ci_lo/ci_hi) so no field
    # ever needs quoting.
    def test_csv_flattens_two_element_list_into_lo_hi_columns(self):
        records = [
            {"skill": "building-skills", "ci": [0.1, 0.9]},
            {"skill": "code-standards", "ci": [0.2, 0.8]},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.csv")
            dump_records(records, path, fmt="csv")
            with open(path, encoding="utf-8") as fh:
                header = fh.readline().strip()
            self.assertEqual(header, "skill,ci_lo,ci_hi")
            self.assertEqual(
                load_records(path, fmt="csv"),
                [
                    {"skill": "building-skills", "ci_lo": "0.1", "ci_hi": "0.9"},
                    {"skill": "code-standards", "ci_lo": "0.2", "ci_hi": "0.8"},
                ],
            )

    def test_csv_flattens_dict_into_prefixed_columns(self):
        records = [{"skill": "building-skills", "score": {"mean": 0.5, "n": 12}}]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.csv")
            dump_records(records, path, fmt="csv")
            with open(path, encoding="utf-8") as fh:
                header = fh.readline().strip()
            self.assertEqual(header, "skill,score_mean,score_n")

    def test_csv_flattens_longer_list_with_indexed_columns(self):
        records = [{"skill": "building-skills", "samples": [1, 2, 3]}]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.csv")
            dump_records(records, path, fmt="csv")
            with open(path, encoding="utf-8") as fh:
                header = fh.readline().strip()
            self.assertEqual(header, "skill,samples_0,samples_1,samples_2")

    def test_flattened_csv_never_needs_quoting(self):
        records = [{"skill": "building-skills", "ci": [0.1, 0.9], "evidence_count": 3}]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "records.csv")
            dump_records(records, path, fmt="csv")
            with open(path, encoding="utf-8") as fh:
                body = fh.read()
            self.assertNotIn('"', body)


def _group_of(filename):
    """Everything before the trailing '.<replicate>.txt' — mirrors a skill/eval/arm group key."""
    return filename.rsplit(".", 2)[0]


class SampleAndArchiveRawTest(unittest.TestCase):
    def _make_outputs(self, tmp, groups_and_counts):
        """groups_and_counts: {group_prefix: n_replicates}. Writes group_prefix.<i>.txt files."""
        for group, n in groups_and_counts.items():
            for i in range(1, n + 1):
                with open(os.path.join(tmp, f"{group}.{i}.txt"), "w", encoding="utf-8") as fh:
                    fh.write(f"raw output {group} replicate {i}\n")

    def test_keeps_exactly_keep_per_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_outputs(tmp, {"building-skills.1.with": 3, "building-skills.1.without": 3,
                                      "code-standards.1.with": 2})
            kept, archived = sample_and_archive_raw(tmp, keep_per_group=1, group_fn=_group_of)
            self.assertEqual(kept, 3)   # one per group, 3 groups
            self.assertEqual(archived, (3 - 1) + (3 - 1) + (2 - 1))  # = 5

    def test_kept_files_remain_plain_and_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_outputs(tmp, {"building-skills.1.with": 3})
            sample_and_archive_raw(tmp, keep_per_group=1, group_fn=_group_of)
            remaining = sorted(f for f in os.listdir(tmp) if f.endswith(".txt"))
            self.assertEqual(remaining, ["building-skills.1.with.1.txt"])  # sorted-order sample
            with open(os.path.join(tmp, remaining[0]), encoding="utf-8") as fh:
                self.assertIn("raw output", fh.read())

    def test_archived_files_removed_from_dir_and_present_in_tar(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_outputs(tmp, {"building-skills.1.with": 3})
            sample_and_archive_raw(tmp, keep_per_group=1, group_fn=_group_of)
            self.assertFalse(os.path.exists(os.path.join(tmp, "building-skills.1.with.2.txt")))
            self.assertFalse(os.path.exists(os.path.join(tmp, "building-skills.1.with.3.txt")))
            with tarfile.open(os.path.join(tmp, "all.tar.gz"), "r:gz") as tar:
                names = sorted(tar.getnames())
            self.assertEqual(names, ["building-skills.1.with.2.txt", "building-skills.1.with.3.txt"])

    def test_keep_per_group_larger_than_group_archives_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_outputs(tmp, {"solo-group": 1})
            kept, archived = sample_and_archive_raw(tmp, keep_per_group=5, group_fn=_group_of)
            self.assertEqual((kept, archived), (1, 0))
            with tarfile.open(os.path.join(tmp, "all.tar.gz"), "r:gz") as tar:
                self.assertEqual(tar.getnames(), [])

    def test_rerun_is_stable_ignores_prior_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_outputs(tmp, {"building-skills.1.with": 3})
            sample_and_archive_raw(tmp, keep_per_group=1, group_fn=_group_of)
            # A second pass over the now-sampled dir must not try to tar its own archive file.
            kept, archived = sample_and_archive_raw(tmp, keep_per_group=1, group_fn=_group_of)
            self.assertEqual((kept, archived), (1, 0))


if __name__ == "__main__":
    unittest.main()
