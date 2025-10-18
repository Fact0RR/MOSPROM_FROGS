import json
import logging

from .State import EvidenceItem, State, StepAudit
from .initial_text_parsing import extract_entities, normalize_text
from .local_calls import LLM_call
from .prompts import (
    get_draft_prompt,
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


def react_workflow(request_id: int, user_input: str) -> str:
    """Core ReAct entrypoint that orchestrates normalization, entity extraction, and classification."""
    state = State(request_id=request_id, raw_text=user_input)

    normalized_text = normalize_text(user_input)
    state.norm_text = normalized_text

    entities = extract_entities(normalized_text)
    state.entities = _coerce_entities(entities)

    # TODO: Implement classification once intent routing is ready.
    # classification = classify_text(normalized_text, entities)
    # state.intent_label = ...
    # state.intent_conf = ...

    state = _react_loop(state)

    finalize_prompt = get_finalize_answer_prompt(state)
    final_answer = LLM_call(finalize_prompt)
    # TODO: Utilize normalized text, entities, and eventual classification results to decide and execute ReAct steps.
    return final_answer


def _react_loop(state: State) -> None:
    """Placeholder for the ReAct reasoning loop."""
    logger.info("Starting ReAct loop; request_id=%s", state.request_id)

    for _ in range(5):
        # TODO: Fix prompt
        planner_prompt = get_planner_prompt(state)
        plan_raw = LLM_call(planner_prompt)
        plan_data = json.loads(plan_raw)
        instrument_name = plan_data["instrument_name"]
        instrument_args = plan_data.get("instrument_args", {})

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

        if instrument_name == "RAG":
            query_text = instrument_args.get("query", state.norm_text or "")
            top_k = instrument_args.get("top_k", 3)
            rag_items = RAG_tool(query=query_text, top_k=top_k)
            state.evidence.extend(rag_items)
            tool_output = "\n".join(item.text for item in rag_items)
            tool_input_summary = f"query_len={len(query_text)} top_k={top_k}"
            tool_output_summary = f"evidence_items={len(rag_items)}"
        elif instrument_name == "Draft answer":
            context = "\n".join(item.text for item in state.evidence)
            # TODO: Fix prompt
            draft_messages = get_draft_prompt(state, context)
            tool_output = LLM_call(draft_messages)
            state.answer_draft = tool_output
            tool_input_summary = "used current evidence"
            tool_output_summary = f"draft_length={len(tool_output)}"
            logger.info("Generated draft answer; length=%d", len(tool_output))
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
    logger.info("Generated fallback draft answer; length=%d", len(fallback_output))
    return state

