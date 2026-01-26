
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.document_processor import DocumentProcessor
from src.ai.dwg_processor import DrawingProcessor
from loguru import logger

def extract_requirements():
    conditions_dir = Path(r"G:\My Drive\Shmekla\Schmekla\Conditions")
    
    # Process PDFs
    pdf_processor = DocumentProcessor()
    for pdf_file in conditions_dir.glob("**/*.pdf"):
        logger.info(f"Processing PDF: {pdf_file.name}")
        chunks = pdf_processor.process_file(pdf_file)
        # In a real RAG system, we'd store these. For this task, we'll print relevant snippets.
        # Just printing the first chunk of each page to get an overview
        for chunk in chunks[:3]: 
            print(f"--- CONTENT FROM {pdf_file.name} ---")
            print(chunk['text'][:500] + "...")
            print("-----------------------------------")

    # Process DWGs
    dwg_processor = DrawingProcessor()
    for dwg_file in conditions_dir.glob("**/*.dwg"):
        logger.info(f"Processing DWG: {dwg_file.name}")
        entities = dwg_processor.process_file(dwg_file)
        # Print first few text entities found
        print(f"--- TEXT FROM {dwg_file.name} ---")
        for entity in entities[:20]:
            print(f"Layer: {entity['metadata']['layer']} | Text: {entity['text']}")
        print("-----------------------------------")

if __name__ == "__main__":
    extract_requirements()
