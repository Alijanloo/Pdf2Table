from typing import List, Optional

from pdf2table.entities.table_entities import (
    PageImage,
    DetectedTable,
)
from pdf2table.usecases.services.table_services import (
    TableValidationService,
)
from pdf2table.usecases.table_grid_builder import TableGridBuilder
from pdf2table.usecases.interfaces.framework_interfaces import (
    PDFImageExtractorInterface,
    TableDetectorInterface,
    TableStructureRecognizerInterface,
    OCRInterface,
)
from pdf2table.usecases.table_visualization_utils import (
    visualize_table_structure,
    visualize_cell_grid,
    visualize_table_detection,
)


class TableExtractionUseCase:
    """Use case for extracting tables from PDF documents."""

    def __init__(
        self,
        pdf_extractor: PDFImageExtractorInterface,
        table_detector: TableDetectorInterface,
        structure_recognizer: TableStructureRecognizerInterface,
        ocr_service: OCRInterface,
        visualize: bool = False,
        visualization_save_dir: str = None,
    ):
        self.pdf_extractor = pdf_extractor
        self.table_detector = table_detector
        self.structure_recognizer = structure_recognizer
        self.validation_service = TableValidationService()
        self.grid_builder = TableGridBuilder(ocr_service)
        self._visualize = visualize
        self._visualization_save_dir = visualization_save_dir

    def extract_tables_from_page(
        self, pdf_path: str, page_number: int
    ) -> List[DetectedTable]:
        """Extract all tables from a PDF page."""
        page_image = self.pdf_extractor.extract_page_image(pdf_path, page_number)

        detected_tables = self.table_detector.detect_tables(page_image)

        if self._visualize:
            visualize_table_detection(
                page_image,
                detected_tables,
                visualization_save_dir=self._visualization_save_dir,
            )

        structured_tables = []
        for idx, table in enumerate(detected_tables):
            try:
                structured_table = self._process_detected_table(
                    page_image, table, table_idx=idx
                )
                if structured_table:
                    structured_tables.append(structured_table)
            except Exception as e:
                print(f"Error processing table on page {page_number}: {e}")
                continue

        return structured_tables

    def _process_detected_table(
        self, page_image: PageImage, detected_table: DetectedTable, table_idx: int = 0
    ) -> Optional[DetectedTable]:
        """Process a single detected table to extract its structure."""
        detected_cells = self.structure_recognizer.recognize_structure(
            page_image, detected_table.detection_box
        )

        if self._visualize:
            visualize_table_structure(
                page_image,
                detected_cells,
                detected_table.detection_box,
                self._visualization_save_dir,
            )

        if not self.validation_service.is_valid_table_structure(detected_cells):
            return None

        table_grid = self.grid_builder.build_grid(
            detected_cells, page_image, detected_table.detection_box
        )

        if self._visualize and table_grid:
            visualize_cell_grid(
                table_grid,
                page_image,
                visualization_save_dir=self._visualization_save_dir,
                show_text=True,
            )

        if not table_grid:
            return None

        detected_table.grid = table_grid
        return detected_table
