from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Entity(BaseModel):
    type: str = Field(..., description="Entity category, e.g., 'Product', 'Version', 'TicketID'.")
    value: str = Field(..., description="Surface form used in retrieval and templates.")


class EvidenceItem(BaseModel):
    doc_id: str = Field(..., description="Source document identifier (URL/path/UUID).")
    chunk_id: str = Field(..., description="Chunk identifier within the source document.")
    text: str = Field(..., description="Retrieved text chunk used as LLM context.")
    score: float = Field(..., description="Retriever/re-ranker score; higher is better.")


class StepAudit(BaseModel):
    n: int = Field(..., description="Sequential step index within the ReAct loop.")
    tool: str = Field(..., description="Instrument name invoked at this step.")
    input_summary: str = Field(..., description="Brief, safe summary of tool input.")
    output_summary: str = Field(..., description="Brief, safe summary of tool output.")


class State(BaseModel):
    request_id: int = Field(..., description="Stable ID to correlate logs, retries, and tool calls.")
    raw_text: str = Field(..., description="Original user message for audit and replay.")
    chat_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Full chat transcript with role/content pairs for planner context.",
    )
    norm_text: Optional[str] = Field(None, description="Optionally normalized text used by tools.")
    intent_label: Optional[str] = Field(None, description="Classifier's primary label for routing (e.g., 'billing').")
    intent_conf: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence for intent_label in [0,1].")
    entities: List[Entity] = Field(default_factory=list, description="NER anchors extracted from the request.")
    search_query: Optional[str] = Field(None, description="Canonical query string used by the retriever.")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Top-K grounding snippets for synthesis.")
    steps: List[StepAudit] = Field(default_factory=list, description="Action/observation audit for the ReAct loop.")
    answer_draft: Optional[str] = Field(None, description="First-pass synthesized answer before checks.")
    thoughts: List[str] = Field(default_factory=list, description="Intermediate observations captured during ReAct.")
    support_needed: bool = Field(False, description="True when automation escalates to a human operator.")
    rag_used: bool = Field(False, description="True once a retrieval step has executed in this session.")
    finalize_required: bool = Field(True, description="False when the current draft should be returned as-is.")
