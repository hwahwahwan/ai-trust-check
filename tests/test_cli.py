import subprocess
import sys
import unittest
from unittest.mock import patch

from ai_trust_check.cli import collect_answers, format_result, main
from ai_trust_check.engine import evaluate
from ai_trust_check.facts import Answer, QUESTIONS, validate_answers


class CliTests(unittest.TestCase):
    def setUp(self):
        self.answers = {q.id: Answer.YES for q in QUESTIONS}

    def test_invalid_inputs_are_retried(self):
        values = iter(['', 'hello', '0', '3', ' 1 '] + ['1'] * 4 + ['3', '3', '1', '3'])
        errors = []
        answers = collect_answers(lambda _: next(values), errors.append)
        self.assertEqual(len(errors), 4)
        self.assertEqual(answers['F6'], Answer.NA)
        validate_answers(answers)

    def test_trace_contains_reasons_and_new_facts(self):
        output = format_result(evaluate(self.answers | {'F4': Answer.NO}))
        for expected in ('[초기 사실]', '[Cycle 1]', 'R8 발화', 'AI 주장 뒷받침 = 아니오',
                         '→ 새로운 사실: 명확한 신뢰성 문제 발견', '[생성된 사실]', '최종 결과:\n신뢰도 낮음'):
            self.assertIn(expected, output)

    def test_f4_partial_input_and_output(self):
        values = iter(['1', '1', '1', '3', '1', '1', '1', '1', '3'])
        answers = collect_answers(lambda _: next(values))
        self.assertIs(answers['F4'], Answer.PARTIAL)
        self.assertIn('F4. AI 주장 뒷받침: 일부 일치', format_result(evaluate(answers)))

    def test_interrupt_does_not_produce_judgment(self):
        for interruption in (KeyboardInterrupt, EOFError):
            with self.subTest(interruption=interruption), patch('ai_trust_check.cli.collect_answers', side_effect=interruption), patch('builtins.print') as output:
                self.assertEqual(main(), 1)
                self.assertIn('판정하지 않았습니다', output.call_args.args[0])

    def test_conditional_questions(self):
        cases = [
            (['2', '1', '1', '1', '1'], ['F1', 'F6', 'F7', 'F8', 'F9'], ['F2', 'F3', 'F4', 'F5']),
            (['1', '2', '1', '1', '1', '1'], ['F1', 'F2', 'F6', 'F7', 'F8', 'F9'], ['F3', 'F4', 'F5']),
            (['1', '1', '2', '2', '1', '3', '3', '1', '3'], [q.id for q in QUESTIONS], []),
        ]
        for values, expected_questions, skipped in cases:
            with self.subTest(values=values):
                pending = iter(values)
                asked, notices = [], []

                def read(prompt):
                    asked.append(prompt.split('.')[0])
                    return next(pending)

                answers = collect_answers(read, notices.append)
                self.assertEqual(asked, expected_questions)
                self.assertEqual(len(notices), len(skipped))
                for fact in skipped:
                    self.assertIs(answers[fact], Answer.UNKNOWN)
                validate_answers(answers)
                self.assertEqual(next(pending, None), None)

    def test_module_entrypoint(self):
        process = subprocess.run([sys.executable, '-m', 'ai_trust_check'],
                                 input='1\n' * 9, text=True, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn('최종 결과:\n신뢰 조건 충족', process.stdout)

    def test_main_entrypoint_matches_module_entrypoint(self):
        outputs = []
        for args in (['main.py'], ['-m', 'ai_trust_check']):
            process = subprocess.run([sys.executable, *args], input='1\n' * 9,
                                     text=True, capture_output=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            outputs.append(process.stdout)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == '__main__':
    unittest.main()
