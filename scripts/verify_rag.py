
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.rag_engine import RAGEngine

def verify_rag():
    logger.info("Verifying RAG Pipeline...")
    
    # Initialize Engine (it will create ChromaDB in .schmekla/knowledge_db)
    engine = RAGEngine()
    
    # Define a sample file to ingest (Use one of the conditions files)
    sample_pdf = Path(r"G:\My Drive\Shmekla\Schmekla\Conditions\704216-2-Domino Printing-Provisional GA.pdf")
    
    if not sample_pdf.exists():
        logger.error(f"Sample file not found: {sample_pdf}")
        return

    # 1. Ingest
    logger.info(f"Step 1: Ingesting {sample_pdf.name}...")
    engine.ingest_file(sample_pdf)
    
    # 2. Query
    query = "What is the project location and height?"
    logger.info(f"Step 2: Querying: '{query}'")
    
    results = engine.query(query, n_results=3)
    
    # 3. Display Results
    if results and results['documents']:
        logger.success("Query successful! Retrieved context:")
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            print(f"\n[Result {i+1}] (Page {meta.get('page')})")
            print("-" * 50)
            print(doc[:200] + "..." if len(doc) > 200 else doc)
            print("-" * 50)
    else:
        logger.error("Query returned no results.")

if __name__ == "__main__":
    verify_rag()
