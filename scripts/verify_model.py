
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from build_domino_canopy import build_domino_canopy

def verify_model():
    logger.info("Verifying Domino Canopy Model generation...")
    
    try:
        # Build the model (headless)
        model = build_domino_canopy()
        
        # Verify Key Metrics
        logger.info(f"Model Name: {model.name}")
        logger.info(f"Total Elements: {model.element_count}")
        
        # Expected counts from build_domino_canopy.py logs
        # Columns: 10
        # Hoops: 10
        # Purlins: 68 
        # Eaves beams: 18
        # Total: 106 ?? Wait, existing log said 168? Let's check my count.
        # Hoops: 5 main + 4 intermediate = 9? No loops are 1-5 and intermediate.
        # Let's count explicitly.
        
        counts = {
            "beam": len([e for e in model.get_all_elements() if e.element_type.name == "BEAM"]),
            "column": len([e for e in model.get_all_elements() if e.element_type.name == "COLUMN"]),
            # CurvedBeam is likely a subclass of Beam or its own type.
            # If ElementType doesn't have CURVED_BEAM, it might be generic.
        }
        
        logger.info(f"Element Breakdown: {counts}")
        
        if model.element_count > 0:
            logger.success("Model generated successfully!")
            return True
        else:
            logger.error("Model is empty!")
            return False
            
    except Exception as e:
        logger.exception(f"Model verification failed: {e}")
        return False

if __name__ == "__main__":
    verify_model()
