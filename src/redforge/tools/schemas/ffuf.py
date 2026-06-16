from pydantic import BaseModel
from typing import List, Optional
from .base import BaseToolOutput

class FfufMatch(BaseModel):
    url: str
    status: int
    length: int
    words: int

class FfufResult(BaseToolOutput):
    tool_name: str = "ffuf"
    matches: List[FfufMatch]
