from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
import chromadb
from chromadb.config import Settings
import shutil

class VectorStore(ABC):
    """Abstract interface for vector storage backends."""

    @abstractmethod
    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str], embeddings: List[List[float]]):
        """Add documents and their embeddings to the store."""
        pass

    @abstractmethod
    def query(self, query_embeddings: List[List[float]], n_results: int = 5) -> Dict[str, Any]:
        """Query the store for similar documents."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return the number of documents in the store."""
        pass


class ChromaDBStore(VectorStore):
    """ChromaDB implementation of VectorStore (Local)."""

    def __init__(self, persist_directory: str = None, collection_name: str = "schmekla_knowledge"):
        if not persist_directory:
            # Default to .schmekla/knowledge_db in user home
            persist_directory = str(Path.home() / ".schmekla" / "knowledge_db")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        logger.info(f"Initializing ChromaDB at {self.persist_directory}")
        
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.debug(f"Collection '{self.collection_name}' loaded. Records: {self.collection.count()}")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str], embeddings: List[List[float]]):
        if not documents:
            return

        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            logger.success(f"Added {len(documents)} documents to vector store.")
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")

    def query(self, query_embeddings: List[List[float]], n_results: int = 5, where: Dict = None) -> Dict[str, Any]:
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"Vector query failed: {e}")
            return {}

    def count(self) -> int:
        return self.collection.count()
    
    def reset(self):
        """DANGER: Delete entire collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(self.collection_name)
        logger.warning(f"Collection '{self.collection_name}' has been RESET.")
