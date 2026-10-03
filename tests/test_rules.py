import itertools
import unittest

from ai_trust_check.engine import evaluate, final_status
from ai_trust_check.facts import Answer, QUESTIONS
from ai_trust_check.rules import TRUSTED, NEEDS_REVIEW, LOW_TRUST


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.answers = {q.id: Answer.YES for q in QUESTIONS}

    def test_required_scenarios(self):
        scenarios = [({}, TRUSTED), ({'F5': Answer.NO}, NEEDS_REVIEW),
                     ({'F4': Answer.NO}, LOW_TRUST), ({'F8': Answer.NO}, LOW_TRUST),
                     ({'F6': Answer.NA}, TRUSTED), ({'F7': Answer.NA}, TRUSTED),
                     ({'F9': Answer.NA}, TRUSTED)]
        for changes, expected in scenarios:
            with self.subTest(changes=changes):
                self.assertEqual(final_status(evaluate(self.answers | changes)), expected)

    def test_all_1728_valid_inputs_have_one_correct_result_and_terminate(self):
        choices = [(Answer.YES, Answer.NO, Answer.NA) if q.allow_na else
                   (Answer.YES, Answer.NO) for q in QUESTIONS]
        for values in itertools.product(*choices):
            answers = dict(zip((q.id for q in QUESTIONS), values))
            with self.subTest(values=values):
                result = evaluate(answers)
                expected = LOW_TRUST if answers['F4'] is Answer.NO or answers['F8'] is Answer.NO else (
                    NEEDS_REVIEW if Answer.NO in values else TRUSTED)
                self.assertEqual(final_status(result), expected)
                self.assertEqual(len(result.memory.derived & {TRUSTED, NEEDS_REVIEW, LOW_TRUST}), 1)
                ids = [s.rule_id for s in result.trace]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertLessEqual(len(ids), 10)
                if 'R10' in ids:
                    self.assertEqual(ids[-1], 'R10')


if __name__ == '__main__':
    unittest.main()
