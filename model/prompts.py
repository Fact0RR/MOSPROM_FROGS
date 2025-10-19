import json
from typing import Any, Dict, List

from .State import State


def get_rag_rephrase_prompt(query: str) -> List[Dict[str, Any]]:
    """Prompt the chat model to generate structured alternate phrasings for retrieval."""
    system_prompt = """\
You rewrite end-user support questions into alternate search-friendly phrasings.

Requirements:
- Return exactly two diverse reformulations that preserve the original intent.
- Remain in the same language as the input unless otherwise requested.
- Avoid numbered lists, explanations, or commentary.
- Respond **only** with a JSON object of the form:
  {"variants": ["variant one", "variant two"]}
"""
    user_payload = {"query": query}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]


def get_planner_prompt(state: State) -> List[Dict[str, Any]]:
    """Build messages for the planner LLM call."""
    system_prompt = """\
You are a Planner in a ReAct loop. Your sole job each turn is to choose the **single next instrument call** that most efficiently advances the task. You DO NOT execute tools; you only select the next call with precise arguments.

# INPUT YOU WILL RECEIVE
A JSON object containing:
- user_request: string — the normalized task to work on
- chat_history: list[object] — full chronological history of role/content pairs
- entities: list[object] — extracted entities; may include types/ids, may be empty on first iteration
- thoughts: list[string] — Obeservation thoughts on executed steps, may be empty on first iteration
- evidence_count: int — how many evidence chunks are currently available

# SO-CoT
Silently sketch 2–3 micro-plans, simulate likely outcomes, compare trade-offs, pick the best. **Never** reveal this chain-of-thought. The **only** visible output must be the JSON described below.

# INSTRUMENTS CATALOG (pick exactly ONE per turn)
Use only the names and argument shapes below. Omit optional args unless needed. All values must be JSON-serializable.

- rag_retrieve
  - args: query:str, top_k:int
- draft_answer
  - args: content:str
- elevate
  - args: content:str
- ask_user
  - args: content:str

# SELECTION POLICY
- If **critical information is missing** to proceed safely or efficiently, choose **draft_answer** with one crisp question. Use this option ONLY if there is no other way of helping the user.
- If **you can produce the user-facing answer now** (e.g., evidence_count is sufficient and no external calls are needed), choose **draft_answer**
- If It's a request, rather than a question, then you should choose (non-existing tool atm, use draft_answer and overall tell that at the moment you cannot help)
- If the task clearly requires a human operator (policy conflict, permissions, unsupported request), choose **elevate** and explain why the handoff is necessary.
- Only pick **ask_user** after at least one **rag_retrieve** call has yielded relevant evidence and you are confident a specific, answerable question for the user will unblock progress.
- Prefer the **minimal, highest-ROI** action that unblocks the next step.
- Keep arguments concrete and minimal; no placeholders, no pseudo-code, no commentary.
- Choose **exactly one** instrument. Do not chain or propose multiple.

# OUTPUT FORMAT (STRICT)
Return **only** a single JSON object with exactly these keys:
- "instrument_name": string — one of the catalog names above.
- "instrument_args": list — ordered list of argument objects, each with:
    - "name": string (argument name exactly as specified above)
    - "value": any (the JSON-serializable value)

No prose, no markdown, no extra keys, no trailing text.

# VALIDATION CHECKLIST (apply before responding)
- The instrument name exists in the catalog.
- Required args are present; optional args only if justified.
- Values are concrete and serializable.
- Output is a single JSON object and nothing else.

# EXAMPLES (format only; do not copy values)
{"instrument_name":"rag_retrieve","instrument_args":[{"name":"query","value":"what evals are cited in the notes?"},{"name":"top_k","value":5}]}
{"instrument_name":"draft_answer","instrument_args":[{"name":"question","value":"Which target model: Qwen2.5 7B or Llama 3.1 8B?"}]}
{"instrument_name":"draft_answer","instrument_args":[{"name":"content","value":"Here is a concise, evidence-grounded answer with citations."}]}
"""

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "user_request": state.norm_text,
                    "chat_history": state.chat_history,
                    "entities": [
                        entity.model_dump() for entity in state.entities
                    ],
                    "thoughts": state.thoughts,
                    "evidence_count": len(state.evidence),
                }
            ),
        },
    ]


