import unittest
from frameshift.construct import analyze_text, caesar, caesar_sweep, solve_linear, solve_construct

class LinguisticConstructTests(unittest.TestCase):
    def test_caesar_round_trip(self):
        self.assertEqual(caesar(caesar('National Treasure!', 7), -7), 'National Treasure!')
    def test_caesar_sweep_all_shifts(self):
        self.assertEqual(len(caesar_sweep('ABC')), 25)
        self.assertEqual(caesar_sweep('ABC')[0]['text'], 'BCD')
    def test_line_initials(self):
        out=analyze_text('Find\nEvery\nClue')
        self.assertEqual(out['candidates'][0]['result'], 'FEC')
    def test_word_initials(self):
        out=analyze_text('Hidden clues wait')
        self.assertIn('Hcw', [c['result'] for c in out['candidates']])
    def test_linear_equation(self):
        out=solve_linear('2*(x+3)=14')
        self.assertEqual(out['status'],'solved')
        self.assertAlmostEqual(out['solution'],4)
        self.assertTrue(out['verification']['equal_within_tolerance'])
    def test_no_solution(self): self.assertEqual(solve_linear('x+1=x+2')['status'],'no_solution')
    def test_infinite_solutions(self): self.assertEqual(solve_linear('x+1=1+x')['status'],'infinite_solutions')
    def test_reject_nonlinear(self):
        with self.assertRaises(ValueError): solve_linear('x*x=4')
    def test_reject_code_execution(self):
        with self.assertRaises(ValueError): solve_linear('__import__("os").system("echo bad")=1')
    def test_construct_warns_not_proof(self):
        out=solve_construct('Look\nUnder\nOld stones')
        self.assertIn('not evidence', out['analysis']['warning'])
        self.assertGreaterEqual(len(out['transformation_candidates']), 20)

if __name__ == '__main__': unittest.main()
