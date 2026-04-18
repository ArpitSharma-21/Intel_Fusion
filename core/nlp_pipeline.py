"""
NLP Pipeline for entity extraction and relationship detection.
"""
import spacy
from spacy.tokens import Doc
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime
import re

from config import nlp_config


@dataclass
class Entity:
    """Represents an extracted entity."""
    text: str
    label: str
    start: int
    end: int
    sentence: str
    document_id: str
    count: int = 1
    
    @property
    def normalized_text(self) -> str:
        """Normalized version of entity text."""
        return self.text.strip().title()
    
    def __hash__(self):
        return hash((self.normalized_text, self.label))
    
    def __eq__(self, other):
        if isinstance(other, Entity):
            return (self.normalized_text == other.normalized_text and 
                    self.label == other.label)
        return False


@dataclass
class Relationship:
    """Represents a relationship between two entities."""
    source: str
    target: str
    source_type: str
    target_type: str
    relationship_type: str
    weight: int = 1
    context: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash((self.source, self.target, self.relationship_type))


@dataclass
class Event:
    """Represents a temporal event."""
    description: str
    date_text: str
    parsed_date: Optional[datetime]
    entities_involved: List[str]
    document_id: str
    confidence: float = 1.0


@dataclass 
class ExtractionResult:
    """Complete extraction results from NLP pipeline."""
    entities: List[Entity]
    relationships: List[Relationship]
    events: List[Event]
    entity_counts: Dict[str, Dict[str, int]]  # {label: {entity: count}}
    document_id: str


class NLPPipeline:
    """
    Main NLP pipeline for intelligence extraction.
    
    Extracts entities, relationships, and temporal events from text.
    """
    
    def __init__(self, model_name: str = None):
        """Initialize the NLP pipeline with spaCy model."""
        model_name = model_name or nlp_config.model_name
        
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            # Download model if not present
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
        
        self.entity_types = set(nlp_config.entity_types)
        
        # Date patterns for extraction
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        ]
    
    def process(self, text: str, document_id: str) -> ExtractionResult:
        """
        Process text through the full NLP pipeline.
        
        Args:
            text: Input text to process
            document_id: ID of source document
            
        Returns:
            ExtractionResult with all extracted intelligence
        """
        # Process with spaCy
        doc = self.nlp(text)
        
        # Extract entities
        entities = self._extract_entities(doc, document_id)
        
        # Count entity occurrences
        entity_counts = self._count_entities(entities)
        
        # Extract relationships from co-occurrences
        relationships = self._extract_relationships(doc, document_id)
        
        # Extract temporal events
        events = self._extract_events(doc, document_id)
        
        return ExtractionResult(
            entities=entities,
            relationships=relationships,
            events=events,
            entity_counts=entity_counts,
            document_id=document_id
        )
    
    def _extract_entities(self, doc: Doc, document_id: str) -> List[Entity]:
        """Extract named entities from document."""
        entities = []
        seen = set()
        
        for ent in doc.ents:
            if ent.label_ not in self.entity_types:
                continue
            
            # Get sentence context
            sentence = ent.sent.text.strip() if ent.sent else ""
            
            # Create entity
            entity = Entity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                sentence=sentence,
                document_id=document_id
            )
            
            # Track unique entities
            key = (entity.normalized_text, entity.label)
            if key not in seen:
                seen.add(key)
                entities.append(entity)
        
        return entities
    
    def _count_entities(self, entities: List[Entity]) -> Dict[str, Dict[str, int]]:
        """Count entity occurrences by type."""
        counts = defaultdict(lambda: defaultdict(int))
        
        for entity in entities:
            counts[entity.label][entity.normalized_text] += 1
        
        return dict(counts)
    
    def _extract_relationships(self, doc: Doc, document_id: str) -> List[Relationship]:
        """
        Extract relationships based on sentence co-occurrence.
        
        Entities appearing in the same sentence are considered related.
        """
        relationships = []
        relationship_map = defaultdict(lambda: {"weight": 0, "contexts": []})
        
        for sent in doc.sents:
            # Get entities in this sentence
            sent_entities = [
                ent for ent in sent.ents 
                if ent.label_ in self.entity_types
            ]
            
            # Create relationships between all pairs
            for i, ent1 in enumerate(sent_entities):
                for ent2 in sent_entities[i + 1:]:
                    # Skip self-relationships
                    if ent1.text.lower() == ent2.text.lower():
                        continue
                    
                    # Create sorted key for consistency
                    key = tuple(sorted([
                        (ent1.text.strip().title(), ent1.label_),
                        (ent2.text.strip().title(), ent2.label_)
                    ]))
                    
                    relationship_map[key]["weight"] += 1
                    if len(relationship_map[key]["contexts"]) < 3:
                        relationship_map[key]["contexts"].append(sent.text.strip())
        
        # Convert to Relationship objects
        for (source_info, target_info), data in relationship_map.items():
            relationships.append(Relationship(
                source=source_info[0],
                target=target_info[0],
                source_type=source_info[1],
                target_type=target_info[1],
                relationship_type="co-occurrence",
                weight=data["weight"],
                context=data["contexts"]
            ))
        
        return relationships
    
    def _extract_events(self, doc: Doc, document_id: str) -> List[Event]:
        """Extract temporal events from text."""
        events = []
        
        for sent in doc.sents:
            # Look for sentences with DATE entities
            date_entities = [ent for ent in sent.ents if ent.label_ == "DATE"]
            other_entities = [
                ent.text.strip().title() 
                for ent in sent.ents 
                if ent.label_ in {"PERSON", "ORG", "GPE", "EVENT"}
            ]
            
            if date_entities:
                for date_ent in date_entities:
                    parsed = self._parse_date(date_ent.text)
                    
                    events.append(Event(
                        description=sent.text.strip(),
                        date_text=date_ent.text,
                        parsed_date=parsed,
                        entities_involved=other_entities,
                        document_id=document_id,
                        confidence=0.9 if parsed else 0.6
                    ))
        
        return events
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Attempt to parse date text into datetime object."""
        from dateutil import parser
        
        try:
            # Try parsing with dateutil
            return parser.parse(date_text, fuzzy=True)
        except (ValueError, TypeError):
            return None


# Convenience function
def process_text(text: str, document_id: str) -> ExtractionResult:
    """Process text through NLP pipeline."""
    pipeline = NLPPipeline()
    return pipeline.process(text, document_id)
