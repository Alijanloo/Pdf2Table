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
        """Build a structured grid from detected cells (robust, overlap-based)."""
        if not detected_cells:
            return None

        # Collect all y and x edges from all detected cells
        y_edges = set()
        x_edges = set()
        for cell in detected_cells:
            y_edges.add(cell.box.y_min)
            y_edges.add(cell.box.y_max)
            x_edges.add(cell.box.x_min)
            x_edges.add(cell.box.x_max)

        # Cluster edges to get row/col boundaries
        row_boundaries = self._clustering_service.cluster_coordinates(
            sorted(y_edges), threshold=10.0
        )
        col_boundaries = self._clustering_service.cluster_coordinates(
            sorted(x_edges), threshold=10.0
        )

        # Ensure sorted and unique
        row_boundaries = sorted(set(int(round(y)) for y in row_boundaries))
        col_boundaries = sorted(set(int(round(x)) for x in col_boundaries))

        n_rows = len(row_boundaries) - 1
        n_cols = len(col_boundaries) - 1
        if n_rows <= 0 or n_cols <= 0:
            return None

        # Build grid: assign detected cells to grid slots by overlap
        grid = {}
        for cell in detected_cells:
            c_xmin, c_ymin, c_xmax, c_ymax = (
                cell.box.x_min,
                cell.box.y_min,
                cell.box.x_max,
                cell.box.y_max,
            )
            for r in range(n_rows):
                # Check if the cell vertically overlaps with the current grid row, skip if not
                if not (c_ymax > row_boundaries[r] and c_ymin < row_boundaries[r + 1]):
                    continue
                for c in range(n_cols):
                    # Check horizontal overlap
                    if not (
                        c_xmax > col_boundaries[c] and c_xmin < col_boundaries[c + 1]
                    ):
                        continue
                    pos = (r, c)
                    if (
                        pos not in grid
                        or cell.confidence_score > grid[pos].confidence_score
                    ):
                        grid[pos] = cell

        # Fill grid cells, including empty ones
        grid_cells = []
        for r in range(n_rows):
            for c in range(n_cols):
                pos = (r, c)
                # Compute cell bounding box
                cell_box = BoundingBox(
                    x_min=max(0, col_boundaries[c]),
                    y_min=max(0, row_boundaries[r]),
                    x_max=min(table_box.x_max, col_boundaries[c + 1]),
                    y_max=min(table_box.y_max, row_boundaries[r + 1]),
                )
                if pos in grid:
                    cell = grid[pos]
                    confidence = cell.confidence_score
                else:
                    confidence = 0.0

                text = ""
                if cell_box.area > 0:
                    text = self._extract_cell_text(cell_box, page_image)

                grid_cell = GridCell(
                    row=r,
                    col=c,
                    text=text,
                    box=cell_box,
                    confidence_score=confidence,
                )
                grid_cells.append(grid_cell)

        return TableGrid(
            cells=grid_cells, n_rows=n_rows, n_cols=n_cols, table_box=table_box
        )

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
                selected_text = " ".join(
                    [
                        w[4]
                        for w in page_image.words
                        if fitz.Rect(w[:4]).intersects(rect)
                    ]
                )
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
