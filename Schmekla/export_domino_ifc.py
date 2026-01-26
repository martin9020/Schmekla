"""
Export the Domino Printing canopy model to IFC format.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from loguru import logger

def main():
    """Build model and export to IFC."""

    # Setup logging
    from src.utils.logger import setup_logging
    setup_logging()

    logger.info("=" * 60)
    logger.info("Domino Printing Canopy - IFC Export")
    logger.info("=" * 60)

    # Build the model
    logger.info("\nBuilding structural model...")
    from examples.domino_printing_canopy import build_domino_printing_canopy
    model = build_domino_printing_canopy()

    # Export to IFC
    output_path = project_root / "output" / "704216_Domino_Printing_Canopy.ifc"
    output_path.parent.mkdir(exist_ok=True)

    logger.info(f"\nExporting to IFC: {output_path}")

    try:
        from src.ifc.exporter import IFCExporter
        exporter = IFCExporter(model)
        exporter.export(str(output_path), schema="IFC2X3")

        logger.info("=" * 60)
        logger.info("EXPORT COMPLETE")
        logger.info(f"Output file: {output_path}")
        logger.info("=" * 60)

        return True

    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Install with: pip install ifcopenshell")
        return False

    except Exception as e:
        logger.error(f"Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
