import re
from typing import List, Optional, Dict, Any

from app.models.schemas import HistoricalEvent, KnowledgeSearchQuery, KnowledgeSearchResult
from app.services.ingestion_service import ingestion_service

class KnowledgeService:
    def __init__(self):
        pass

    def search_events(self, query_params: KnowledgeSearchQuery) -> KnowledgeSearchResult:
        events = ingestion_service.get_all_events()
        filtered = []

        q_text = (query_params.query or "").lower().strip()

        # Extract keywords and potential depth numbers from natural language query
        extracted_depths = [float(x) for x in re.findall(r'(\d{3,5})', q_text)]
        depth_target = extracted_depths[0] if extracted_depths else None

        for ev in events:
            # Well filter
            if query_params.well_id:
                clean_target = query_params.well_id.replace("-", "/").replace("_", "/").strip().lower()
                clean_well = ev.well_id.replace("-", "/").replace("_", "/").strip().lower()
                if clean_target != clean_well and clean_target not in clean_well:
                    continue

            # Formation filter
            if query_params.formation:
                if query_params.formation.lower() not in ev.formation.lower():
                    continue

            # Event Type filter
            if query_params.event_type:
                if query_params.event_type.lower() not in ev.event_type.lower():
                    continue

            # Severity filter
            if query_params.severity:
                if query_params.severity.upper() != ev.severity.upper():
                    continue

            # Depth filter
            if query_params.depth_min is not None and ev.depth_end_m < query_params.depth_min:
                continue
            if query_params.depth_max is not None and ev.depth_start_m > query_params.depth_max:
                continue

            # Text query matching
            if q_text:
                text_corpus = f"{ev.well_id} {ev.formation} {ev.event_type} {ev.mitigation_action} {ev.verbatim_excerpt}".lower()

                # Check for NLP concept match
                match_score = 0
                query_tokens = [w for w in re.split(r'\W+', q_text) if len(w) > 2]

                for token in query_tokens:
                    if token in text_corpus:
                        match_score += 1

                # Check depth proximity if mentioned in query
                if depth_target:
                    if (ev.depth_start_m - 200.0) <= depth_target <= (ev.depth_end_m + 200.0):
                        match_score += 3

                # Accept if tokens matched or if query was empty
                if match_score == 0 and len(query_tokens) > 0:
                    continue

            filtered.append((match_score if q_text else 1, ev))

        # Sort: Highest match_score first, then CRITICAL/HIGH, then depth
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        filtered.sort(key=lambda item: (-item[0], severity_order.get(item[1].severity, 4), item[1].depth_start_m))

        # Extract events and truncate to limit
        results = [item[1] for item in filtered[:query_params.limit]]

        # Generate AI Summary for driller / superintendent
        summary_text = self._generate_ai_summary(q_text, results)

        return KnowledgeSearchResult(
            total_matches=len(filtered),
            query_applied=query_params.model_dump(),
            results=results,
            ai_summary=summary_text
        )

    def get_events_for_depth_window(
        self,
        target_depth_m: float,
        formation: Optional[str] = None,
        lookahead_m: float = 50.0,
        offset_wells: Optional[List[str]] = None
    ) -> List[HistoricalEvent]:
        """Finds offset well events occurring within a lookahead window of active bit depth."""
        events = ingestion_service.get_all_events()
        matches = []

        window_start = target_depth_m - 20.0
        window_end = target_depth_m + lookahead_m

        for ev in events:
            if offset_wells and ev.well_id not in offset_wells:
                continue

            # Check depth overlap
            overlap = not (ev.depth_end_m < window_start or ev.depth_start_m > window_end)
            formation_match = formation is not None and formation.lower() in ev.formation.lower()

            if overlap or formation_match:
                matches.append(ev)

        return matches

    def _generate_ai_summary(self, query: str, results: List[HistoricalEvent]) -> str:
        if not results:
            return f"No historical drilling incidents found matching the query '{query}'. Formations in this search space appear to have been drilled routinely."

        top_events = {}
        for r in results:
            top_events[r.event_type] = top_events.get(r.event_type, 0) + 1

        events_str = ", ".join([f"{k} ({v}x)" for k, v in top_events.items()])
        sample = results[0]

        summary = (
            f"Found {len(results)} historical operational incidents. Primary hazards: {events_str}. "
            f"Most severe reference is {sample.well_id} in {sample.formation} ({sample.depth_start_m:.0f}-{sample.depth_end_m:.0f}m): "
            f"'{sample.verbatim_excerpt[:160]}...'. Proven mitigation: {sample.mitigation_action[:140]}."
        )
        return summary

knowledge_service = KnowledgeService()
