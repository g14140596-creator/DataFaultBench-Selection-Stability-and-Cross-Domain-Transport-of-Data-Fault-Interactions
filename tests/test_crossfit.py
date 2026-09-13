import unittest

import pandas as pd

from datafaultbench.crossfit import CANDIDATE_COLUMNS, select_candidate


class CrossfitSelectionTests(unittest.TestCase):
    def test_training_only_selection(self):
        rows = []
        for domain in range(14):
            for model, effect in [("a", 0.10), ("b", 0.01)]:
                rows.append({
                    "dataset_id": str(domain), "model": model, "defect_pair": "p",
                    "process": "independent", "severity": "0.10+0.10",
                    "domain_interaction": effect + domain * 0.0001,
                })
        values = pd.DataFrame(rows)
        selected = select_candidate(values, {str(x) for x in range(13)}, 12)
        self.assertEqual(selected["model"], "a")
        self.assertEqual(selected["training_n"], 13)

    def test_lexicographic_tie_break(self):
        rows = []
        for domain in range(12):
            for model in ["b", "a"]:
                rows.append({
                    "dataset_id": str(domain), "model": model, "defect_pair": "p",
                    "process": "independent", "severity": "0.10+0.10",
                    "domain_interaction": 0.01 + domain * 0.001,
                })
        selected = select_candidate(pd.DataFrame(rows), {str(x) for x in range(12)}, 12)
        self.assertEqual(selected["model"], "a")


if __name__ == "__main__":
    unittest.main()
