"""F1~F9 초기 사실, 입력 항목 및 허용 응답 정의."""
from dataclasses import dataclass
from enum import Enum


class Answer(Enum):
    YES = "예"
    NO = "아니오"
    NA = "해당 없음"


@dataclass(frozen=True)
class Question:
    id: str
    label: str
    prompt: str
    allow_na: bool = False


QUESTIONS = (
    Question("F1", "출처 제시", "답변에 출처가 제시되어 있는가?"),
    Question("F2", "출처 접근 가능", "제시된 출처가 실제로 존재하며 접근 가능한가?"),
    Question("F3", "출처 신뢰성", "공식기관, 공식문서, 논문 등 신뢰할 만한 출처인가?"),
    Question("F4", "AI 주장 뒷받침", "출처의 실제 내용이 AI의 주장을 뒷받침하는가?"),
    Question("F5", "교차검증", "독립적인 다른 자료에서도 같은 내용을 확인할 수 있는가?"),
    Question("F6", "최신성", "최신성이 필요한 정보라면 최신 자료를 사용했는가?", True),
    Question("F7", "구체적 사실 근거", "날짜, 통계, 수치 등 구체적인 주장에 확인 가능한 근거가 있는가?", True),
    Question("F8", "내부 일관성", "답변 내부에 서로 모순되는 내용이 없는가?"),
    Question("F9", "불확실성 표시", "불확실한 내용을 사실처럼 단정하지 않고 적절히 표시했는가?", True),
)


def validate_answers(answers: dict[str, Answer]) -> None:
    if set(answers) != {q.id for q in QUESTIONS}:
        raise ValueError("F1~F9의 초기 사실을 모두 입력해야 합니다.")
    for q in QUESTIONS:
        value = answers[q.id]
        if not isinstance(value, Answer) or (value is Answer.NA and not q.allow_na):
            raise ValueError(f"{q.id}에 허용되지 않은 응답입니다.")