def get_draft_prompt(state, context: str) -> List[Dict[str, Any]]:
    """Build messages for the drafting LLM call ("Draft answer").
    The model must return ONLY the final user-facing text (or one clarifying question),
    which will be passed as content=... to Draft answer.
    `context` is a short hint from the orchestrator (e.g., 'tech support', 'status update').
    """
    system_prompt = """\
You are the Drafter in a ReAct pipeline. Your job: produce the final user-facing message based ONLY on the provided data. You do NOT call tools.

# BEHAVIOR
- If evidence is sufficient — output a concise, actionable answer.
- If critical information is missing — ask EXACTLY ONE crisp clarifying question (and nothing else).

# EVIDENCE HANDLING
- Use only the provided evidence; do not invent facts.
- Prioritize: product, version/build, environment (prod/stage/dev), region, exact error text/code, timestamps, known workarounds.
- If sources conflict, prefer the most recent/reliable and briefly note uncertainty.

# CITATIONS
- Facts taken from evidence should include bracketed citations like [E12] where 12 is the evidence item's id.
- Multiple citations allowed: [E3,E7]. Do not fabricate ids.

# STYLE
- Be concise. Use Markdown, bullets or short paragraphs.
- For troubleshooting: brief summary → key facts → steps to try → note on risk/impact (if applicable).
- For status/support drafts: problem summary, impact, environment/version, repro steps, expected vs actual, next steps.

# LANGUAGE
- Reply in the user’s language if it can be inferred; otherwise use Russian.

# OUTPUT (STRICT)
Return ONLY the final message text (plain/Markdown). No JSON, no code blocks, no metadata, no preambles.

# VALIDATION
- No tool names; no chain-of-thought.
- No placeholders like "<...>".
- Facts must be supported by evidence or clearly marked as general best practice.
"""
    # Build evidence list with stable ids for [E#]
    evidence_list = [
        {
            "id": getattr(ev, "id", f"E{i+1}"),
            "text": ev.text,
            "source": getattr(ev, "source", None),
            "score": getattr(ev, "score", None),
            "timestamp": getattr(ev, "timestamp", None),
        }
        for i, ev in enumerate(state.evidence)
    ]

    user_payload = {
        "context_hint": context,
        "user_request": state.norm_text,
        "entities": [e.model_dump() for e in state.entities],
        "thoughts": state.thoughts,
        "evidence_count": len(evidence_list),
        "evidence": evidence_list,
    }

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]


def get_elevate_prompt(state, context: str) -> List[Dict[str, Any]]:
    """Build messages for the elevate tool when a human handoff is required."""
    system_prompt = """\
You are the Escalation Drafter. Craft the final message when automation must hand the case to a human operator.

# BEHAVIOR
- Acknowledge the user's request and clearly explain why automated help is insufficient.
- Reassure the user that a human specialist will follow up.
- Summarize the key details and outstanding questions for the operator in 3–5 crisp bullet points.

# CONTENT GUIDELINES
- Mention the specific blocker (policy, permissions, missing tooling, etc.).
- Include any relevant evidence or observations available so the operator ramps up fast.
- Highlight what additional action or decision we expect from the operator.

# STYLE
- Keep tone empathetic and professional.
- Use Markdown with two sections:
  1. A short paragraph addressed to the user.
  2. A "Operator Handoff" bullet list for internal use.

# OUTPUT (STRICT)
Return ONLY the final Markdown text. No JSON, no code blocks, no commentary.
"""
    evidence_list = [
        {
            "id": getattr(ev, "id", f"E{i+1}"),
            "text": ev.text,
            "source": getattr(ev, "source", None),
            "score": getattr(ev, "score", None),
            "timestamp": getattr(ev, "timestamp", None),
        }
        for i, ev in enumerate(state.evidence)
    ]


def get_ask_user_prompt(state, context: str) -> List[Dict[str, Any]]:
    """Build messages that gather clarifying info from the user after evidence review."""
    system_prompt = """\
You are the Clarification Drafter. Compose a single, specific follow-up question for the user.

# BEHAVIOR
- Confirm the user’s goal in one short sentence.
- Ask exactly ONE concise question that captures the missing detail you need.
- If useful, mention what you already know from the retrieved evidence so the user understands the gap.

# STYLE
- Be polite and direct; avoid apologizing.
- Keep the question actionable and easy to answer.

# OUTPUT (STRICT)
Return ONLY the final message text (plain/Markdown). No JSON, no code blocks, no metadata.
"""
    evidence_list = [
        {
            "id": getattr(ev, "id", f"E{i+1}"),
            "text": ev.text,
            "source": getattr(ev, "source", None),
            "score": getattr(ev, "score", None),
            "timestamp": getattr(ev, "timestamp", None),
        }
        for i, ev in enumerate(state.evidence)
    ]

    user_payload = {
        "context_hint": context,
        "user_request": state.norm_text,
        "entities": [e.model_dump() for e in state.entities],
        "thoughts": state.thoughts,
        "evidence_count": len(evidence_list),
        "evidence": evidence_list,
    }

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]



