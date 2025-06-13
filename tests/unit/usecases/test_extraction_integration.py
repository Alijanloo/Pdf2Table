import unittest
from unittest.mock import Mock
import numpy as np

from table_rag.entities.table_entities import (
    PageImage,
    DetectedTable,
    DetectedCell,
    BoundingBox,
)
from table_rag.usecases.table_extraction_use_case import (
    TableExtractionUseCase,
)


# Integration test showing the full workflow
class TestTableExtractionIntegration(unittest.TestCase):
    """Integration tests demonstrating the complete workflow."""

    def test_end_to_end_table_extraction(self):
        """Test the complete table extraction workflow with realistic data."""
        # This would typically use real implementations for integration testing
        # For demonstration, we'll use mocks that return realistic data

        # Create realistic mock data
        mock_pdf_extractor = Mock()
        mock_table_detector = Mock()
        mock_structure_recognizer = Mock()
        mock_ocr_service = Mock()

        # Set up realistic return values
        page_image = PageImage(
            page_number=0,
            image_data=np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8),
            source_file="sample.pdf",
        )
        mock_pdf_extractor.extract_page_image.return_value = page_image

        detected_table = DetectedTable(
            detection_box=BoundingBox(x_min=50, y_min=50, x_max=350, y_max=250),
            confidence_score=0.92,
            page_number=0,
            source_file="sample.pdf",
        )
        mock_table_detector.detect_tables.return_value = [detected_table]

        # Create a 2x2 table structure
        detected_cells = [
            # Row indicators
            DetectedCell(
                box=BoundingBox(x_min=50, y_min=50, x_max=350, y_max=100),
                cell_type="table row",
                confidence_score=0.85,
            ),
            DetectedCell(
                box=BoundingBox(x_min=50, y_min=100, x_max=350, y_max=150),
                cell_type="table row",
                confidence_score=0.80,
            ),
            # Column indicators
            DetectedCell(
                box=BoundingBox(x_min=50, y_min=50, x_max=200, y_max=150),
                cell_type="table column",
                confidence_score=0.90,
            ),
            DetectedCell(
                box=BoundingBox(x_min=200, y_min=50, x_max=350, y_max=150),
                cell_type="table column",
                confidence_score=0.88,
            ),
        ]
        mock_structure_recognizer.recognize_structure.return_value = detected_cells

        # Mock OCR to return different text for different cells
        ocr_responses = ["Header 1", "Header 2", "Data 1", "Data 2"]
        mock_ocr_service.extract_text.side_effect = ocr_responses

        # Create use case and run extraction
        use_case = TableExtractionUseCase(
            pdf_extractor=mock_pdf_extractor,
            table_detector=mock_table_detector,
            structure_recognizer=mock_structure_recognizer,
            ocr_service=mock_ocr_service,
        )

        # Act
        results = use_case.extract_tables_from_page("sample.pdf", 0)

        # Assert
        assert len(results) == 1
        table = results[0]
        assert table.is_structured
        assert table.grid.n_rows >= 2
        assert table.grid.n_cols >= 2

        # Check that we can convert to row format
        row_data = table.grid.to_row_format()
        assert len(row_data) >= 1  # At least one data row (excluding header)

        print(
            f"Successfully extracted table with {table.grid.n_rows} rows and {table.grid.n_cols} columns"
        )
        print(f"Row data: {row_data}")


if __name__ == "__main__":
    unittest.main()
