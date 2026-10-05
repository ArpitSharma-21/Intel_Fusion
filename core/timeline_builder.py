"""
Timeline generation module for temporal event analysis.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from core.nlp_pipeline import Event


@dataclass
class TimelineEntry:
    """A single entry on the timeline."""
    date: datetime
    date_display: str
    events: List[str]
    entities: List[str]
    document_ids: List[str]
    importance: float = 1.0
    
    def __lt__(self, other):
        if self.date and other.date:
            return self.date < other.date
        return False


@dataclass
class Timeline:
    """Complete timeline with entries and metadata."""
    entries: List[TimelineEntry]
    date_range: Tuple[Optional[datetime], Optional[datetime]]
    total_events: int
    entities_involved: List[str]


class TimelineBuilder:
    """
    Builds chronological timelines from extracted events.
    """
    
    def __init__(self):
        self.events: List[Event] = []
        self._timeline_cache: Optional[Timeline] = None
    
    def add_events(self, events: List[Event]):
        """Add events to the timeline builder."""
        self.events.extend(events)
        self._timeline_cache = None  # Invalidate cache
    
    def build(self) -> Timeline:
        """Build timeline from collected events."""
        if self._timeline_cache:
            return self._timeline_cache
        
        # Group events by date
        date_groups = defaultdict(list)
        undated_events = []
        
        for event in self.events:
            if event.parsed_date:
                # Normalize to date only (remove time)
                date_key = event.parsed_date.date()
                date_groups[date_key].append(event)
            else:
                undated_events.append(event)
        
        # Create timeline entries
        entries = []
        all_entities = set()
        
        for date, events in sorted(date_groups.items()):
            event_descriptions = []
            entry_entities = set()
            doc_ids = set()
            
            for event in events:
                event_descriptions.append(event.description)
                entry_entities.update(event.entities_involved)
                doc_ids.add(event.document_id)
                all_entities.update(event.entities_involved)
            
            entries.append(TimelineEntry(
                date=datetime.combine(date, datetime.min.time()),
                date_display=date.strftime("%B %d, %Y"),
                events=event_descriptions,
                entities=list(entry_entities),
                document_ids=list(doc_ids),
                importance=len(events)  # More events = more important
            ))
        
        # Sort by date
        entries.sort()
        
        # Calculate date range
        date_range = (
            entries[0].date if entries else None,
            entries[-1].date if entries else None
        )
        
        self._timeline_cache = Timeline(
            entries=entries,
            date_range=date_range,
            total_events=len(self.events),
            entities_involved=list(all_entities)
        )
        
        return self._timeline_cache
    
    def get_events_for_entity(self, entity_name: str) -> List[TimelineEntry]:
        """Get timeline entries involving a specific entity."""
        timeline = self.build()
        
        entity_lower = entity_name.lower()
        return [
            entry for entry in timeline.entries
            if any(entity_lower in e.lower() for e in entry.entities)
        ]
    
    def get_events_in_range(
        self, 
        start: datetime, 
        end: datetime
    ) -> List[TimelineEntry]:
        """Get timeline entries within a date range."""
        timeline = self.build()
        
        return [
            entry for entry in timeline.entries
            if start <= entry.date <= end
        ]
    
    def detect_temporal_clusters(
        self, 
        window_days: int = 7
    ) -> List[Dict]:
        """
        Detect clusters of events happening close together.
        
        Returns clusters where multiple events occur within window_days.
        """
        timeline = self.build()
        clusters = []
        
        if not timeline.entries:
            return clusters
        
        current_cluster = [timeline.entries[0]]
        
        for entry in timeline.entries[1:]:
            prev_date = current_cluster[-1].date
            
            if (entry.date - prev_date).days <= window_days:
                current_cluster.append(entry)
            else:
                if len(current_cluster) >= 2:
                    clusters.append({
                        "start": current_cluster[0].date,
                        "end": current_cluster[-1].date,
                        "event_count": sum(len(e.events) for e in current_cluster),
                        "entries": current_cluster,
                        "entities": list(set().union(*[
                            set(e.entities) for e in current_cluster
                        ]))
                    })
                current_cluster = [entry]
        
        # Don't forget the last cluster
        if len(current_cluster) >= 2:
            clusters.append({
                "start": current_cluster[0].date,
                "end": current_cluster[-1].date,
                "event_count": sum(len(e.events) for e in current_cluster),
                "entries": current_cluster,
                "entities": list(set().union(*[
                    set(e.entities) for e in current_cluster
                ]))
            })
        
        return clusters
    
    def reset(self):
        """Clear all events."""
        self.events = []
        self._timeline_cache = None
