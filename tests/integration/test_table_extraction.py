#!/usr/bin/env python3
"""
Test table extraction on actual PDF file
"""
import os

from table_rag.frameworks.table_extraction_factory import TableExtractionService


def test_actual_table_extraction():
    """Test table extraction on the sample PDF"""
    print("✅ Creating table extraction service...")
    service = TableExtractionService(device="cpu")

    # Sample PDF path
    pdf_path = "tests/samples/A_Comprehensive_Review_of_Low_Rank_Adaptation_in_Large_Language_Models_for_Efficient_Parameter_Tuning-1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print(f"\n🔍 Testing with sample PDF: {os.path.basename(pdf_path)}")
        result = service.extract_tables_from_page(pdf_path, 4)
        
        if result["success"]:
            print("✅ Successfully processed page 4")
            print(f"📊 Found {len(result['tables'])} table(s)")
        else:
            print(f"⚠️ Processing failed: {result.get('error', 'Unknown error')}")

        print("\n🎉 Clean Architecture demo completed successfully!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_actual_table_extraction()
