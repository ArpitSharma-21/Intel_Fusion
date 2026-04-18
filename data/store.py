"""
In-memory data store for the application.
Maintains state across Streamlit reruns using session state.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

from core.extractor import Document
from core.nlp_pipeline import ExtractionResult
from core.graph_builder import IntelGraph, GraphBuilder
from core.timeline_builder import Timeline, TimelineBuilder
from core.pattern_detector import PatternReport
from core.risk_scorer import RiskAssessment


@dataclass
class AnalysisState:
    """Complete analysis state."""
    documents: List[Document] = field(default_factory=list)
    extractions: List[ExtractionResult] = field(default_factory=list)
    graph_builder: GraphBuilder = field(default_factory=GraphBuilder)
    timeline_builder: TimelineBuilder = field(default_factory=TimelineBuilder)
    pattern_report: Optional[PatternReport] = None
    risk_assessment: Optional[RiskAssessment] = None
    last_updated: Optional[datetime] = None
    
    @property
    def has_data(self) -> bool:
        """Check if any data has been loaded."""
        return len(self.documents) > 0
    
    @property
    def document_count(self) -> int:
        return len(self.documents)
    
    @property
    def entity_count(self) -> int:
        return sum(len(e.entities) for e in self.extractions)
    
    @property
    def graph(self) -> IntelGraph:
        return self.graph_builder.get_master_graph()
    
    @property
    def timeline(self) -> Timeline:
        return self.timeline_builder.build()
    
    def add_document(self, doc: Document, extraction: ExtractionResult):
        """Add a processed document to the state."""
        self.documents.append(doc)
        self.extractions.append(extraction)
        
        # Update graph
        self.graph_builder.process_extraction(extraction)
        
        # Update timeline
        self.timeline_builder.add_events(extraction.events)
        
        self.last_updated = datetime.now()
        
        # Invalidate cached analyses
        self.pattern_report = None
        self.risk_assessment = None
    
    def clear(self):
        """Clear all data."""
        self.documents = []
        self.extractions = []
        self.graph_builder = GraphBuilder()
        self.timeline_builder = TimelineBuilder()
        self.pattern_report = None
        self.risk_assessment = None
        self.last_updated = None
    
    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """Find a document by its ID."""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary of current state."""
        metrics = self.graph.get_metrics()
        
        return {
            "documents": self.document_count,
            "total_words": sum(d.total_words for d in self.documents),
            "entities": self.entity_count,
            "relationships": metrics.edge_count,
            "events": len(self.timeline_builder.events),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


def get_state() -> AnalysisState:
    """
    Get or create the analysis state.
    
    Uses Streamlit session state for persistence across reruns.
    """
    import streamlit as st
    
    if "analysis_state" not in st.session_state:
        st.session_state.analysis_state = AnalysisState()
    
    return st.session_state.analysis_state


def reset_state():
    """Reset the analysis state."""
    import streamlit as st
    
    if "analysis_state" in st.session_state:
        st.session_state.analysis_state.clear()
