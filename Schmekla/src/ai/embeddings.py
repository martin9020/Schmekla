from typing import List, Union
from loguru import logger
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class EmbeddingGenerator:
    """
    Generates vector embeddings for text chunks using local models.
    Defaults to 'all-MiniLM-L6-v2' (fast, lightweight).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers not installed. Please run 'pip install sentence-transformers'")
            
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        logger.debug(f"Model loaded. Dimension: {self.embedding_dimension}")

    def generate(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for a string or list of strings.
        
        Args:
            text: Single string or list of strings.
            
        Returns:
            List of floats (if input is str) or List of List of floats (if input is list).
        """
        try:
            embeddings = self.model.encode(text, convert_to_numpy=True)
            
            if isinstance(embeddings, np.ndarray):
                return embeddings.tolist()
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return [] if isinstance(text, str) else [[]] * len(text)
