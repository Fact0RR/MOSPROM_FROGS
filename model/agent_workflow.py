import json
import logging
from typing import Any, Dict, Mapping, Sequence

from .State import EvidenceItem, State, StepAudit
from .initial_text_parsing import extract_entities, normalize_text
from .local_calls import LLM_call
from .prompts import (
    get_draft_prompt,
    get_ask_user_prompt,
    get_elevate_prompt,
    get_force_draft_prompt,
    get_finalize_answer_prompt,
    get_observation_prompt,
    get_planner_prompt,
)
from .tools import RAG_tool

logger = logging.getLogger(__name__)


def _coerce_entities(raw_entities):
    """Normalize entity + type lists into State.Entity-compatible dictionaries."""
    normalized = []
    values, types = raw_entities
    if not values or not types:
        return normalized

    for value, ent_type in zip(values, types):
        normalized.append({"type": str(ent_type), "value": str(value)})
    return normalized


def react_workflow(request_id: int, messages: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    """Core ReAct entrypoint that orchestrates normalization, entity extraction, and classification."""
    if not messages:
        raise ValueError("messages payload must include at least one entry.")

    chat_history = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            raise ValueError(f"Invalid chat message payload: {message!r}")
        chat_history.append({"role": role, "content": content})

    last_user_message = next(
        (entry["content"] for entry in reversed(chat_history) if entry["role"] == "user"),
        None,
    )
    if last_user_message is None:
        raise ValueError("messages payload must include at least one user message.")

    state = State(request_id=request_id, raw_text=last_user_message, chat_history=chat_history)

    normalized_text = normalize_text(last_user_message)
    state.norm_text = normalized_text

    entities = extract_entities(normalized_text)
    state.entities = _coerce_entities(entities)

    # TODO: Implement classification once intent routing is ready.
    # classification = classify_text(normalized_text, entities)
    # state.intent_label = ...
    # state.intent_conf = ...

    state = _react_loop(state)

    if not state.finalize_required:
        final_answer = state.answer_draft or ""
    else:
        finalize_prompt = get_finalize_answer_prompt(state)
        final_answer = LLM_call(finalize_prompt)

    return {
        "message": final_answer,
        "is_support_needed": state.support_needed,
    }


def _react_loop(state: State) -> None:
    """Placeholder for the ReAct reasoning loop."""
    logger.info("Starting ReAct loop; request_id=%s", state.request_id)

    for _ in range(5):
        # TODO: Fix prompt
        planner_prompt = get_planner_prompt(state)
        plan_raw = LLM_call(planner_prompt)
        plan_data = json.loads(plan_raw)
        instrument_name = plan_data["instrument_name"]
        instrument_args_raw = plan_data.get("instrument_args", {})

        if isinstance(instrument_args_raw, list):
            instrument_args = {
                arg.get("name"): arg.get("value") for arg in instrument_args_raw if isinstance(arg, dict)
            }
        elif isinstance(instrument_args_raw, dict):
            instrument_args = instrument_args_raw
        else:
            instrument_args = {}

        normalized_instrument = (instrument_name or "").strip().lower().replace(" ", "_")

        state.steps.append(
            StepAudit(
                n=len(state.steps) + 1,
                tool="Plan",
                input_summary="single iteration",
                output_summary=f"instrument={instrument_name}",
            )
        )
        logger.info("Planner selected instrument=%s args=%s", instrument_name, instrument_args)

        tool_output = ""
        tool_input_summary = ""
        tool_output_summary = ""
        should_return = False

        if normalized_instrument in {"rag", "rag_retrieve"}:
            query_text = instrument_args.get("query", state.norm_text or "")
            top_k = instrument_args.get("top_k", 3)
            rag_items = RAG_tool(query=query_text, top_k=top_k)
            state.evidence.extend(rag_items)
            if rag_items:
                state.rag_used = True
            tool_output = "\n".join(item.text for item in rag_items)
            tool_input_summary = f"query_len={len(query_text)} top_k={top_k}"
            tool_output_summary = f"evidence_items={len(rag_items)}"
        elif normalized_instrument in {"draft", "draft_answer"}:
            context = "\n".join(item.text for item in state.evidence)
            # TODO: Fix prompt
            draft_messages = get_draft_prompt(state, context)
            tool_output = LLM_call(draft_messages)
            state.answer_draft = tool_output
            state.finalize_required = True
            tool_input_summary = "used current evidence"
            tool_output_summary = f"draft_length={len(tool_output)}"
            logger.info("Generated draft answer; length=%d", len(tool_output))
            should_return = True
        elif normalized_instrument == "elevate":
            context = "\n".join(item.text for item in state.evidence)
            elevate_messages = get_elevate_prompt(state, context)
            tool_output = LLM_call(elevate_messages)
            state.answer_draft = tool_output
            state.support_needed = True
            state.finalize_required = False
            tool_input_summary = "handoff initiated"
            tool_output_summary = f"escalate_length={len(tool_output)}"
            logger.info("Generated elevate message; length=%d", len(tool_output))
            should_return = True
        elif normalized_instrument == "ask_user":
            if not state.rag_used or not state.evidence:
                tool_output = "ask_user skipped: requires prior RAG evidence before querying the user."
                tool_input_summary = "missing_rag_context"
                tool_output_summary = "ask_user_blocked"
                logger.warning(
                    "Planner attempted ask_user without prior relevant RAG; rag_used=%s evidence=%d",
                    state.rag_used,
                    len(state.evidence),
                )
            else:
                context = "\n".join(item.text for item in state.evidence)
                ask_messages = get_ask_user_prompt(state, context)
                tool_output = LLM_call(ask_messages)
                state.answer_draft = tool_output
                state.finalize_required = False
                tool_input_summary = "needs_user_detail"
                tool_output_summary = f"ask_length={len(tool_output)}"
                logger.info("Generated ask_user prompt; length=%d", len(tool_output))
                should_return = True
        else:
            tool_output = ""
            tool_input_summary = "unrecognized instrument"
            tool_output_summary = f"instrument={instrument_name}"

        state.steps.append(
            StepAudit(
                n=len(state.steps) + 1,
                tool=instrument_name or "",
                input_summary=tool_input_summary,
                output_summary=tool_output_summary,
            )
        )

        observation_prompt = get_observation_prompt(instrument_name, tool_output)
        observation_text = LLM_call(observation_prompt)
        state.thoughts.append(observation_text)

        state.steps.append(
            StepAudit(
                n=len(state.steps) + 1,
                tool="Observation",
                input_summary=f"instrument={instrument_name}",
                output_summary=f"thought_length={len(observation_text)}",
            )
        )
        logger.info("Recorded observation; length=%d", len(observation_text))

        if should_return:
            return state

    context = "\n".join(item.text for item in state.evidence)
    # TODO: Fix prompt
    force_prompt = get_force_draft_prompt(state, context)
    fallback_output = LLM_call(force_prompt)
    state.answer_draft = fallback_output
    state.finalize_required = True
    logger.info("Generated fallback draft answer; length=%d", len(fallback_output))
    return state
