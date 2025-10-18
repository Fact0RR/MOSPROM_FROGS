import json
import logging
import re
import unicodedata
from itertools import zip_longest
from typing import List, Mapping, Sequence, Tuple

from .local_calls import LLM_call

logger = logging.getLogger(__name__)


def normalize_text(raw_text: str) -> str:
    """Normalize raw user text for downstream processing."""
    text = raw_text
    total_changes = 0

    # Pass 1: Newlines & whitespace canon
    whitespace_replacements = 0
    crlf_count = text.count("\r\n")
    if crlf_count:
        text = text.replace("\r\n", "\n")
        whitespace_replacements += crlf_count
    cr_count = text.count("\r")
    if cr_count:
        text = text.replace("\r", "\n")
        whitespace_replacements += cr_count

    space_like_chars = {
        "\u00A0",
        "\u1680",
        "\u2000",
        "\u2001",
        "\u2002",
        "\u2003",
        "\u2004",
        "\u2005",
        "\u2006",
        "\u2007",
        "\u2008",
        "\u2009",
        "\u200A",
        "\u202F",
        "\u205F",
        "\u3000",
    }
    replacements = sum(1 for ch in text if ch in space_like_chars)
    if replacements:
        translation_table = str.maketrans({ch: " " for ch in space_like_chars})
        text = text.translate(translation_table)
        whitespace_replacements += replacements

    text, collapsed_spaces = re.subn(r"[ \t]{2,}", " ", text)
    whitespace_replacements += collapsed_spaces

    text, collapsed_newlines = re.subn(r"\n{3,}", "\n\n", text)
    whitespace_replacements += collapsed_newlines

    logger.info("normalize_text pass=%s replacements=%d", "whitespace", whitespace_replacements)
    total_changes += whitespace_replacements

    # Pass 2: Unicode normalization (NFC)
    normalized = unicodedata.normalize("NFC", text)
    unicode_replacements = sum(1 for a, b in zip_longest(text, normalized) if a != b)
    text = normalized
    logger.info("normalize_text pass=%s replacements=%d", "unicode_nfc", unicode_replacements)
    total_changes += unicode_replacements

    # Pass 3: Strip invisible/control characters
    control_chars = {
        "\u200B",  # zero width space
        "\u200C",  # zero width non-joiner
        "\u200D",  # zero width joiner
        "\u00AD",  # soft hyphen
        "\uFEFF",  # zero width no-break space (BOM)
        "\u202A",  # LRE
        "\u202B",  # RLE
        "\u202C",  # PDF
        "\u202D",  # LRO
        "\u202E",  # RLO
        "\u2066",  # LRI
        "\u2067",  # RLI
        "\u2068",  # FSI
        "\u2069",  # PDI
    }
    control_replacements = sum(1 for ch in text if ch in control_chars)
    if control_replacements:
        text = "".join(ch for ch in text if ch not in control_chars)
    logger.info("normalize_text pass=%s replacements=%d", "strip_controls", control_replacements)
    total_changes += control_replacements

    # Pass 4: Punctuation normalization
    punct_map = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201A": "'",
        "\u201B": "'",
        "\u201C": '"',
        "\u201D": '"',
        "\u201E": '"',
        "\u201F": '"',
        "\u2032": "'",
        "\u2033": '"',
        "\u2034": '"',
        "\u2035": "'",
        "\u2036": '"',
        "\u2037": '"',
        "\u2026": "...",
        "\u2010": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
        "\uFF01": "!",
        "\uFF02": '"',
        "\uFF03": "#",
        "\uFF04": "$",
        "\uFF05": "%",
        "\uFF06": "&",
        "\uFF07": "'",
        "\uFF08": "(",
        "\uFF09": ")",
        "\uFF0A": "*",
        "\uFF0C": ",",
        "\uFF0D": "-",
        "\uFF0E": ".",
        "\uFF0F": "/",
        "\uFF1A": ":",
        "\uFF1B": ";",
        "\uFF1F": "?",
        "\uFF20": "@",
        "\uFF3B": "[",
        "\uFF3D": "]",
        "\uFF3F": "_",
        "\uFF5B": "{",
        "\uFF5D": "}",
    }
    punct_replacements = 0
    output_chars: List[str] = []
    for ch in text:
        if ch in punct_map:
            output_chars.append(punct_map[ch])
            punct_replacements += 1
        else:
            output_chars.append(ch)
    text = "".join(output_chars)
    logger.info("normalize_text pass=%s replacements=%d", "punct_norm", punct_replacements)
    total_changes += punct_replacements

    # Pass 5: Digit normalization
    digit_replacements = 0
    normalized_chars: List[str] = []
    for ch in text:
        if "0" <= ch <= "9":
            normalized_chars.append(ch)
            continue
        try:
            digit_value = unicodedata.digit(ch)
        except (TypeError, ValueError):
            normalized_chars.append(ch)
        else:
            normalized_chars.append(str(digit_value))
            digit_replacements += 1
    text = "".join(normalized_chars)
    logger.info("normalize_text pass=%s replacements=%d", "digit_norm", digit_replacements)
    total_changes += digit_replacements

    # Pass 6: Mild repetition smoothing
    repetition_counts = {"punct": 0, "letters": 0}

    def _limit_punct(match: re.Match) -> str:
        original = match.group(0)
        char = match.group(1)
        limited = char * 2
        repetition_counts["punct"] += len(original) - len(limited)
        return limited

    text = re.sub(r"([!?])\1{2,}", _limit_punct, text)

    def _limit_letters(match: re.Match) -> str:
        char = match.group(1)
        original = match.group(0)
        limited = char * 2
        repetition_counts["letters"] += len(original) - len(limited)
        return limited

    text = re.sub(r"([A-Za-z])\1{2,}", _limit_letters, text)

    repetition_replacements = repetition_counts["punct"] + repetition_counts["letters"]
    logger.info("normalize_text pass=%s replacements=%d", "repetition_smooth", repetition_replacements)
    total_changes += repetition_replacements

    logger.info("normalize_text pass=%s total_changes=%d", "done", total_changes)
    return text


