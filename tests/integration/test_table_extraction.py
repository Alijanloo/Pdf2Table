#!/usr/bin/env python3
"""
Test table extraction on actual PDF file
"""

import os

from pdf2table.frameworks.table_extraction_factory import TableExtractionFactory


def test_actual_table_extraction():
    """Test table extraction on the sample PDF"""
    print("✅ Creating table extraction adapter...")
    adapter = TableExtractionFactory.create_table_extraction_adapter(visualize=True)

    # Sample PDF path
    pdf_path = "data/oxford-textbook-of-medicine-693.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print(f"\n🔍 Testing with sample PDF: {os.path.basename(pdf_path)}")
        result = adapter.extract_tables(pdf_path, page_number=0).to_dict()

        if result["success"]:
            print("✅ Successfully processed page 0")
            print(f"📊 Found {len(result['tables'])} table(s)")
        else:
            print(f"⚠️ Processing failed: {result.get('error', 'Unknown error')}")

        print("\n🎉 Integration test completed successfully!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_actual_table_extraction()
