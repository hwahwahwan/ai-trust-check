"""규칙 데이터와 Working Memory를 분리한 전향추론 엔진."""
from dataclasses import dataclass, field
from .facts import Answer, validate_answers
from .rules import RULES, LOW_TRUST, TRUSTED, NEEDS_REVIEW, Rule, fallback_reasons


@dataclass
class WorkingMemory:
    initial: dict[str, Answer]
    derived: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class TraceStep:
    cycle: int
    rule_id: str
    reasons: tuple[str, ...]
    conclusion: str


@dataclass
class InferenceResult:
    memory: WorkingMemory
    trace: list[TraceStep]


def forward_chaining(initial: dict[str, Answer], rules: tuple[Rule, ...]) -> InferenceResult:
    validate_answers(initial)
    memory = WorkingMemory(dict(initial))
    trace = []
    fired = set()
    cycle = 1
    while True:
        # 이번 cycle 시작 시점의 사실로 판단한다. 새 사실은 다음 cycle에서 사용한다.
        applicable = [r for r in rules if r.id not in fired and r.matches(memory)]
        if not applicable:
            break
        steps = [TraceStep(cycle, r.id,
                           tuple(c.explain(memory) for c in r.conditions if c.matches(memory)),
                           r.conclusion) for r in applicable]
        for rule, step in zip(applicable, steps):
            fired.add(rule.id)
            if rule.conclusion not in memory.derived:
                memory.derived.add(rule.conclusion)
                trace.append(step)
        cycle += 1
    return InferenceResult(memory, trace)


def evaluate(answers: dict[str, Answer]) -> InferenceResult:
    result = forward_chaining(answers, RULES)
    # 부정 조건을 사용하는 R10은 R1~R9가 고정점에 도달한 뒤 별도로 평가한다.
    reasons = fallback_reasons(result.memory)
    if reasons:
        cycle = max((step.cycle for step in result.trace), default=0) + 1
        result.memory.derived.add(NEEDS_REVIEW)
        result.trace.append(TraceStep(cycle, "R10", reasons, NEEDS_REVIEW))
    return result


def final_status(result: InferenceResult) -> str:
    for status in (LOW_TRUST, TRUSTED, NEEDS_REVIEW):
        if status in result.memory.derived:
            return status
    raise ValueError("최종 상태가 없습니다. evaluate() 결과를 사용하세요.")