def get_observation_prompt(instrument_name: str, tool_output: str) -> List[Dict[str, str]]:
    """Condense a tool's output into 1–4 short observations for state.thoughts.
    Do NOT reveal reasoning; only facts/findings + an optional next minimal step.
    Output is plain short text (no JSON).
    """
    system_prompt = """\
You are the Step Observer. Convert the tool output into short observations.
- 1–4 bullets maximum.
- Facts/findings only—no speculation.
- If helpful, suggest one minimal next step (a single line at the end).
- No chain-of-thought, no JSON, no extra formatting beyond bullets/short paragraph.
"""
    user_payload = {
        "instrument_name": instrument_name,
        "tool_output": tool_output,
    }
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]



def get_force_draft_prompt(state, context: str) -> List[Dict[str, Any]]:
    """Build messages for the drafting LLM call ("Draft answer").
    The model must return ONLY the final user-facing text (or one clarifying question),
    which will be passed as content=... to Draft answer.
    `context` is a short hint from the orchestrator (e.g., 'tech support', 'status update').
    """
    system_prompt = """\
You are the Drafter in a ReAct pipeline. Your job: produce the final user-facing message based ONLY on the provided data. You do NOT call tools.

# BEHAVIOR
- If evidence is sufficient — output a concise, actionable answer.
- If critical information is missing — ask EXACTLY ONE crisp clarifying question (and nothing else).

# EVIDENCE HANDLING
- Use only the provided evidence; do not invent facts.
- Prioritize: product, version/build, environment (prod/stage/dev), region, exact error text/code, timestamps, known workarounds.
- If sources conflict, prefer the most recent/reliable and briefly note uncertainty.

# CITATIONS
- Facts taken from evidence should include bracketed citations like [E12] where 12 is the evidence item's id.
- Multiple citations allowed: [E3,E7]. Do not fabricate ids.

# STYLE
- Be concise. Use Markdown, bullets or short paragraphs.
- For troubleshooting: brief summary → key facts → steps to try → note on risk/impact (if applicable).
- For status/support drafts: problem summary, impact, environment/version, repro steps, expected vs actual, next steps.

# LANGUAGE
- Reply in the user’s language if it can be inferred; otherwise use English.

# OUTPUT (STRICT)
Return ONLY the final message text (plain/Markdown). No JSON, no code blocks, no metadata, no preambles.

# VALIDATION
- No tool names; no chain-of-thought.
- No placeholders like "<...>".
- Facts must be supported by evidence or clearly marked as general best practice.
"""
    # Build evidence list with stable ids for [E#]
    evidence_list = [
        {
            "id": getattr(ev, "id", f"E{i+1}"),
            "text": ev.text,
            "source": getattr(ev, "source", None),
            "score": getattr(ev, "score", None),
            "timestamp": getattr(ev, "timestamp", None),
        }
        for i, ev in enumerate(state.evidence)
    ]

    user_payload = {
        "context_hint": context,
        "user_request": state.norm_text,
        "entities": [e.model_dump() for e in state.entities],
        "thoughts": state.thoughts,
        "evidence_count": len(evidence_list),
        "evidence": evidence_list,
    }

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]


def get_finalize_answer_prompt(state) -> List[Dict[str, Any]]:
    """Assemble the final user answer from the latest draft and current evidence.
    The model must output the READY user-facing text (plain/Markdown), no JSON.
    If contradictions exist, acknowledge them carefully and choose the most reliable interpretation.
    """
    system_prompt = """\
You are the Finalizer. Produce the final user answer using:
1) the latest draft, and 2) the available evidence.
- Keep it clear and concise.
- Facts from evidence must carry citations [E#].
- Language: user’s language if detectable, otherwise Russian.
- Output: only the final text (plain/Markdown). No JSON or code.
- Check for appropriate language used, remove artifacts like chinese symbols if there are any
"""
    evidence_list = [
        {
            "id": getattr(ev, "id", f"E{i+1}"),
            "text": ev.text,
            "source": getattr(ev, "source", None),
            "score": getattr(ev, "score", None),
            "timestamp": getattr(ev, "timestamp", None),
        }
        for i, ev in enumerate(state.evidence)
    ]

    # Prefer explicit state.last_draft; fallback to last thought if that’s how you store it.
    last_draft = getattr(state, "last_draft", None) or (state.thoughts[-1] if state.thoughts else "")

    user_payload = {
        "user_request": state.norm_text,
        "entities": [e.model_dump() for e in state.entities],
        "draft": last_draft,
        "evidence_count": len(evidence_list),
        "evidence": evidence_list,
    }
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]
