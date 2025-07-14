import unittest
from unittest.mock import Mock
import numpy as np

from pdf2table.entities.table_entities import (
    PageImage,
    DetectedCell,
    BoundingBox,
    TableGrid,
)
from pdf2table.usecases.table_extraction_use_case import (
    TableGridBuilder,
)


class TestTableGridBuilder(unittest.TestCase):
    """Test suite for TableGridBuilder."""

    def setUp(self):
        self.mock_ocr_service = Mock()
        self.builder = TableGridBuilder(self.mock_ocr_service)

    def test_build_grid_with_valid_cells(self):
        """Test building a grid from valid detected cells."""
        # Arrange: at least 2 rows and 2 columns for a valid grid
        detected_cells = [
            DetectedCell(
                box=BoundingBox(x_min=0, y_min=0, x_max=50, y_max=10),  # row 1
                cell_type="table row",
                confidence_score=0.8,
            ),
            DetectedCell(
                box=BoundingBox(x_min=0, y_min=100, x_max=50, y_max=110),  # row 2 (y_min=100, y_max=110)
                cell_type="table row",
                confidence_score=0.7,
            ),
            DetectedCell(
                box=BoundingBox(x_min=0, y_min=0, x_max=10, y_max=110),  # col 1
                cell_type="table column",
                confidence_score=0.9,
            ),
            DetectedCell(
                box=BoundingBox(x_min=100, y_min=0, x_max=110, y_max=110),  # col 2 (x_min=100, x_max=110)
                cell_type="table column",
                confidence_score=0.8,
            ),
        ]

        page_image = PageImage(
            page_number=0,
            image_data=np.zeros((200, 200, 3), dtype=np.uint8),
            source_file="test.pdf",
        )

        table_box = BoundingBox(x_min=0, y_min=0, x_max=120, y_max=120)

        self.mock_ocr_service.extract_text.return_value = "cell text"

        # Act
        result = self.builder.build_grid(detected_cells, page_image, table_box)

        # Assert
        assert result is not None
        assert isinstance(result, TableGrid)
        assert result.n_rows >= 2
        assert result.n_cols >= 2
        assert len(result.cells) == result.n_rows * result.n_cols

    def test_build_grid_with_empty_cells(self):
        """Test handling of empty cell list."""
        # Arrange
        detected_cells = []
        page_image = PageImage(
            page_number=0,
            image_data=np.zeros((200, 200, 3), dtype=np.uint8),
            source_file="test.pdf",
        )
        table_box = BoundingBox(x_min=0, y_min=0, x_max=120, y_max=120)

        # Act
        result = self.builder.build_grid(detected_cells, page_image, table_box)

        # Assert
        assert result is None



if __name__ == "__main__":
    unittest.main()
