from typing import Optional, List

import matplotlib.pyplot as plt
from table_rag.entities.table_entities import (
    PageImage,
    TableGrid,
    DetectedTable,
    DetectedCell,
)


def visualize_table_detection(
    page_image: PageImage,
    detected_tables: List[DetectedTable],
    save_path: str = None,
):
    """
    Visualize DetectedTable entities on a PageImage.
    """
    COLORS = [
        [0.000, 0.447, 0.741],
        [0.850, 0.325, 0.098],
        [0.929, 0.694, 0.125],
        [0.494, 0.184, 0.556],
        [0.466, 0.674, 0.188],
        [0.301, 0.745, 0.933],
    ]

    plt.figure(figsize=(16, 10))
    plt.imshow(page_image.image_data)
    ax = plt.gca()
    colors = COLORS * 100

    for i, table in enumerate(detected_tables):
        c = colors[i % len(colors)]
        box = table.detection_box
        label = "table"
        ax.add_patch(
            plt.Rectangle(
                (box.x_min, box.y_min),
                box.x_max - box.x_min,
                box.y_max - box.y_min,
                fill=False,
                color=c,
                linewidth=3,
            )
        )
        text = f"{label}: {table.confidence_score:0.2f}"
        ax.text(
            box.x_min,
            box.y_min,
            text,
            fontsize=15,
            bbox=dict(facecolor="yellow", alpha=0.5),
        )

    plt.axis("off")
    plt.title("Table Detection Result")

    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def visualize_table_structure(
    page_image: PageImage,
    detected_cells: List[DetectedCell],
    table_box,
    save_path: str = None,
):
    COLORS = [
        [0.000, 0.447, 0.741],
        [0.850, 0.325, 0.098],
        [0.929, 0.694, 0.125],
        [0.494, 0.184, 0.556],
        [0.466, 0.674, 0.188],
        [0.301, 0.745, 0.933],
    ]

    # Crop the table image
    cropped = page_image.image_data[
        table_box.y_min : table_box.y_max, table_box.x_min : table_box.x_max
    ]
    plt.figure(figsize=(12, 8))
    plt.imshow(cropped)
    ax = plt.gca()
    colors = COLORS * 100
    for i, cell in enumerate(detected_cells):
        c = colors[i % len(colors)]
        # Draw cell box relative to crop
        rel_xmin = cell.box.x_min - table_box.x_min
        rel_ymin = cell.box.y_min - table_box.y_min
        rel_xmax = cell.box.x_max - table_box.x_min
        rel_ymax = cell.box.y_max - table_box.y_min
        label = cell.cell_type
        ax.add_patch(
            plt.Rectangle(
                (rel_xmin, rel_ymin),
                rel_xmax - rel_xmin,
                rel_ymax - rel_ymin,
                fill=False,
                color=c,
                linewidth=2,
            )
        )
        text = f"{label}: {cell.confidence_score:0.2f}"
        ax.text(
            rel_xmin,
            rel_ymin,
            text,
            fontsize=12,
            bbox=dict(facecolor="yellow", alpha=0.5),
        )
    plt.axis("off")
    plt.title("Table Structure Result (Cropped)")
    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def visualize_cell_grid(
    table_grid: TableGrid,
    page_image: PageImage,
    save_path: Optional[str] = None,
    show_text: bool = True,
):
    """
    Visualize a TableGrid entity on a PageImage.
    """
    if not table_grid or not table_grid.cells:
        print("No cells detected in grid, skipping visualization.")
        return

    COLORS = [
        [0.000, 0.447, 0.741],  # Blue
        [0.850, 0.325, 0.098],  # Red
        [0.929, 0.694, 0.125],  # Yellow
        [0.494, 0.184, 0.556],  # Purple
        [0.466, 0.674, 0.188],  # Green
        [0.301, 0.745, 0.933],  # Cyan
        [0.635, 0.078, 0.184],  # Dark Red
        [0.300, 0.300, 0.300],  # Gray
        [0.800, 0.500, 0.300],  # Orange
    ]

    # Crop the table image
    cropped = page_image.image_data[
        table_grid.table_box.y_min : table_grid.table_box.y_max,
        table_grid.table_box.x_min : table_grid.table_box.x_max,
    ]
    plt.figure(figsize=(12, 8))
    plt.imshow(cropped)
    ax = plt.gca()

    print(f"Table grid: {table_grid.n_rows} rows × {table_grid.n_cols} columns")

    for cell in table_grid.cells:
        r, c = cell.row, cell.col
        box = cell.box
        color_idx = c % len(COLORS)
        cell_color = COLORS[color_idx]

        # Draw cell box relative to crop
        rel_xmin = box.x_min - table_grid.table_box.x_min
        rel_ymin = box.y_min - table_grid.table_box.y_min
        rel_xmax = box.x_max - table_grid.table_box.x_min
        rel_ymax = box.y_max - table_grid.table_box.y_min

        rect = plt.Rectangle(
            (rel_xmin, rel_ymin),
            rel_xmax - rel_xmin,
            rel_ymax - rel_ymin,
            fill=False,
            color=cell_color,
            linewidth=2,
            alpha=0.7,
        )
        ax.add_patch(rect)

        cell_label = f"r{r},c{c}"
        label_x = rel_xmin + 5
        label_y = rel_ymin + 15

        ax.text(
            label_x,
            label_y,
            cell_label,
            fontsize=12,
            color="white",
            bbox=dict(facecolor=cell_color, alpha=0.7, pad=0.2),
            zorder=10,
        )

        if show_text and cell.text:
            text = cell.text
            if len(text) > 20:
                text = text[:17] + "..."
            center_x = rel_xmin + (rel_xmax - rel_xmin) / 2
            center_y = rel_ymin + (rel_ymax - rel_ymin) / 2
            ax.text(
                center_x,
                center_y,
                text,
                fontsize=12,
                ha="center",
                va="center",
                bbox=dict(facecolor="white", alpha=0.7, pad=0.3),
                wrap=True,
                zorder=5,
            )

    plt.title(
        f"Table Cell Grid: {table_grid.n_rows} rows × {table_grid.n_cols} columns (Cropped)"
    )
    plt.axis("off")

    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
    else:
        plt.tight_layout()
        plt.show()
