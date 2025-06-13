from typing import List, Optional

from table_rag.entities.table_entities import (
    PageImage,
    DetectedTable,
)
from table_rag.usecases.services.table_services import (
    TableValidationService,
)
from table_rag.usecases.table_grid_builder import TableGridBuilder
from table_rag.usecases.interfaces.framework_interfaces import (
    PDFImageExtractorInterface,
    TableDetectorInterface,
    TableStructureRecognizerInterface,
    OCRInterface,
)


# Use Case Classes
class TableExtractionUseCase:
    """Use case for extracting tables from PDF documents."""

    def __init__(
        self,
        pdf_extractor: PDFImageExtractorInterface,
        table_detector: TableDetectorInterface,
        structure_recognizer: TableStructureRecognizerInterface,
        ocr_service: OCRInterface,
    ):
        self._pdf_extractor = pdf_extractor
        self._table_detector = table_detector
        self._structure_recognizer = structure_recognizer
        self._ocr_service = ocr_service
        self._validation_service = TableValidationService()

    def extract_tables_from_page(
        self, pdf_path: str, page_number: int
    ) -> List[DetectedTable]:
        """Extract all tables from a PDF page."""
        # Extract page image
        page_image = self._pdf_extractor.extract_page_image(pdf_path, page_number)

        # Detect tables
        detected_tables = self._table_detector.detect_tables(page_image)

        # Process each detected table
        structured_tables = []
        for table in detected_tables:
            try:
                structured_table = self._process_detected_table(page_image, table)
                if structured_table:
                    structured_tables.append(structured_table)
            except Exception as e:
                print(f"Error processing table on page {page_number}: {e}")
                continue

        return structured_tables

    def _process_detected_table(
        self, page_image: PageImage, detected_table: DetectedTable
    ) -> Optional[DetectedTable]:
        """Process a single detected table to extract its structure."""
        # Recognize table structure
        detected_cells = self._structure_recognizer.recognize_structure(
            page_image, detected_table.detection_box
        )

        # Validate detected structure
        if not self._validation_service.is_valid_table_structure(detected_cells):
            return None

        # Build table grid
        grid_builder = TableGridBuilder(self._ocr_service)
        table_grid = grid_builder.build_grid(
            detected_cells, page_image, detected_table.detection_box
        )

        if not table_grid:
            return None

        # Update detected table with grid
        detected_table.grid = table_grid
        return detected_table
