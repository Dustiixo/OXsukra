import tempfile, unittest
from pathlib import Path
from frameshift.junkrat import JunkratLab, report_markdown

class JunkratLabTests(unittest.TestCase):
    def test_three_rounds_fold_back_30_records(self):
        root=Path(__file__).resolve().parents[1]
        r=JunkratLab(3).run(root)
        self.assertEqual(r["total_attack_records"], 30)
        self.assertEqual(r["rounds"], 3)
        self.assertEqual(len(r["attacks"]), 10)
        self.assertIn("arbitrary generated code", r["safety_boundary"])

    def test_round_budget_is_bounded(self):
        with self.assertRaises(ValueError): JunkratLab(6)
        with self.assertRaises(ValueError): JunkratLab(0)

    def test_markdown_report_contains_each_attack(self):
        root=Path(__file__).resolve().parents[1]
        md=report_markdown(JunkratLab(2).run(root))
        self.assertIn("Junkrat Recursive Attack Lab", md)
        self.assertIn("consensus-laundering", md)
        self.assertIn("Next moves", md)

if __name__ == "__main__": unittest.main()
