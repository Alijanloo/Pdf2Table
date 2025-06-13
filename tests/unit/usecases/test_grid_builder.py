import unittest
from unittest.mock import Mock
import numpy as np

from table_rag.entities.table_entities import (
    PageImage,
    DetectedCell,
    BoundingBox,
    TableGrid,
)
from table_rag.usecases.table_extraction_use_case import (
    TableGridBuilder,
)


class TestTableGridBuilder(unittest.TestCase):
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
                confidence_score=0.8,
            ),
            DetectedCell(
                box=BoundingBox(x_min=0, y_min=25, x_max=50, y_max=50),
                cell_type="table row",
                confidence_score=0.7,
            ),
            DetectedCell(
                box=BoundingBox(x_min=0, y_min=0, x_max=25, y_max=50),
                cell_type="table column",
                confidence_score=0.9,
            ),
            DetectedCell(
                box=BoundingBox(x_min=25, y_min=0, x_max=50, y_max=50),
                cell_type="table column",
                confidence_score=0.8,
            ),
        ]

        page_image = PageImage(
            page_number=0,
            image_data=np.zeros((100, 100, 3), dtype=np.uint8),
            source_file="test.pdf",
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
            source_file="test.pdf",
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
            confidence_score=0.8,
        )
        wide_col = DetectedCell(
            box=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=50),  # Very wide
            cell_type="table column",
            confidence_score=0.9,
        )

        col_cells = [narrow_col, wide_col]

        # Act
        filtered = self.builder._filter_spurious_columns(col_cells)

        # Assert
        assert len(filtered) == 1
        assert filtered[0] == narrow_col  # Wide column should be filtered out


if __name__ == "__main__":
    unittest.main()
