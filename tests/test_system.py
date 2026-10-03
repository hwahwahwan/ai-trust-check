import itertools
import subprocess
import sys
import unittest
from unittest.mock import patch

from ai_trust_check.cli import format_result, main
from ai_trust_check.engine import forward_chaining
from ai_trust_check.facts import Answer, QUESTIONS, collect_answers, validate_answers
from ai_trust_check.rules import RULES, TRUSTED, NEEDS_REVIEW, LOW_TRUST, evaluate, final_status


class ReliabilityTests(unittest.TestCase):
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

    def test_invalid_inputs_are_retried(self):
        values = iter(['', 'hello', '0', '3', ' 1 '] + ['1'] * 4 + ['3', '3', '1', '3'])
        errors = []
        answers = collect_answers(lambda _: next(values), errors.append)
        self.assertEqual(len(errors), 4)
        self.assertEqual(answers['F6'], Answer.NA)
        validate_answers(answers)

    def test_invalid_programmatic_facts_are_rejected(self):
        for answers in ({}, self.answers | {'F1': Answer.NA},
                        self.answers | {'F1': True}, self.answers | {'F10': Answer.YES}):
            with self.subTest(answers=answers), self.assertRaises(ValueError):
                evaluate(answers)

    def test_trace_contains_reasons_and_new_facts(self):
        output = format_result(evaluate(self.answers | {'F4': Answer.NO}))
        for expected in ('[초기 사실]', '[Cycle 1]', 'R8 발화', 'AI 주장 뒷받침 = 아니오',
                         '→ 새로운 사실: 명확한 신뢰성 문제 발견', '[생성된 사실]', '최종 결과:\n신뢰도 낮음'):
            self.assertIn(expected, output)

    def test_interrupt_does_not_produce_judgment(self):
        for interruption in (KeyboardInterrupt, EOFError):
            with self.subTest(interruption=interruption), patch('ai_trust_check.cli.collect_answers', side_effect=interruption), patch('builtins.print') as output:
                self.assertEqual(main(), 1)
                self.assertIn('판정하지 않았습니다', output.call_args.args[0])

    def test_module_entrypoint(self):
        process = subprocess.run([sys.executable, '-m', 'ai_trust_check'],
                                 input='1\n' * 9, text=True, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn('최종 결과:\n신뢰 조건 충족', process.stdout)


if __name__ == '__main__':
    unittest.main()
