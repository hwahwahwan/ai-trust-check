"""규칙 데이터와 Working Memory를 분리한 전향추론 엔진."""
from dataclasses import dataclass, field
from .facts import Answer, QUESTIONS, validate_answers


@dataclass
class WorkingMemory:
    initial: dict[str, Answer]
    derived: set[str] = field(default_factory=set)


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
