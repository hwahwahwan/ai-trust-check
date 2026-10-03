import unittest

from ai_trust_check.engine import evaluate, final_status, forward_chaining
from ai_trust_check.facts import Answer, QUESTIONS
from ai_trust_check.rules import RULES, TRUSTED


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.answers = {q.id: Answer.YES for q in QUESTIONS}

    def test_chain_uses_previous_cycles_even_when_rules_reversed(self):
        result = forward_chaining(self.answers, tuple(reversed(RULES)))
        cycles = {s.rule_id: s.cycle for s in result.trace}
        self.assertLess(cycles['R1'], cycles['R2'])
        self.assertLess(cycles['R2'], cycles['R3'])
        self.assertLess(cycles['R3'], cycles['R6'])
        self.assertLess(cycles['R6'], cycles['R7'])
        self.assertEqual(final_status(result), TRUSTED)
        self.assertEqual(set(self.answers), {q.id for q in QUESTIONS})
        self.assertIsNot(result.memory.initial, self.answers)

    def test_fallback_runs_only_after_other_rules(self):
        result = evaluate(self.answers | {'F9': Answer.NO})
        self.assertEqual(result.trace[-1].rule_id, 'R10')
        self.assertGreater(result.trace[-1].cycle, max(s.cycle for s in result.trace[:-1]))
        self.assertIn('사실적 신뢰성 높음', result.memory.derived)
        self.assertNotIn('R10', [s.rule_id for s in evaluate(self.answers).trace])

    def test_invalid_programmatic_facts_are_rejected(self):
        for answers in ({}, self.answers | {'F1': Answer.NA},
                        self.answers | {'F1': True}, self.answers | {'F10': Answer.YES}):
            with self.subTest(answers=answers), self.assertRaises(ValueError):
                evaluate(answers)


if __name__ == '__main__':
    unittest.main()
