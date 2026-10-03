"""명세의 R1~R9와 고정점 이후에만 적용하는 R10."""
from .engine import Condition, Rule, TraceStep, InferenceResult, forward_chaining
from .facts import Answer, QUESTIONS

TRUSTED = "신뢰 조건 충족"
NEEDS_REVIEW = "추가 검증 필요"
LOW_TRUST = "신뢰도 낮음"


def yes(fact: str) -> Condition:
    return Condition(fact, (Answer.YES,))


def neutral_or_yes(fact: str) -> Condition:
    return Condition(fact, (Answer.YES, Answer.NA))


RULES = (
    Rule("R1", (yes("F1"), yes("F2")), "출처 추적 가능"),
    Rule("R2", (Condition("출처 추적 가능"), yes("F3"), yes("F4")), "인용 근거 유효"),
    Rule("R3", (Condition("인용 근거 유효"), yes("F5")), "외부 근거 검증 완료"),
    Rule("R4", (neutral_or_yes("F6"), neutral_or_yes("F7")), "사실 정보 검증 완료"),
    Rule("R5", (yes("F8"), neutral_or_yes("F9")), "답변 자체 신뢰성 확보"),
    Rule("R6", (Condition("외부 근거 검증 완료"), Condition("사실 정보 검증 완료")), "사실적 신뢰성 높음"),
    Rule("R7", (Condition("사실적 신뢰성 높음"), Condition("답변 자체 신뢰성 확보")), TRUSTED),
    Rule("R8", (Condition("F4", (Answer.NO,)), Condition("F8", (Answer.NO,))), "명확한 신뢰성 문제 발견", match_any=True),
    Rule("R9", (Condition("명확한 신뢰성 문제 발견"),), LOW_TRUST),
)


def evaluate(answers: dict[str, Answer]) -> InferenceResult:
    result = forward_chaining(answers, RULES)
    # 부정 조건을 사용하는 R10은 R1~R9가 고정점에 도달한 뒤 별도로 평가한다.
    missing = tuple(f"{q.label} = 아니오" for q in QUESTIONS if answers[q.id] is Answer.NO)
    if TRUSTED not in result.memory.derived and LOW_TRUST not in result.memory.derived and missing:
        reasons = (f"{TRUSTED} 미도출", f"{LOW_TRUST} 미도출") + missing
        cycle = max((step.cycle for step in result.trace), default=0) + 1
        result.memory.derived.add(NEEDS_REVIEW)
        result.trace.append(TraceStep(cycle, "R10", reasons, NEEDS_REVIEW))
    return result


def final_status(result: InferenceResult) -> str:
    for status in (LOW_TRUST, TRUSTED, NEEDS_REVIEW):
        if status in result.memory.derived:
            return status
    raise ValueError("최종 상태가 없습니다. evaluate() 결과를 사용하세요.")
