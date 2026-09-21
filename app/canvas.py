import json
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal


CanvasAction = Literal["add", "remove", "refresh", "replace"]


@dataclass(frozen=True)
class CanvasCommand:
    action: CanvasAction
    targets: set[str]
    entities: set[str]

BLOCK_FIELDS = {
    "direct_answer": "direct_answer",
    "headline": "headline",
    "headline_grid": "headlines",
    "summary": "summary",
    "chart": "charts",
    "metric_grid": "metrics",
    "company_grid": "companies",
    "insight_list": "insights",
    "evidence": "evidence",
    "news_feed": "news",
    "source_list": "sources",
    "tool_activity": "tool_calls",
}

TARGET_TERMS = {
    "direct_answer": ("answer", "brief", "overview"),
    "headline": ("price", "quote", "headline"),
    "chart": ("chart", "graph", "history", "trend", "performance"),
    "metric_grid": ("metric", "ratio", "valuation", "financials", "numbers"),
    "company_grid": ("company", "companies", "comparison", "compare"),
    "insight_list": ("insight", "analysis", "takeaway"),
    "evidence": ("evidence", "supporting data", "proof"),
    "news_feed": ("news", "headlines", "stories", "live feed"),
    "source_list": ("source", "sources", "citations"),
    "summary": ("summary", "explanation"),
}
ENTITY_NAMES = {
    "apple": "AAPL", "microsoft": "MSFT", "tesla": "TSLA", "nvidia": "NVDA",
    "amazon": "AMZN", "google": "GOOGL", "alphabet": "GOOGL", "meta": "META",
    "paytm": "PAYTM.NS", "reliance": "RELIANCE.NS", "infosys": "INFY.NS", "tcs": "TCS.NS",
}


def detect_canvas_command(question: str, has_canvas: bool) -> CanvasCommand | None:
    if not has_canvas:
        return None
    lowered = " ".join(question.casefold().split())
    action: CanvasAction | None = None
    if re.search(r"\b(remove|hide|delete|take off|clear)\b", lowered):
        action = "remove"
    elif re.search(r"\b(refresh|update|reload)\b", lowered):
        action = "refresh"
    elif re.search(
        r"\b(bring(?:\s+up)?|add|include|append|put on|show .*on (?:the )?screen|also|too|as well|alongside|in addition)\b",
        lowered,
    ):
        action = "add"
    elif re.search(r"\b(replace|swap|change .* to)\b", lowered):
        action = "replace"
    if action is None:
        return None

    targets = {
        block_type
        for block_type, terms in TARGET_TERMS.items()
        if any(term in lowered for term in terms)
    }
    if "compare" in lowered or "comparison" in lowered:
        targets.update({"company_grid", "chart"})
    if "headline" in targets:
        targets.add("headline_grid")
    entities = {ticker for name, ticker in ENTITY_NAMES.items() if name in lowered}
    entities.update(re.findall(r"\b[A-Z]{1,5}(?:\.NS)?\b", question))
    if action == "remove" and entities and not targets:
        targets.update({"headline_grid", "company_grid", "chart"})
    if "everything" in lowered or "entire page" in lowered:
        targets.update(set(BLOCK_FIELDS) - {"source_list", "tool_activity"})
    # Add/refresh/replace may name an entity rather than a component (for
    # example, "bring up Tesla too"). In that case, the generated response's
    # allow-listed blocks become the targets. A targetless remove is rejected.
    return CanvasCommand(action, targets, entities) if targets or action != "remove" else None


def _dedupe(items: list[Any], key) -> list[Any]:
    seen: set[str] = set()
    output: list[Any] = []
    for item in items:
        marker = key(item)
        if marker in seen:
            continue
        seen.add(marker)
        output.append(item)
    return output


def _merge_collection(field: str, current: list[Any], incoming: list[Any]) -> list[Any]:
    keys = {
        "metrics": lambda item: f"{item.get('ticker')}:{item.get('name')}",
        "companies": lambda item: str(item.get("ticker")),
        "news": lambda item: str(item.get("url") or item.get("title")),
        "evidence": lambda item: f"{item.get('claim')}:{item.get('metric')}",
        "sources": lambda item: str(item.get("url")),
        "tool_calls": lambda item: f"{item.get('name')}:{json.dumps(item.get('arguments', {}), sort_keys=True)}",
        "insights": lambda item: str(item),
    }
    return _dedupe([*current, *incoming], keys.get(field, lambda item: json.dumps(item, sort_keys=True)))


