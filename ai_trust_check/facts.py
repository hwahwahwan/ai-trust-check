"""F1~F9 초기 사실, 입력 항목 및 허용 응답 정의."""
from dataclasses import dataclass
from enum import Enum


class Answer(Enum):
    YES = "예"
    NO = "아니오"
    PARTIAL = "일부 일치"
    NA = "해당 없음"
    UNKNOWN = "미확인"


@dataclass(frozen=True)
class Question:
    id: str
    label: str
    prompt: str
    allow_na: bool = False
    allow_partial: bool = False


QUESTIONS = (
    Question("F1", "출처 제시", "답변에 출처가 제시되어 있는가?"),
    Question("F2", "출처 접근 가능", "제시된 출처가 실제로 존재하며 접근 가능한가?"),
    Question("F3", "출처 신뢰성", "공식기관, 공식문서, 논문 등 신뢰할 만한 출처인가?"),
    Question("F4", "AI 주장 뒷받침", "제시된 출처의 실제 내용이 AI의 핵심 주장을 뒷받침하는가?", allow_partial=True),
    Question("F5", "교차검증", "독립적인 다른 자료에서도 같은 내용을 확인할 수 있는가?"),
    Question("F6", "최신성", "최신성이 중요한 질문인 경우, 답변의 정보가 현재 시점에도 유효한가?", True),
    Question("F7", "구체적 사실 근거", "날짜, 통계, 수치 등 구체적인 주장에 확인 가능한 근거가 있는가?", True),
    Question("F8", "내부 일관성", "답변 내부에 서로 모순되는 내용이 없는가?"),
    Question("F9", "불확실성 표시", "불확실한 내용을 사실처럼 단정하지 않고 적절히 표시했는가?", True),
)


def skip_reason(question_id: str, answers: dict[str, Answer]) -> str | None:
    """출처 후속 질문의 선행 조건. 입력과 검증이 같은 기준을 사용한다."""
    if question_id in ("F2", "F3", "F4", "F5") and answers.get("F1") is Answer.NO:
        return "출처가 제시되지 않음"
    if question_id in ("F3", "F4", "F5") and answers.get("F2") is Answer.NO:
        return "출처에 접근할 수 없음"
    return None


def validate_answers(answers: dict[str, Answer]) -> None:
    if set(answers) != {q.id for q in QUESTIONS}:
        raise ValueError("F1~F9의 초기 사실을 모두 입력해야 합니다.")
    for q in QUESTIONS:
        value = answers[q.id]
        if skip_reason(q.id, answers):
            if value is not Answer.UNKNOWN:
                raise ValueError(f"{q.id}는 선행 조건 미충족으로 미확인이어야 합니다.")
            continue
        if (value is Answer.UNKNOWN or not isinstance(value, Answer)
                or (value is Answer.NA and not q.allow_na)
                or (value is Answer.PARTIAL and not q.allow_partial)):
            raise ValueError(f"{q.id}에 허용되지 않은 응답입니다.")
