from typing import TypedDict, List


class PhaseInfo(TypedDict):
    value: str
    allowed: List[str]
    source: str