def _insert_before_audit(blocks: list[dict[str, Any]], block: dict[str, Any]) -> None:
    index = next(
        (i for i, item in enumerate(blocks) if item.get("type") in {"source_list", "tool_activity"}),
        len(blocks),
    )
    blocks.insert(index, block)


def apply_canvas_command(
    current: dict[str, Any],
    incoming: dict[str, Any] | None,
    action: CanvasAction,
    targets: set[str],
    target_entities: set[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Apply allow-listed block operations without executing model-authored UI code."""
    result = deepcopy(current)
    result.pop("canvas_operations", None)
    presentation = result.get("presentation") or {"layout": "research_dashboard", "blocks": []}
    blocks: list[dict[str, Any]] = presentation.setdefault("blocks", [])
    operations: list[dict[str, Any]] = []
    target_entities = {entity.upper() for entity in (target_entities or set())}

    if action == "remove":
        for block_type in targets:
            field = BLOCK_FIELDS[block_type]
            if target_entities and field == "headline" and result.get(field):
                label = str(result[field].get("label", "")).upper()
                if not any(entity in label for entity in target_entities):
                    continue
            if target_entities and field == "headlines":
                result[field] = [
                    item for item in result.get(field, [])
                    if not any(entity in str(item.get("label", "")).upper() for entity in target_entities)
                ]
                if result[field]:
                    operations.extend(
                        {"operation": "remove", "block_type": block_type, "block_id": "canvas-headline-grid", "target_entity": entity}
                        for entity in sorted(target_entities)
                    )
                    continue
            if target_entities and field == "companies":
                result[field] = [
                    item for item in result.get(field, [])
                    if str(item.get("ticker", "")).upper() not in target_entities
                ]
                if result[field]:
                    operations.extend(
                        {"operation": "remove", "block_type": block_type, "target_entity": entity}
                        for entity in sorted(target_entities)
                    )
                    continue
            if target_entities and field == "charts":
                kept_charts = []
                for chart in result.get("charts", []):
                    chart["series"] = [
                        series for series in chart.get("series", [])
                        if str(series.get("name", "")).upper() not in target_entities
                    ]
                    if chart["series"]:
                        kept_charts.append(chart)
                result[field] = kept_charts
                if kept_charts:
                    chart_blocks = [block for block in blocks if block.get("type") == "chart"]
                    blocks[:] = [block for block in blocks if block.get("type") != "chart"]
                    for index, block in enumerate(chart_blocks[: len(kept_charts)]):
                        block["data_ref"] = f"charts.{index}"
                        _insert_before_audit(blocks, block)
                    operations.extend(
                        {"operation": "remove", "block_type": block_type, "target_entity": entity}
                        for entity in sorted(target_entities)
                    )
                    continue
            result[field] = (
                None if field == "headline"
                else ("" if field in {"direct_answer", "summary"} else [])
            )
            removed = [item for item in blocks if item.get("type") == block_type]
            blocks[:] = [item for item in blocks if item.get("type") != block_type]
            for block in removed:
                operation = {
                    "operation": "remove",
                    "block_type": block_type,
                    "block_id": block.get("id"),
                }
                if target_entities:
                    operation["target_entity"] = next(iter(target_entities))
                operations.append(operation)
        result["presentation"] = presentation
        return result, operations

    if incoming is None:
        return result, operations

    incoming_blocks = (incoming.get("presentation") or {}).get("blocks", [])
    incoming_types = {block.get("type") for block in incoming_blocks}
    if action == "replace":
        for obsolete_type in targets - incoming_types:
            field = BLOCK_FIELDS[obsolete_type]
            result[field] = (
                None if field == "headline"
                else ("" if field in {"direct_answer", "summary"} else [])
            )
            removed = [block for block in blocks if block.get("type") == obsolete_type]
            blocks[:] = [block for block in blocks if block.get("type") != obsolete_type]
            operations.extend(
                {"operation": "remove", "block_type": obsolete_type, "block_id": block.get("id")}
                for block in removed
            )
    effective_targets = targets & incoming_types
    if not effective_targets:
        effective_targets = incoming_types - {
            "direct_answer", "summary", "source_list", "tool_activity"
        }

    for block_type in effective_targets:
        field = BLOCK_FIELDS[block_type]
        old_blocks = [block for block in blocks if block.get("type") == block_type]
        new_blocks = [deepcopy(block) for block in incoming_blocks if block.get("type") == block_type]

        if field == "headline" and action == "add":
            existing_headlines = deepcopy(result.get("headlines") or [])
            if not existing_headlines and result.get("headline"):
                existing_headlines.append(deepcopy(result["headline"]))
            if incoming.get("headline"):
                existing_headlines.append(deepcopy(incoming["headline"]))
            result["headlines"] = _dedupe(
                existing_headlines, lambda item: str(item.get("label", "")).casefold()
            )
            result["headline"] = None
            blocks[:] = [
                block for block in blocks
                if block.get("type") not in {"headline", "headline_grid"}
            ]
            headline_grid = {
                "id": "canvas-headline-grid",
                "type": "headline_grid",
                "data_ref": "headlines",
                "span": "full",
                "variant": "comparison",
            }
            blocks.insert(0, headline_grid)
            incoming_summary = str(incoming.get("summary") or "").strip()
            current_summary = str(result.get("summary") or "").strip()
            if incoming_summary and incoming_summary not in current_summary:
                result["summary"] = f"{current_summary} {incoming_summary}".strip()
            incoming_answer = str(incoming.get("direct_answer") or "").strip()
            current_answer = str(result.get("direct_answer") or "").strip()
            if incoming_answer and incoming_answer not in current_answer:
                result["direct_answer"] = f"{current_answer} {incoming_answer}".strip()
            result["summary_source_ids"] = list(
                dict.fromkeys(
                    [
                        *result.get("summary_source_ids", []),
                        *incoming.get("summary_source_ids", []),
                    ]
                )
            )
            if len(result["headlines"]) > 1:
                result["title"] = "Stock Price Board"
            operations.append(
                {"operation": "add", "block_type": "headline_grid", "block_id": headline_grid["id"]}
            )
            continue
        if field == "headline":
            result[field] = incoming.get(field)
        elif field in {"direct_answer", "summary"}:
            result[field] = incoming.get(field, result.get(field, ""))
            if field == "summary":
                result["summary_source_ids"] = incoming.get("summary_source_ids", [])
        elif field == "charts":
            if action == "add":
                offset = len(result.get("charts", []))
                result["charts"] = [*result.get("charts", []), *incoming.get("charts", [])]
                for block in new_blocks:
                    match = re.fullmatch(r"charts\.(\d+)", block.get("data_ref", ""))
                    if match:
                        block["data_ref"] = f"charts.{offset + int(match.group(1))}"
            else:
                result["charts"] = incoming.get("charts", [])
                blocks[:] = [block for block in blocks if block.get("type") != block_type]
        elif action == "add":
            result[field] = _merge_collection(field, result.get(field, []), incoming.get(field, []))
        else:
            result[field] = deepcopy(incoming.get(field, []))
            blocks[:] = [block for block in blocks if block.get("type") != block_type]

        if field != "charts" or action != "add":
            if old_blocks and action == "add":
                new_blocks = []
        for index, block in enumerate(new_blocks):
            block["id"] = f"canvas-{block_type}-{len(blocks) + index}"
            _insert_before_audit(blocks, block)
        operations.append(
            {
                "operation": action,
                "block_type": block_type,
                "block_id": (old_blocks[0].get("id") if old_blocks else (new_blocks[0].get("id") if new_blocks else None)),
            }
        )
        if field == "insights":
            if action == "add":
                result["insight_citations"] = _dedupe(
                    [
                        *result.get("insight_citations", []),
                        *incoming.get("insight_citations", []),
                    ],
                    lambda item: str(item.get("text")),
                )
            else:
                result["insight_citations"] = incoming.get("insight_citations", [])

    for block_type in ("source_list", "tool_activity"):
        field = BLOCK_FIELDS[block_type]
        result[field] = _merge_collection(field, result.get(field, []), incoming.get(field, []))
        if incoming.get(field) and not any(block.get("type") == block_type for block in blocks):
            candidate = next(
                (deepcopy(block) for block in incoming_blocks if block.get("type") == block_type),
                None,
            )
            if candidate:
                candidate["id"] = f"canvas-{block_type}"
                blocks.append(candidate)

    result["generated_at"] = incoming.get("generated_at", result.get("generated_at"))
    result["presentation"] = presentation
    return result, operations
