from pdf2table.usecases.table_extraction_use_case import TableExtractionUseCase
from pdf2table.adaptors.table_extraction_adaptor import TableExtractionAdapter
from pdf2table.frameworks.pdf_image_extractor import PyMuPDFImageExtractor
from pdf2table.frameworks.table_transformer_detector import TableTransformerDetector
from pdf2table.frameworks.table_structure_recognizer import (
    TableTransformerStructureRecognizer,
)
from pdf2table.frameworks.ocr_service import TrOCRService
from pdf2table.frameworks.logging_config import get_logger


logger = get_logger(__name__)


class TableExtractionFactory:
    """Factory for creating table extraction components following Clean Architecture."""

    @staticmethod
    def create_table_extraction_adapter(
        device: str = "cpu",
        detection_threshold: float = 0.9,
        structure_threshold: float = 0.6,
        pdf_dpi: int = 300,
        load_ocr: bool = False,
        visualize: bool = False,
        visualization_save_dir: str = "data/table_visualizations",  # Optional save dir
    ) -> TableExtractionAdapter:
        """Create a fully configured table extraction adapter."""

        logger.info(
            f"Creating table extraction adapter - Device: {device}, "
            f"Detection threshold: {detection_threshold}, "
            f"Structure threshold: {structure_threshold}, "
            f"PDF DPI: {pdf_dpi}, OCR: {load_ocr}, Visualize: {visualize}"
        )

        # Create framework implementations (outermost layer)
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

        if load_ocr:
            logger.debug("Initializing OCR service")
            ocr_service = TrOCRService(device=device)
        else:
            logger.debug("OCR service disabled")
            ocr_service = None

        logger.debug("Creating table extraction use case")
        table_extraction_use_case = TableExtractionUseCase(
            pdf_extractor=pdf_extractor,
            table_detector=table_detector,
            structure_recognizer=structure_recognizer,
            ocr_service=ocr_service,
            visualize=visualize,
            visualization_save_dir=visualization_save_dir,
        )

        logger.debug("Creating table extraction adapter")
        adapter = TableExtractionAdapter(table_extraction_use_case)

        logger.info("Table extraction adapter created successfully")
        return adapter


# Convenience function for backward compatibility
def create_table_transformer_adaptor(device: str = "cpu") -> TableExtractionAdapter:
    """Create table transformer adapter - maintains interface compatibility."""
    return TableExtractionFactory.create_table_extraction_adapter(device)


class TableExtractionService:
    """High-level service interface for table extraction."""

    def __init__(self, device: str = "cpu"):
        logger.info(f"Initializing TableExtractionService with device: {device}")
        self._adapter = TableExtractionFactory.create_table_extraction_adapter(device)

    def extract_tables_from_page(self, pdf_path: str, page_number: int) -> dict:
        """Extract tables from a single PDF page."""
        logger.info(f"Extracting tables from {pdf_path}, page {page_number}")
        try:
            response = self._adapter.extract_tables(pdf_path, page_number)
            result = response.to_dict()
            tables_count = len(result.get("tables", []))
            logger.info(
                f"Successfully extracted {tables_count} tables from page {page_number}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to extract tables from page {page_number}: {e}")
            raise

    def extract_tables_from_pdf(self, pdf_path: str) -> list[dict]:
        """Extract tables from all pages of a PDF."""
        logger.info(f"Starting table extraction from entire PDF: {pdf_path}")

        try:
            response = self._adapter.extract_tables(pdf_path)
            result = response.to_dict()

            if result.get("success"):
                tables_count = len(result.get("tables", []))
                logger.info(
                    f"Successfully extracted {tables_count} tables from entire PDF"
                )
            else:
                logger.error(
                    f"Failed to extract tables from PDF: {result.get('error')}"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to extract tables from PDF: {e}")
            raise
