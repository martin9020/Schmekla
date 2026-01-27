import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
import hashlib

class DocumentProcessor:
    """
    Handles ingestion and processing of PDF documents for the knowledge base.
    """

    def __init__(self, chucker_strategy: str = "sentence"):
        self.chunker_strategy = chucker_strategy

    def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Process a single PDF file and return chunks of text with metadata.
        
        Args:
            file_path: Absolute path to the PDF file.
            
        Returns:
            List of dictionaries containing 'text', 'metadata', and 'id'.
        """
        if not file_path.exists() or file_path.suffix.lower() != ".pdf":
            logger.error(f"Invalid file path or format: {file_path}")
            return []

        logger.info(f"Processing PDF: {file_path.name}")
        
        try:
            doc = fitz.open(file_path)
            all_chunks = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Basic chunking by paragraph for now
                chunks = self._chunk_text(text, page_num)
                
                for chunk_text in chunks:
                    chunk_id = self._generate_id(file_path.name, page_num, chunk_text)
                    all_chunks.append({
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "source": file_path.name,
                            "page": page_num + 1,
                            "file_path": str(file_path)
                        }
                    })
            
            logger.success(f"Extracted {len(all_chunks)} chunks from {file_path.name}")
            return all_chunks

        except Exception as e:
            logger.exception(f"Failed to process PDF {file_path}: {e}")
            return []

    def _chunk_text(self, text: str, page_num: int) -> List[str]:
        """Split text into manageable chunks."""
        # Simple splitting by double newlines to find paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs

    def _generate_id(self, filename: str, page: int, content: str) -> str:
        """Generate a deterministic ID for a chunk."""
        unique_str = f"{filename}_{page}_{content[:50]}"
        return hashlib.md5(unique_str.encode()).hexdigest()