def extract_entities(text: str) -> Tuple[List[str], List[str]]:
    """Extract named entities and their types from normalized text."""
    system_instructions = """You are an information extraction assistant.
Given user-provided text, identify salient named entities such as people,
organizations, locations, products, dates, or other proper nouns.
Return a JSON array where each object contains the keys "Named entities:" and "Entity type", both strings.
If no entities are present, return an empty JSON array."""
    user_prompt = f"Text:\n{text}"
    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_prompt},
    ]

    logger.info("extract_entities submitting text to LLM; length=%d", len(text))
    try:
        llm_response = LLM_call(messages)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("LLM_call failed during entity extraction: %s", exc)
        return ([], [])

    candidate_response = llm_response
    fenced_match = re.search(r"```json\s*(.+?)\s*```", llm_response, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        candidate_response = fenced_match.group(1)

    try:
        parsed_payload = json.loads(candidate_response)
    except json.JSONDecodeError:
        logger.error("NER did not return a correct output")
        return ([], [])

    if isinstance(parsed_payload, Mapping):
        parsed_payload = [parsed_payload]
    if not isinstance(parsed_payload, Sequence) or isinstance(parsed_payload, (str, bytes)):
        logger.error("NER did not return a correct output")
        return ([], [])

    entity_names: List[str] = []
    entity_types: List[str] = []
    for item in parsed_payload:
        if not isinstance(item, Mapping):
            logger.error("NER did not return a correct output")
            return ([], [])
        try:
            name = item["Named entities:"]
            entity_type = item["Entity type"]
        except KeyError:
            logger.error("NER did not return a correct output")
            return ([], [])
        if not isinstance(name, str) or not isinstance(entity_type, str):
            logger.error("NER did not return a correct output")
            return ([], [])
        entity_names.append(name.strip())
        entity_types.append(entity_type.strip())

    logger.info("extract_entities parsed entities successfully; count=%d", len(entity_names))
    return (entity_names, entity_types)


def classify_text(text: str, entities: Tuple[List[str], List[str]]) -> str:
    """Classify normalized text using contextual entity information."""
    pass
