from typing import List, Optional
import fitz

from table_rag.entities.table_entities import (
    PageImage,
    DetectedCell,
    TableGrid,
    GridCell,
    BoundingBox,
)
from table_rag.usecases.services.table_services import (
    CoordinateClusteringService,
)
from table_rag.usecases.interfaces.framework_interfaces import (
    OCRInterface,
)


class TableGridBuilder:
    """Use case for building structured table grids from detected cells."""

    def __init__(self, ocr_service: OCRInterface):
        self._ocr_service = ocr_service
        self._clustering_service = CoordinateClusteringService()

    def build_grid(
        self,
        detected_cells: List[DetectedCell],
        page_image: PageImage,
        table_box: BoundingBox,
    ) -> Optional[TableGrid]:
        """Build a structured grid from detected cells."""
        if not detected_cells:
            return None

        # Separate row and column cells by type
        row_cells = [cell for cell in detected_cells if "row" in cell.cell_type.lower()]
        col_cells = [cell for cell in detected_cells if "column" in cell.cell_type.lower()]



        # Use only row/column cells for clustering, with artifact filtering for columns
        row_coords = [cell.box.center_y for cell in row_cells]
        filtered_col_cells = self._filter_artifact_columns(col_cells)
        col_coords = [cell.box.center_x for cell in filtered_col_cells]

        rows = self._clustering_service.cluster_coordinates(row_coords)
        cols = self._clustering_service.cluster_coordinates(col_coords)


        if len(rows) < 2 or len(cols) < 2:
            return None

        # Create grid cells
        grid_cells = self._create_grid_cells(
            detected_cells, rows, cols, page_image, table_box
        )

        if not grid_cells:
            return None

        return TableGrid(
            cells=grid_cells, n_rows=len(rows), n_cols=len(cols), table_box=table_box
        )
    
    def _filter_artifact_columns(self, col_cells: list) -> list:
        """Filter out spurious wide columns that contain other columns (artifact removal)."""
        if len(col_cells) > 1:
            sorted_by_width = sorted(col_cells, key=lambda c: c.box.width)
            widest_column = sorted_by_width[-1]
            widest_width = widest_column.box.width
            avg_width = sum([c.box.width for c in sorted_by_width[:-1]]) / max(1, len(sorted_by_width) - 1)
            contains_other_columns = any(
                c != widest_column and
                c.box.x_min >= widest_column.box.x_min and
                c.box.x_max <= widest_column.box.x_max
                for c in col_cells
            )
            if contains_other_columns or widest_width > 3 * avg_width:
                filtered = [c for c in col_cells if c != widest_column]
                print(f"Filtered out a wide column ({widest_width:.1f}px) that contains other columns")
                return filtered
        return col_cells

    def _create_grid_cells(
        self,
        detected_cells: List[DetectedCell],
        rows: List[float],
        cols: List[float],
        page_image: PageImage,
        table_box: BoundingBox,
    ) -> List[GridCell]:
        """Create grid cells by mapping detected cells to grid positions."""
        grid_cells = []

        for row_idx, row_y in enumerate(rows):
            for col_idx, col_x in enumerate(cols):
                # Find the best matching detected cell for this grid position
                best_cell = self._find_best_cell_for_position(
                    detected_cells, row_y, col_x
                )

                # Calculate cell boundaries
                cell_box = self._calculate_cell_boundaries(
                    row_idx, col_idx, rows, cols, table_box
                )

                # Extract text
                text = ""
                confidence = 0.0
                if best_cell:
                    confidence = best_cell.confidence_score

                if cell_box.area > 0:
                    text = self._extract_cell_text(cell_box, page_image)

                grid_cell = GridCell(
                    row=row_idx,
                    col=col_idx,
                    text=text,
                    box=cell_box,
                    confidence_score=confidence,
                )
                grid_cells.append(grid_cell)

        return grid_cells

    def _find_best_cell_for_position(
        self, detected_cells: List[DetectedCell], target_y: float, target_x: float
    ) -> Optional[DetectedCell]:
        """Find the detected cell closest to the target position."""
        if not detected_cells:
            return None

        best_cell = None
        min_distance = float("inf")

        for cell in detected_cells:
            distance = abs(cell.box.center_y - target_y) + abs(
                cell.box.center_x - target_x
            )
            if distance < min_distance:
                min_distance = distance
                best_cell = cell

        return best_cell

    def _calculate_cell_boundaries(
        self,
        row_idx: int,
        col_idx: int,
        rows: List[float],
        cols: List[float],
        table_box: BoundingBox,
    ) -> BoundingBox:
        """Calculate cell boundaries based on grid position."""
        # Simple boundary calculation using midpoints
        if row_idx == 0:
            y_min = table_box.y_min
        else:
            y_min = (
                int((rows[row_idx - 1] + rows[row_idx]) / 2)
                if row_idx > 0
                else table_box.y_min
            )

        if row_idx == len(rows) - 1:
            y_max = table_box.y_max
        else:
            y_max = (
                int((rows[row_idx] + rows[row_idx + 1]) / 2)
                if row_idx < len(rows) - 1
                else table_box.y_max
            )

        if col_idx == 0:
            x_min = table_box.x_min
        else:
            x_min = (
                int((cols[col_idx - 1] + cols[col_idx]) / 2)
                if col_idx > 0
                else table_box.x_min
            )

        if col_idx == len(cols) - 1:
            x_max = table_box.x_max
        else:
            x_max = (
                int((cols[col_idx] + cols[col_idx + 1]) / 2)
                if col_idx < len(cols) - 1
                else table_box.x_max
            )

        return BoundingBox(
            x_min=max(0, x_min),
            y_min=max(0, y_min),
            x_max=min(table_box.x_max, x_max),
            y_max=min(table_box.y_max, y_max),
        )

    def _extract_cell_text(self, cell_box: BoundingBox, page_image: PageImage) -> str:
        """Extract text from cell using direct PDF extraction if possible, else OCR."""
        try:
            # Try direct PDF text extraction using PyMuPDF
            try:
                area = (cell_box.x_min, cell_box.y_min, cell_box.x_max, cell_box.y_max)
                rect = fitz.Rect(area)
                selected_text = [w[4] for w in page_image.words if fitz.Rect(w[:4]).intersects(rect)]
                if selected_text.strip():
                    return selected_text.strip()
            except Exception:
                pass  # Fallback to OCR if direct extraction fails

            # Fallback: Crop image and use OCR
            crop = page_image.image_data[
                cell_box.y_min : cell_box.y_max, cell_box.x_min : cell_box.x_max
            ]
            if crop.size > 0 and crop.shape[0] > 0 and crop.shape[1] > 0:
                return self._ocr_service.extract_text(crop)
            else:
                return ""
        except Exception:
            return ""
