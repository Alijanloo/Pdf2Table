import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from table_rag.adaptors.table_transformer_adaptor import TableTransformerAdaptor
from table_rag import DEFAULT_PATH


def main():
    parser = argparse.ArgumentParser(
        description="Visualize table detection and structure recognition."
    )
    parser.add_argument("--pdf", type=str, default=None, help="Path to PDF file")
    parser.add_argument(
        "--page", type=int, default=0, help="Page number to analyze (0-indexed)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save visualizations instead of displaying them",
    )
    parser.add_argument(
        "--table",
        type=int,
        default=0,
        help="Table index to visualize structure (if multiple tables detected)",
    )
    parser.add_argument("--gpu", action="store_true", help="Use GPU if available")
    args = parser.parse_args()

    device = "cuda" if args.gpu else "cpu"

    print(f"Initializing TableTransformerAdaptor with device={device}")
    adaptor = TableTransformerAdaptor(device=device)

    if args.pdf:
        pdf_path = args.pdf
    else:
        pdf_path = os.path.abspath(
            f"{DEFAULT_PATH}/tests/samples/A_Comprehensive_Review_of_Low_Rank_Adaptation_in_Large_Language_Models_for_Efficient_Parameter_Tuning-1.pdf"
        )
        print(f"Using sample PDF: {pdf_path}")

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return

    if args.save:
        output_dir = "table_visualizations"
        os.makedirs(output_dir, exist_ok=True)
        print(f"Visualizations will be saved to {output_dir}/")

    print(f"Visualizing table detection on page {args.page}")
    if args.save:
        detection_output = os.path.join(output_dir, f"detection_page{args.page}.png")
        results = adaptor.visualize_table_detection(
            pdf_path, args.page, save_path=detection_output
        )
        print(f"Detection visualization saved to {detection_output}")
    else:
        results = adaptor.visualize_table_detection(pdf_path, args.page)

    tables = adaptor.detect_tables(adaptor.extract_page_image(pdf_path, args.page))
    if not tables:
        print(f"No tables detected on page {args.page}")
        return

    print(f"Visualizing structure of table {args.table} on page {args.page}")
    if args.save:
        structure_output = os.path.join(
            output_dir, f"structure_page{args.page}_table{args.table}.png"
        )
        adaptor.visualize_table_structure(
            pdf_path, args.page, args.table, save_path=structure_output
        )
        print(f"Structure visualization saved to {structure_output}")
    else:
        adaptor.visualize_table_structure(pdf_path, args.page, args.table)

    tables = adaptor.extract_tables(pdf_path, args.page)
    print(f"Found {len(tables)} tables on page {args.page}")

    for i, table in enumerate(tables):
        if i != args.table:
            continue

        print(f"\nTable {i}:")
        print(f"  Rows: {table['n_rows']}")
        print(f"  Columns: {table['n_cols']}")
        print(f"  Detection score: {table['metadata']['detection_score']:.4f}")

        if table["data"]:
            print("\nStructured Table Data:")
            for row_idx, row in enumerate(table["data"]):
                if row_idx < 5:
                    print(f"  Row {row_idx + 1}:")
                    for header, value in row.items():
                        if value:
                            print(f"    {header}: {value}")

            if len(table["data"]) > 5:
                print(f"  ... and {len(table['data']) - 5} more rows")
        else:
            print("  No structured data available")


if __name__ == "__main__":
    main()
