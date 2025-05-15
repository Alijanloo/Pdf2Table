from typing import List, Dict, Any, Optional

import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

def visualize_table_detection(pil_img: Image, detection_results: Dict, detection_id2label: Dict, save_path: str = None):
    COLORS = [
        [0.000, 0.447, 0.741],
        [0.850, 0.325, 0.098],
        [0.929, 0.694, 0.125],
        [0.494, 0.184, 0.556],
        [0.466, 0.674, 0.188],
        [0.301, 0.745, 0.933],
    ]

    plt.figure(figsize=(16, 10))
    plt.imshow(pil_img)
    ax = plt.gca()
    colors = COLORS * 100

    for score, label, (xmin, ymin, xmax, ymax), c in zip(
        detection_results["scores"].tolist(),
        detection_results["labels"].tolist(),
        detection_results["boxes"].tolist(),
        colors,
    ):
        ax.add_patch(
            plt.Rectangle(
                (xmin, ymin),
                xmax - xmin,
                ymax - ymin,
                fill=False,
                color=c,
                linewidth=3,
            )
        )
        text = f"{detection_id2label[label]}: {score:0.2f}"
        ax.text(xmin, ymin, text, fontsize=15, bbox=dict(facecolor="yellow", alpha=0.5))

    plt.axis("off")
    title = f"Table Detection Result"
    plt.title(title)

    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()

def visualize_table_structure(
    table_pil: Image, structure_result: Dict, structure_id2label: Dict, save_path: str = None
):
    COLORS = [
        [0.000, 0.447, 0.741],
        [0.850, 0.325, 0.098],
        [0.929, 0.694, 0.125],
        [0.494, 0.184, 0.556],
        [0.466, 0.674, 0.188],
        [0.301, 0.745, 0.933],
    ]

    plt.figure(figsize=(16, 10))
    plt.imshow(table_pil)
    ax = plt.gca()
    colors = COLORS * 100

    for score, label, (xmin, ymin, xmax, ymax), c in zip(
        structure_result["scores"].tolist(),
        structure_result["labels"].tolist(),
        structure_result["boxes"].tolist(),
        colors,
    ):
        ax.add_patch(
            plt.Rectangle(
                (xmin, ymin),
                xmax - xmin,
                ymax - ymin,
                fill=False,
                color=c,
                linewidth=3,
            )
        )
        text = f"{structure_id2label[label]}: {score:0.2f}"
        ax.text(xmin, ymin, text, fontsize=12, bbox=dict(facecolor="yellow", alpha=0.5))

    plt.axis("off")
    title = f"Table Structure Result"
    plt.title(title)

    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
    else:
        plt.show()

def visualize_cell_grid(
    cell_grid: List[Dict[str, Any]],
    table_image: np.ndarray,
    save_path: Optional[str] = None,
    show_text: bool = True,
) -> None:

    if not cell_grid:
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

    table_pil = Image.fromarray(table_image)

    plt.figure(figsize=(16, 10))
    plt.imshow(table_pil)
    ax = plt.gca()

    max_row = max([cell["row"] for cell in cell_grid], default=0)
    max_col = max([cell["col"] for cell in cell_grid], default=0)

    print(f"Table grid: {max_row + 1} rows × {max_col + 1} columns")

    has_relative_coords = False
    offset_x = offset_y = 0

    if any("relative_box" in cell for cell in cell_grid):
        for cell in cell_grid:
            if "relative_box" in cell and "box" in cell:
                offset_x = cell["box"][0] - cell["relative_box"][0]
                offset_y = cell["box"][1] - cell["relative_box"][1]
                has_relative_coords = True
                break

    cells_by_position = {}
    for cell in cell_grid:
        row_idx = cell["row"]
        col_idx = cell["col"]
        cells_by_position[(row_idx, col_idx)] = cell

    row_positions = set()
    col_positions = set()

    for cell in cell_grid:
        if len(cell["box"]) == 4:
            box = cell["box"]
            row_positions.add(box[1])
            row_positions.add(box[3])
            col_positions.add(box[0])
            col_positions.add(box[2])

    row_positions = sorted(row_positions)
    col_positions = sorted(col_positions)

    for r in range(max_row + 1):
        for c in range(max_col + 1):
            if (r, c) in cells_by_position:
                cell = cells_by_position[(r, c)]

                if len(cell["box"]) == 4:
                    xmin, ymin, xmax, ymax = cell["box"]

                    if has_relative_coords and "relative_box" in cell and (xmin == 0 or ymin == 0):
                        rel_xmin, rel_ymin, rel_xmax, rel_ymax = cell["relative_box"]
                        xmin, ymin = rel_xmin + offset_x, rel_ymin + offset_y
                        xmax, ymax = rel_xmax + offset_x, rel_ymax + offset_y

                    color_idx = c % len(COLORS)
                    cell_color = COLORS[color_idx]

                    rect = plt.Rectangle(
                        (xmin, ymin), xmax - xmin, ymax - ymin, fill=False, color=cell_color, linewidth=2, alpha=0.7
                    )
                    ax.add_patch(rect)

                    cell_label = f"r{r},c{c}"
                    label_x = xmin + 5
                    label_y = ymin + 15

                    ax.text(
                        label_x,
                        label_y,
                        cell_label,
                        fontsize=8,
                        color="white",
                        bbox=dict(facecolor=cell_color, alpha=0.7, pad=0.2),
                        zorder=10,
                    )

                    if show_text and cell.get("text"):

                        text = cell["text"]
                        if len(text) > 20:
                            text = text[:17] + "..."

                        center_x = xmin + (xmax - xmin) / 2
                        center_y = ymin + (ymax - ymin) / 2

                        ax.text(
                            center_x,
                            center_y,
                            text,
                            fontsize=8,
                            ha="center",
                            va="center",
                            bbox=dict(facecolor="white", alpha=0.7, pad=0.3),
                            wrap=True,
                            zorder=5,
                        )

    plt.title(f"Table Cell Grid: {max_row + 1} rows × {max_col + 1} columns")
    plt.axis("off")

    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
    else:
        plt.tight_layout()
        plt.show()
