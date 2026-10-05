"""Trace Tree Reconstruction Module.

Builds dynamic hierarchical span trees from embedded spans using
parent_span_id pointers. Does not hard-code hierarchy structures.
Computes relative timing offsets for timeline bar visualizations.
"""

from typing import Any, Dict, List, Optional


def build_trace_tree(trace: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reconstruct an ordered, indented tree of spans from trace document.
    
    Each span in the returned list receives:
    - depth: Indentation level (0 for root)
    - relative_start_pct: Start offset as a percentage of total trace duration
    - relative_duration_pct: Span duration as a percentage of total trace duration
    - has_children: Boolean flag
    """
    spans = trace.get("spans", [])
    if not spans:
        return []

    total_trace_duration = max(float(trace.get("duration_ms", 1.0)), 1.0)

    # Group spans by parent_span_id
    by_parent: Dict[Optional[str], List[Dict[str, Any]]] = {}
    by_id: Dict[str, Dict[str, Any]] = {}

    for s in spans:
        span_copy = dict(s)
        span_id = span_copy["span_id"]
        parent_id = span_copy.get("parent_span_id")
        by_id[span_id] = span_copy

        if parent_id not in by_parent:
            by_parent[parent_id] = []
        by_parent[parent_id].append(span_copy)

    ordered_spans: List[Dict[str, Any]] = []

    def traverse(parent_id: Optional[str], current_depth: int):
        children = by_parent.get(parent_id, [])
        # Sort children by start_offset_ms
        children.sort(key=lambda x: x.get("start_offset_ms", 0.0))

        for child in children:
            child_id = child["span_id"]
            has_children = bool(by_parent.get(child_id))

            start_offset = float(child.get("start_offset_ms", 0.0))
            duration = float(child.get("duration_ms", 0.0))

            start_pct = round(min((start_offset / total_trace_duration) * 100.0, 100.0), 2)
            duration_pct = round(min(max((duration / total_trace_duration) * 100.0, 1.0), 100.0 - start_pct), 2)

            child["depth"] = current_depth
            child["has_children"] = has_children
            child["relative_start_pct"] = start_pct
            child["relative_duration_pct"] = duration_pct

            ordered_spans.append(child)
            traverse(child_id, current_depth + 1)

    # Begin traversal from root spans (parent_span_id is None or not in trace)
    root_parents = [p for p in by_parent.keys() if p is None or p not in by_id]
    for r_parent in root_parents:
        traverse(r_parent, 0)

    # Include any disconnected spans if any
    seen_ids = {s["span_id"] for s in ordered_spans}
    for s in spans:
        if s["span_id"] not in seen_ids:
            orphan = dict(s)
            orphan["depth"] = 0
            orphan["has_children"] = False
            start_offset = float(orphan.get("start_offset_ms", 0.0))
            duration = float(orphan.get("duration_ms", 0.0))
            orphan["relative_start_pct"] = round(min((start_offset / total_trace_duration) * 100.0, 100.0), 2)
            orphan["relative_duration_pct"] = round(min(max((duration / total_trace_duration) * 100.0, 1.0), 100.0), 2)
            ordered_spans.append(orphan)

    return ordered_spans
