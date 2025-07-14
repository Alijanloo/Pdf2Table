from typing import List

from pdf2table.entities.table_entities import DetectedCell, TableGrid


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

        coords = sorted(set(coords))

        if len(coords) > 2:
            differences = [coords[i+1] - coords[i] for i in range(len(coords)-1)]
            if differences:

                mean_diff = sum(differences) / len(differences)

                # Adjusting threshold for too high or low mean_diffs
                threshold = max(threshold, mean_diff * 0.7)
                if mean_diff < 5:
                    threshold = min(threshold, mean_diff * 2)

        clusters = [[coords[0]]]

        for coord in coords[1:]:
            if coord - clusters[-1][-1] < threshold:
                clusters[-1].append(coord)
            else:
                clusters.append([coord])

        cluster_centers = [sum(cluster) / len(cluster) for cluster in clusters]

        if len(cluster_centers) > 1:
            final_centers = [cluster_centers[0]]
            for center in cluster_centers[1:]:

                if center - final_centers[-1] < threshold/2:
                    continue
                final_centers.append(center)
            return final_centers
            
        return cluster_centers