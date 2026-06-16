from pydantic import BaseModel

class MemoryEntry(BaseModel):
    id: str
    content: str
    metadata: dict
    
class ContextBundle(BaseModel):
    content: str
    total_tokens: int

class ContextBudget(BaseModel):
    system_prompt: int
    memory_rag: int
    conversation_history: int
    current_turn: int
    reserved_output: int
