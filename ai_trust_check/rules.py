"""명세의 R1~R9와 고정점 이후에만 적용하는 R10."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import WorkingMemory
from .facts import Answer, QUESTIONS

TRUSTED = "신뢰 조건 충족"
NEEDS_REVIEW = "추가 검증 필요"
LOW_TRUST = "신뢰도 낮음"


@dataclass(frozen=True)
class Condition:
    fact: str
    accepted: tuple[Answer, ...] = ()

    def matches(self, memory: WorkingMemory) -> bool:
        if self.accepted:
            return memory.initial.get(self.fact) in self.accepted
        return self.fact in memory.derived

    def explain(self, memory: WorkingMemory) -> str:
        if not self.accepted:
            return self.fact
        label = next(q.label for q in QUESTIONS if q.id == self.fact)
        return f"{label} = {memory.initial[self.fact].value}"


@dataclass(frozen=True)
class Rule:
    id: str
    conditions: tuple[Condition, ...]
    conclusion: str
    match_any: bool = False

    def matches(self, memory: WorkingMemory) -> bool:
        results = (c.matches(memory) for c in self.conditions)
        return any(results) if self.match_any else all(results)


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


def fallback_reasons(memory: WorkingMemory) -> tuple[str, ...]:
    """R10 조건 정의. 엔진이 R1~R9 종료 후 호출하며, 사실은 변경하지 않는다."""
    missing = tuple(
        f"{q.label} = {memory.initial[q.id].value}"
        for q in QUESTIONS if memory.initial[q.id] in (Answer.NO, Answer.UNKNOWN)
    )
    if TRUSTED not in memory.derived and LOW_TRUST not in memory.derived and missing:
        return (f"{TRUSTED} 미도출", f"{LOW_TRUST} 미도출") + missing
    return ()
