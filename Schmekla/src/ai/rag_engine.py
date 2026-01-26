from typing import List, Dict, Any
from pathlib import Path
from loguru import logger
from .document_processor import DocumentProcessor
from .dwg_processor import DrawingProcessor
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore, ChromaDBStore

class RAGEngine:
    """
    Orchestrates the Retrieval-Augmented Generation pipeline.
    Handles document ingestion, embedding generation, and vector storage.
    """

    def __init__(self, persist_directory: str = None):
        self.doc_processor = DocumentProcessor()
        self.dwg_processor = DrawingProcessor()
        self.embedding_generator = EmbeddingGenerator()
        
        # Initialize Vector Store
        self.vector_store = ChromaDBStore(persist_directory=persist_directory)

    def ingest_file(self, file_path: Path):
        """
        Ingest a file (PDF or DWG) into the knowledge base.
        1. Extract text chunks/entities
        2. Generate embeddings
        3. Store in VectorDB
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return

        logger.info(f"Ingesting file: {file_path.name}")
        chunks = []

        # 1. Extraction
        if file_path.suffix.lower() == ".pdf":
            chunks = self.doc_processor.process_file(file_path)
        elif file_path.suffix.lower() == ".dwg":
            chunks = self.dwg_processor.process_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path.suffix}")
            return

        if not chunks:
            logger.warning(f"No content extracted from {file_path.name}")
            return

        # Prepare for storage
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [c["id"] for c in chunks]

        # 2. Embedding Generation
        logger.info(f"Generating embeddings for {len(documents)} chunks...")
        embeddings = self.embedding_generator.generate(documents)

        # 3. Storage
        self.vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
        logger.success(f"Successfully ingested {file_path.name}")

    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search the knowledge base for relevant context.
        """
        logger.info(f"Querying knowledge base: '{query_text}'")
        
        # Generator query embedding
        query_embedding = self.embedding_generator.generate(query_text)
        
        # Search vector store
        # Note: EmbeddingGenerator returns list[float] for str input, but query expects list[list[float]]
        if isinstance(query_embedding[0], float):
             query_embedding = [query_embedding]

        results = self.vector_store.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        return results

    def ingest_directory(self, directory: Path):
        """Bulk ingest all supported files in a directory."""
        directory = Path(directory)
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return

        files = list(directory.glob("**/*.pdf")) + list(directory.glob("**/*.dwg"))
        logger.info(f"Found {len(files)} files to ingest in {directory}")

        for file_path in files:
            self.ingest_file(file_path)
