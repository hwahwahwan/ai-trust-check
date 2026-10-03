"""터미널 실행과 사람이 읽을 수 있는 추론 과정 출력."""
from typing import Callable

from .engine import InferenceResult, evaluate, final_status
from .facts import Answer, QUESTIONS


def collect_answers(
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> dict[str, Answer]:
    answers = {}
    for q in QUESTIONS:
        choices = {"1": Answer.YES, "2": Answer.NO}
        if q.allow_na:
            choices["3"] = Answer.NA
        options = " / ".join(f"{key}={value.value}" for key, value in choices.items())
        while True:
            raw = read(f"{q.id}. {q.prompt} [{options}]: ").strip()
            if raw in choices:
                answers[q.id] = choices[raw]
                break
            write(f"잘못된 입력입니다. {', '.join(choices)} 중 하나를 입력하세요.")
    return answers


def format_result(result: InferenceResult) -> str:
    lines = ["===== 전향추론 시작 =====", "", "[초기 사실]"]
    lines.extend(f"{q.id}. {q.label}: {result.memory.initial[q.id].value}" for q in QUESTIONS)
    cycle = None
    for step in result.trace:
        if step.cycle != cycle:
            cycle = step.cycle
            lines.extend(["", f"[Cycle {cycle}]"])
        lines.extend([f"{step.rule_id} 발화", " + ".join(step.reasons), f"→ 새로운 사실: {step.conclusion}"])
    lines.extend(["", "===== 추론 종료 =====", "", "[생성된 사실]"])
    lines.extend(f"- {step.conclusion}" for step in result.trace)
    lines.extend(["", "발화된 규칙:", " → ".join(step.rule_id for step in result.trace),
                  "", "최종 결과:", final_status(result), "",
                  "사용자가 관찰한 사실과 설정된 규칙에 따른 결과이며, 답변의 절대적 진실을 보증하지 않습니다."])
    return "\n".join(lines)


def main() -> int:
    print("생성형 AI 답변 신뢰성 검증 전문가 시스템")
    print("답변과 출처를 직접 확인한 뒤 입력하세요. API나 자동 사실 확인은 사용하지 않습니다.")
    print("F6·F7·F9만 해당 없음을 허용합니다.")
    print("주의: F4의 아니오는 출처 내용이 주장을 뒷받침하지 않음을 확인했다는 뜻입니다.")
    print("F4 또는 F8을 확인할 수 없다면 Ctrl+C로 중단한 뒤 자료를 확인하세요.\n")
    try:
        answers = collect_answers()
    except (EOFError, KeyboardInterrupt):
        print("\n입력이 중단되어 판정하지 않았습니다.")
        return 1
    print("\n" + format_result(evaluate(answers)))
    return 0
