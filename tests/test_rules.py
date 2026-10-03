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

    def test_reachable_source_states(self):
        # 실제 질문 흐름에서 도달 가능한 출처 상태만 생성한다.
        source_states = [
            (Answer.NO,) + (Answer.UNKNOWN,) * 4,
            (Answer.YES, Answer.NO) + (Answer.UNKNOWN,) * 3,
        ]
        source_states.extend((Answer.YES, Answer.YES, *tail)
                             for tail in itertools.product((Answer.YES, Answer.NO), repeat=3))
        for source in source_states:
            for remaining in itertools.product((Answer.YES, Answer.NO, Answer.NA),
                                               (Answer.YES, Answer.NO, Answer.NA),
                                               (Answer.YES, Answer.NO),
                                               (Answer.YES, Answer.NO, Answer.NA)):
                answers = dict(zip((q.id for q in QUESTIONS), source + remaining))
                with self.subTest(answers=answers):
                    result = evaluate(answers)
                    if answers['F4'] is Answer.NO or answers['F8'] is Answer.NO:
                        expected = LOW_TRUST
                    elif source != (Answer.YES,) * 5 or Answer.NO in remaining:
                        expected = NEEDS_REVIEW
                    else:
                        expected = TRUSTED
                    self.assertEqual(final_status(result), expected)
                    self.assertEqual(len(result.memory.derived & {TRUSTED, NEEDS_REVIEW, LOW_TRUST}), 1)
                    ids = [s.rule_id for s in result.trace]
                    self.assertEqual(len(ids), len(set(ids)))
                    self.assertLessEqual(len(ids), 10)
                    if 'R10' in ids:
                        self.assertEqual(ids[-1], 'R10')

    def test_skipped_source_checks_are_not_counterevidence(self):
        for source in ((Answer.NO,) + (Answer.UNKNOWN,) * 4,
                       (Answer.YES, Answer.NO) + (Answer.UNKNOWN,) * 3):
            answers = self.answers | dict(zip(('F1', 'F2', 'F3', 'F4', 'F5'), source))
            with self.subTest(source=source):
                result = evaluate(answers)
                self.assertEqual(final_status(result), NEEDS_REVIEW)
                self.assertNotIn('R8', [s.rule_id for s in result.trace])
                self.assertNotIn('R9', [s.rule_id for s in result.trace])
                self.assertIn('AI 주장 뒷받침 = 미확인', result.trace[-1].reasons)
                # 출처 미확인과 별개로 실제 내부 모순은 낮은 신뢰도를 뜻한다.
                self.assertEqual(final_status(evaluate(answers | {'F8': Answer.NO})), LOW_TRUST)


if __name__ == '__main__':
    unittest.main()
