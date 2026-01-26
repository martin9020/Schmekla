import ezdxf
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import hashlib

class DrawingProcessor:
    """
    Handles ingestion and processing of DWG drawings.
    Extracts text entities, layers, and basic geometry metadata.
    """

    def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Process a single DWG file.
        
        Args:
            file_path: Absolute path to the DWG file.
            
        Returns:
            List of chunks (text entities found in the building).
        """
        if not file_path.exists() or file_path.suffix.lower() != ".dwg":
            logger.error(f"Invalid file path or format: {file_path}")
            return []

        logger.info(f"Processing DWG: {file_path.name}")
        
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            
            extracted_text = []
            
            # Extract MTEXT and TEXT entities
            for entity in msp.query('TEXT MTEXT'):
                text_content = entity.dxf.text if entity.dxftype() == 'TEXT' else entity.text
                if text_content and len(text_content.strip()) > 3: # Filter noise
                    extracted_text.append({
                        "id": self._generate_id(file_path.name, text_content),
                        "text": text_content.strip(),
                        "metadata": {
                            "source": file_path.name,
                            "type": "dwg_text",
                            "layer": entity.dxf.layer,
                            "file_path": str(file_path)
                        }
                    })
            
            logger.success(f"Extracted {len(extracted_text)} text entities from {file_path.name}")
            return extracted_text

        except Exception as e:
            logger.exception(f"Failed to process DWG {file_path}: {e}")
            return []

    def _generate_id(self, filename: str, content: str) -> str:
        unique_str = f"{filename}_{content[:50]}"
        return hashlib.md5(unique_str.encode()).hexdigest()
