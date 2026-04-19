"""
PDF text extraction module.
Handles extraction of text content from PDF documents.
"""
import fitz  # PyMuPDF
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import hashlib

from docx import Document as DocxDocument
import pandas as pd
from bs4 import BeautifulSoup

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



class MultiFormatExtractor:
    """
    Handles multiple document formats and routes to appropriate extractor.
    """
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.supported_extensions = {
            '.pdf', '.docx', '.txt', '.csv', '.xlsx', '.html'
        }

    def extract(self, file_bytes: bytes, filename: str) -> Document:
        ext = '.' + filename.split('.')[-1].lower()

        if ext == '.pdf':
            return self.pdf_extractor.extract(file_bytes, filename)

        elif ext == '.docx':
            return self._extract_docx(file_bytes, filename)

        elif ext == '.txt':
            return self._extract_txt(file_bytes, filename)

        elif ext == '.csv':
            return self._extract_csv(file_bytes, filename)

        elif ext == '.xlsx':
            return self._extract_excel(file_bytes, filename)

        elif ext == '.html':
            return self._extract_html(file_bytes, filename)

        else:
            raise ValueError(f"Unsupported file type: {ext}")
        

    def _create_document(self, text: str, filename: str, file_bytes: bytes) -> Document:
        doc_id = hashlib.md5(file_bytes).hexdigest()[:12]

        pages = [
            Page(
                number=1,
                text=text,
                word_count=len(text.split())
            )
        ]

        return Document(
            id=doc_id,
            filename=filename,
            pages=pages,
            full_text=text,
            total_pages=1,
            total_words=len(text.split()),
            extracted_at=datetime.now(),
            metadata={}
        )
    def _extract_docx(self, file_bytes, filename):
        from io import BytesIO
        doc = DocxDocument(BytesIO(file_bytes))
        text = "\n".join([p.text for p in doc.paragraphs])
        return self._create_document(text, filename, file_bytes)

    def _extract_txt(self, file_bytes, filename):
        text = file_bytes.decode("utf-8", errors="ignore")
        return self._create_document(text, filename, file_bytes)

    def _extract_csv(self, file_bytes, filename):
        from io import BytesIO
        df = pd.read_csv(BytesIO(file_bytes))
        text = df.to_string()
        return self._create_document(text, filename, file_bytes)
    
    def _extract_excel(self, file_bytes, filename):
        from io import BytesIO
        df = pd.read_excel(BytesIO(file_bytes))
        text = df.to_string()
        return self._create_document(text, filename, file_bytes)
    def _extract_html(self, file_bytes, filename):
        soup = BeautifulSoup(file_bytes, "html.parser")
        text = soup.get_text()
        return self._create_document(text, filename, file_bytes)


    
def extract_document(file_bytes: bytes, filename: str) -> Document:
    extractor = MultiFormatExtractor()
    return extractor.extract(file_bytes, filename)