"""
PDF text extraction module.
Handles extraction of text content from PDF documents.
"""
import fitz  # PyMuPDF
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import hashlib


@dataclass
class Page:
    """Represents a single page from a document."""
    number: int
    text: str
    word_count: int


@dataclass
class Document:
    """Represents an extracted document with metadata."""
    id: str
    filename: str
    pages: List[Page]
    full_text: str
    total_pages: int
    total_words: int
    extracted_at: datetime
    metadata: dict = field(default_factory=dict)
    
    @property
    def preview(self) -> str:
        """Return first 500 characters as preview."""
        return self.full_text[:500] + "..." if len(self.full_text) > 500 else self.full_text


class PDFExtractor:
    """
    Extracts text content from PDF files.
    
    Uses PyMuPDF for reliable extraction with fallback strategies.
    """
    
    def __init__(self):
        self.supported_extensions = {'.pdf'}
    
    def extract(self, file_bytes: bytes, filename: str) -> Document:
        """
        Extract text from PDF bytes.
        
        Args:
            file_bytes: Raw PDF file content
            filename: Original filename for reference
            
        Returns:
            Document object with extracted content
        """
        # Generate unique ID from content hash
        doc_id = hashlib.md5(file_bytes).hexdigest()[:12]
        
        # Open PDF from bytes
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        
        pages = []
        all_text = []
        
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            
            # Extract text with layout preservation
            text = page.get_text("text")
            
            # Clean up the text
            text = self._clean_text(text)
            
            if text.strip():
                pages.append(Page(
                    number=page_num + 1,
                    text=text,
                    word_count=len(text.split())
                ))
                all_text.append(text)
        
        pdf.close()
        
        full_text = "\n\n".join(all_text)
        
        return Document(
            id=doc_id,
            filename=filename,
            pages=pages,
            full_text=full_text,
            total_pages=len(pages),
            total_words=sum(p.word_count for p in pages),
            extracted_at=datetime.now(),
            metadata=self._extract_metadata(file_bytes)
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Remove excessive spaces within line
                line = ' '.join(line.split())
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_metadata(self, file_bytes: bytes) -> dict:
        """Extract PDF metadata."""
        try:
            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            metadata = pdf.metadata or {}
            pdf.close()
            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creation_date": metadata.get("creationDate", "")
            }
        except Exception:
            return {}


# Convenience function
def extract_pdf(file_bytes: bytes, filename: str) -> Document:
    """Extract text from a PDF file."""
    extractor = PDFExtractor()
    return extractor.extract(file_bytes, filename)
