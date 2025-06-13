from typing import List

from table_rag.entities.table_entities import DetectedCell, TableGrid


# Domain Services (Business Rules)
class TableValidationService:
    """Domain service for table validation rules."""

    @staticmethod
    def is_valid_table_structure(cells: List[DetectedCell]) -> bool:
        """Validate if detected cells form a valid table structure."""
        if len(cells) < 2:
            return False

        # Simple validation: check if we have structure indicators or enough cells
        has_structure = any(
            "row" in cell.cell_type.lower() or "column" in cell.cell_type.lower()
            for cell in cells
        )
        return has_structure or len(cells) >= 4

    @staticmethod
    def calculate_grid_confidence(grid: TableGrid) -> float:
        """Calculate overall confidence score for a table grid."""
        if not grid.cells:
            return 0.0

        total_confidence = sum(cell.confidence_score for cell in grid.cells)
        return total_confidence / len(grid.cells)


class CoordinateClusteringService:
    """Domain service for clustering coordinates."""

    @staticmethod
    def cluster_coordinates(
        coords: List[float], threshold: float = 20.0
    ) -> List[float]:
        """Cluster coordinates that are close together."""
        if not coords:
            return []

        sorted_coords = sorted(set(coords))
        if len(sorted_coords) == 1:
            return sorted_coords

        # Simple clustering based on threshold
        clusters = [[sorted_coords[0]]]

        for coord in sorted_coords[1:]:
            if coord - clusters[-1][-1] < threshold:
                clusters[-1].append(coord)
            else:
                clusters.append([coord])

        # Return cluster centers
        return [sum(cluster) / len(cluster) for cluster in clusters]
