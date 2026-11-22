import unittest
from frameshift.asymmetric import solve

class AsymmetricAbductionTests(unittest.TestCase):
    def test_explicit_line_initial_clue_surfaces_solution(self):
        r = solve('Find\nEvery\nClue', clue='Take the first letter of each line', expected='FEC')
        self.assertEqual(r['status'], 'candidate_found')
        self.assertEqual(r['supported'][0]['operation'], 'line-initials')
        self.assertEqual(r['supported'][0]['result'], 'FEC')

    def test_no_clue_does_not_promote_matching_answer(self):
        r = solve('Find\nEvery\nClue', expected='FEC')
        self.assertNotIn('line-initials', [h['operation'] for h in r['supported']])
        self.assertTrue(any(h['status'] == 'target_match_without_clue' for h in r['hypotheses']))

    def test_word_initials_clue(self):
        r = solve('Hidden clues wait', clue='Use the initials of each word', expected='HCW')
        found = [h for h in r['supported'] if h['operation'] == 'word-initials']
        self.assertEqual(found[0]['result'], 'HCW')

    def test_ambiguous_phonetic_boundary_keeps_both_readings(self):
        r = solve('I scream, you scream, we all scream for ice cream', clue='Listen for a sound-alike and word boundary')
        h = [x for x in r['hypotheses'] if x['operation'] == 'phonetic-boundary']
        self.assertTrue(h)
        self.assertEqual(h[0]['status'], 'supported_candidate')
        self.assertIn('I scream', h[0]['result']['reading_a'])
        self.assertIn('ice cream', h[0]['result']['reading_b'])

    def test_unconstrained_input_remains_underdetermined(self):
        r = solve('The old map remembers nothing')
        self.assertEqual(r['status'], 'underdetermined')
        self.assertTrue(all(h['status'] != 'supported_candidate' for h in r['hypotheses']))

    def test_attack_penalizes_unjustified_caesar_sweep(self):
        r = solve('Khoor Zruog')
        caesar_rows = [h for h in r['hypotheses'] if h['operation'] == 'caesar']
        self.assertTrue(caesar_rows)
        self.assertTrue(all(h['status'] != 'supported_candidate' for h in caesar_rows))

if __name__ == '__main__': unittest.main()
