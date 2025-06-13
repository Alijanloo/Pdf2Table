from unittest.mock import Mock
import numpy as np

from table_rag.entities.table_entities import (
    PageImage, DetectedTable, DetectedCell, BoundingBox, TableGrid
)
from table_rag.usecases.table_extraction_use_case import TableExtractionUseCase, TableGridBuilder


class TestTableExtractionUseCase:
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


class TestTableGridBuilder:
    """Test suite for TableGridBuilder."""
    
    def setup_method(self):
        self.mock_ocr_service = Mock()
        self.builder = TableGridBuilder(self.mock_ocr_service)
    
    def test_build_grid_with_valid_cells(self):
        """Test building a grid from valid detected cells."""
        # Arrange
        detected_cells = [
            DetectedCell(
                box=BoundingBox(x_min=0, y_min=0, x_max=50, y_max=25),
                cell_type="table row",
                confidence_score=0.8
            ),
            DetectedCell(
                box=BoundingBox(x_min=0, y_min=25, x_max=50, y_max=50),
                cell_type="table row",
                confidence_score=0.7
            ),
            DetectedCell(
                box=BoundingBox(x_min=0, y_min=0, x_max=25, y_max=50),
                cell_type="table column",
                confidence_score=0.9
            ),
            DetectedCell(
                box=BoundingBox(x_min=25, y_min=0, x_max=50, y_max=50),
                cell_type="table column",
                confidence_score=0.8
            )
        ]
        
        page_image = PageImage(
            page_number=0,
            image_data=np.zeros((100, 100, 3), dtype=np.uint8),
            source_file="test.pdf"
        )
        
        table_box = BoundingBox(x_min=0, y_min=0, x_max=50, y_max=50)
        
        self.mock_ocr_service.extract_text.return_value = "cell text"
        
        # Act
        result = self.builder.build_grid(detected_cells, page_image, table_box)
        
        # Assert
        assert result is not None
        assert isinstance(result, TableGrid)
        assert result.n_rows >= 1
        assert result.n_cols >= 1
        assert len(result.cells) == result.n_rows * result.n_cols
    
    def test_build_grid_with_empty_cells(self):
        """Test handling of empty cell list."""
        # Arrange
        detected_cells = []
        page_image = PageImage(
            page_number=0,
            image_data=np.zeros((100, 100, 3), dtype=np.uint8),
            source_file="test.pdf"
        )
        table_box = BoundingBox(x_min=0, y_min=0, x_max=50, y_max=50)
        
        # Act
        result = self.builder.build_grid(detected_cells, page_image, table_box)
        
        # Assert
        assert result is None
    
    def test_filter_spurious_columns(self):
        """Test filtering of spurious wide columns."""
        # Arrange
        narrow_col = DetectedCell(
            box=BoundingBox(x_min=0, y_min=0, x_max=25, y_max=50),
            cell_type="table column",
            confidence_score=0.8
        )
        wide_col = DetectedCell(
            box=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=50),  # Very wide
            cell_type="table column",
            confidence_score=0.9
        )
        
        col_cells = [narrow_col, wide_col]
        
        # Act
        filtered = self.builder._filter_spurious_columns(col_cells)
        
        # Assert
        assert len(filtered) == 1
        assert filtered[0] == narrow_col  # Wide column should be filtered out


# Integration test showing the full workflow
class TestTableExtractionIntegration:
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
            source_file="sample.pdf"
        )
        mock_pdf_extractor.extract_page_image.return_value = page_image
        
        detected_table = DetectedTable(
            detection_box=BoundingBox(x_min=50, y_min=50, x_max=350, y_max=250),
            confidence_score=0.92,
            page_number=0,
            source_file="sample.pdf"
        )
        mock_table_detector.detect_tables.return_value = [detected_table]
        
        # Create a 2x2 table structure
        detected_cells = [
            # Row indicators
            DetectedCell(
                box=BoundingBox(x_min=50, y_min=50, x_max=350, y_max=100),
                cell_type="table row",
                confidence_score=0.85
            ),
            DetectedCell(
                box=BoundingBox(x_min=50, y_min=100, x_max=350, y_max=150),
                cell_type="table row",
                confidence_score=0.80
            ),
            # Column indicators  
            DetectedCell(
                box=BoundingBox(x_min=50, y_min=50, x_max=200, y_max=150),
                cell_type="table column",
                confidence_score=0.90
            ),
            DetectedCell(
                box=BoundingBox(x_min=200, y_min=50, x_max=350, y_max=150),
                cell_type="table column",
                confidence_score=0.88
            )
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
            ocr_service=mock_ocr_service
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
        
        print(f"Successfully extracted table with {table.grid.n_rows} rows and {table.grid.n_cols} columns")
        print(f"Row data: {row_data}")


if __name__ == "__main__":
    # Run a simple test
    test_integration = TestTableExtractionIntegration()
    test_integration.test_end_to_end_table_extraction()
    print("Integration test passed!")
