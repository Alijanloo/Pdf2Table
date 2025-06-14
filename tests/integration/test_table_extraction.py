#!/usr/bin/env python3
"""
Test table extraction on actual PDF file
"""

import os

from table_rag.frameworks.table_extraction_factory import TableExtractionFactory
from table_rag.usecases.dtos import TableExtractionRequest


def test_actual_table_extraction():
    """Test table extraction on the sample PDF"""
    print("✅ Creating table extraction adapter...")
    adapter = TableExtractionFactory.create_table_extraction_adapter(visualize=True)

    # Sample PDF path
    pdf_path = "tests/samples/A_Comprehensive_Review_of_Low_Rank_Adaptation_in_Large_Language_Models_for_Efficient_Parameter_Tuning-1.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print(f"\n🔍 Testing with sample PDF: {os.path.basename(pdf_path)}")
        request = TableExtractionRequest(pdf_path, 4)
        result = adapter.extract_tables(request).to_dict()

        if result["success"]:
            print("✅ Successfully processed page 4")
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
