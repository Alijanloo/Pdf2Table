from typing import Optional
from pdf2table.usecases.table_extraction_use_case import TableExtractionUseCase
from pdf2table.frameworks.pdf_image_extractor import PyMuPDFImageExtractor
from pdf2table.frameworks.table_transformer_detector import TableTransformerDetector
from pdf2table.frameworks.table_structure_recognizer import (
    TableTransformerStructureRecognizer,
)
from pdf2table.frameworks.ocr_service import TrOCRService
from pdf2table.frameworks.logging_config import get_logger


logger = get_logger(__name__)


def create_pipeline(
    device: str = "cpu",
    detection_threshold: float = 0.9,
    structure_threshold: float = 0.6,
    pdf_dpi: int = 300,
    load_ocr: bool = False,
    visualize: bool = False,
    visualization_save_dir: str = "data/table_visualizations",
) -> TableExtractionUseCase:
    """
    Create a fully configured table extraction pipeline.

    Args:
        device: Device to use for ML models ('cpu' or 'cuda')
        detection_threshold: Confidence threshold for table detection
        structure_threshold: Confidence threshold for structure recognition
        pdf_dpi: DPI for PDF page rendering
        load_ocr: Whether to load OCR service
        visualize: Whether to enable visualization
        visualization_save_dir: Directory to save visualizations

    Returns:
        TableExtractionUseCase: Configured use case ready for table extraction
    """
    logger.info(
        f"Creating table extraction pipeline - Device: {device}, "
        f"Detection threshold: {detection_threshold}, "
        f"Structure threshold: {structure_threshold}, "
        f"PDF DPI: {pdf_dpi}, OCR: {load_ocr}, Visualize: {visualize}"
    )

    logger.debug("Initializing PDF image extractor")
    pdf_extractor = PyMuPDFImageExtractor(dpi=pdf_dpi)

    logger.debug("Initializing table transformer detector")
    table_detector = TableTransformerDetector(
        device=device, confidence_threshold=detection_threshold
    )

    logger.debug("Initializing table structure recognizer")
    structure_recognizer = TableTransformerStructureRecognizer(
        device=device, confidence_threshold=structure_threshold
    )

    ocr_service: Optional[TrOCRService] = None
    if load_ocr:
        logger.debug("Initializing OCR service")
        ocr_service = TrOCRService(device=device)
    else:
        logger.debug("OCR service disabled")

    logger.debug("Creating table extraction use case")
    use_case = TableExtractionUseCase(
        pdf_extractor=pdf_extractor,
        table_detector=table_detector,
        structure_recognizer=structure_recognizer,
        ocr_service=ocr_service,
        visualize=visualize,
        visualization_save_dir=visualization_save_dir,
    )

    logger.info("Table extraction pipeline created successfully")
    return use_case
