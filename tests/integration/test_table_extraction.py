#!/usr/bin/env python3
"""
Test table extraction on actual PDF file
"""

import os

from pdf2table.frameworks.pipeline import create_pipeline


def test_actual_table_extraction():
    """Test table extraction on the sample PDF"""
    print("✅ Creating table extraction pipeline...")
    use_case = create_pipeline(visualize=True)

    pdf_path = "data/oxford-textbook-of-medicine-693.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print(f"\n🔍 Testing with sample PDF: {os.path.basename(pdf_path)}")
        tables = use_case.extract_tables(pdf_path, page_number=0)

        print("✅ Successfully processed page 0")
        print(f"📊 Found {len(tables)} table(s)")

        print("\n🎉 Integration test completed successfully!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_actual_table_extraction()
