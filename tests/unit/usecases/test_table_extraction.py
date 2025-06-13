import unittest
from unittest.mock import Mock
import numpy as np

from table_rag.entities.table_entities import (
    PageImage, DetectedTable, DetectedCell, BoundingBox
)
from table_rag.usecases.table_extraction_use_case import TableExtractionUseCase


class TestTableExtractionUseCase(unittest.TestCase):
    """Test suite for TableExtractionUseCase demonstrating Clean Architecture benefits."""
    
    def setup_method(self):
        """Set up mocks for each test."""
        self.mock_pdf_extractor = Mock()
        self.mock_table_detector = Mock()
        self.mock_structure_recognizer = Mock()
        self.mock_ocr_service = Mock()
        
        self.use_case = TableExtractionUseCase(
            pdf_extractor=self.mock_pdf_extractor,
            table_detector=self.mock_table_detector,
            structure_recognizer=self.mock_structure_recognizer,
            ocr_service=self.mock_ocr_service
        )
    
    def test_extract_tables_from_page_success(self):
        """Test successful table extraction from a page."""
        # Arrange
        pdf_path = "test.pdf"
        page_number = 0
        
        # Mock page image
        mock_image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        page_image = PageImage(
            page_number=page_number,
            image_data=mock_image_data,
            source_file=pdf_path
        )
        self.mock_pdf_extractor.extract_page_image.return_value = page_image
        
        # Mock detected table
        detection_box = BoundingBox(x_min=10, y_min=10, x_max=90, y_max=90)
        detected_table = DetectedTable(
            detection_box=detection_box,
            confidence_score=0.95,
            page_number=page_number,
            source_file=pdf_path
        )
        self.mock_table_detector.detect_tables.return_value = [detected_table]
        
        # Mock detected cells
        cell1 = DetectedCell(
            box=BoundingBox(x_min=10, y_min=10, x_max=50, y_max=30),
            cell_type="table row",
            confidence_score=0.8
        )
        cell2 = DetectedCell(
            box=BoundingBox(x_min=10, y_min=30, x_max=50, y_max=50),
            cell_type="table column",
            confidence_score=0.7
        )
        self.mock_structure_recognizer.recognize_structure.return_value = [cell1, cell2]
        
        # Mock OCR
        self.mock_ocr_service.extract_text.return_value = "test text"
        
        # Act
        result = self.use_case.extract_tables_from_page(pdf_path, page_number)
        
        # Assert
        assert len(result) == 1
        assert result[0].confidence_score == 0.95
        assert result[0].grid is not None
        
        # Verify method calls
        self.mock_pdf_extractor.extract_page_image.assert_called_once_with(pdf_path, page_number)
        self.mock_table_detector.detect_tables.assert_called_once_with(page_image)
        self.mock_structure_recognizer.recognize_structure.assert_called_once()
    
    def test_extract_tables_from_page_no_valid_structure(self):
        """Test handling of tables with invalid structure."""
        # Arrange
        pdf_path = "test.pdf"
        page_number = 0
        
        mock_image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        page_image = PageImage(
            page_number=page_number,
            image_data=mock_image_data,
            source_file=pdf_path
        )
        self.mock_pdf_extractor.extract_page_image.return_value = page_image
        
        detection_box = BoundingBox(x_min=10, y_min=10, x_max=90, y_max=90)
        detected_table = DetectedTable(
            detection_box=detection_box,
            confidence_score=0.95,
            page_number=page_number,
            source_file=pdf_path
        )
        self.mock_table_detector.detect_tables.return_value = [detected_table]
        
        # Mock insufficient cells for valid structure
        cell1 = DetectedCell(
            box=BoundingBox(x_min=10, y_min=10, x_max=50, y_max=30),
            cell_type="unknown",
            confidence_score=0.3
        )
        self.mock_structure_recognizer.recognize_structure.return_value = [cell1]
        
        # Act
        result = self.use_case.extract_tables_from_page(pdf_path, page_number)
        
        # Assert
        assert len(result) == 0  # No valid tables should be returned
    
    def test_extract_tables_handles_exceptions(self):
        """Test that exceptions in processing individual tables don't stop the entire process."""
        # Arrange
        pdf_path = "test.pdf"
        page_number = 0
        
        mock_image_data = np.zeros((100, 100, 3), dtype=np.uint8)
        page_image = PageImage(
            page_number=page_number,
            image_data=mock_image_data,
            source_file=pdf_path
        )
        self.mock_pdf_extractor.extract_page_image.return_value = page_image
        
        # Create two tables, one will fail
        table1 = DetectedTable(
            detection_box=BoundingBox(x_min=10, y_min=10, x_max=50, y_max=50),
            confidence_score=0.95,
            page_number=page_number,
            source_file=pdf_path
        )
        table2 = DetectedTable(
            detection_box=BoundingBox(x_min=60, y_min=10, x_max=90, y_max=50),
            confidence_score=0.90,
            page_number=page_number,
            source_file=pdf_path
        )
        self.mock_table_detector.detect_tables.return_value = [table1, table2]
        
        # Make structure recognition fail for first table, succeed for second
        def mock_recognize_structure(page_image, table_box):
            if table_box.x_min == 10:
                raise Exception("Processing failed")
            else:
                return [
                    DetectedCell(
                        box=BoundingBox(x_min=60, y_min=10, x_max=75, y_max=30),
                        cell_type="table row",
                        confidence_score=0.8
                    ),
                    DetectedCell(
                        box=BoundingBox(x_min=75, y_min=10, x_max=90, y_max=30),
                        cell_type="table column",
                        confidence_score=0.7
                    )
                ]
        
        self.mock_structure_recognizer.recognize_structure.side_effect = mock_recognize_structure
        self.mock_ocr_service.extract_text.return_value = "test"
        
        # Act
        result = self.use_case.extract_tables_from_page(pdf_path, page_number)
        
        # Assert
        assert len(result) == 1  # Only the second table should succeed
        assert result[0].detection_box.x_min == 60


if __name__ == "__main__":
    unittest.main()
