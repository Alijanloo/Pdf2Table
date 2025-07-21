# Pdf2Table

A Python library for detecting, extracting, and processing tables from PDF documents.

## Overview

This project provides a robust solution for extracting tabular data from PDF documents. The library utilizes advanced computer vision models to detect and recognize table structures, making it easy to convert PDF tables into structured data formats.

## Technologies Used

- **Table Transformer**: For recognizing table structures in PDF documents.
- **PyMuPDF**: For reading PDF files.

## Features

- PDF processing with page-by-page table detection
- Table structure recognition using Table Transformer
- Clean architecture with separation of concerns

## Project Structure

- `pdf2table/`: Main package
  - `adaptors/`: Interface with external systems(PDF reader, Table Transformer)
  - `entities/`: Domain models
  - `usecases/`: Application logic
  - `frameworks/`: UI and infrastructure
- `tests/`: Unit tests
  - `adaptors/`: Tests for adaptors
  - `samples/`: Sample PDFs for testing

## Installation

```bash
# Install the package in development mode
pip install -e .
```

### Usage
```python
from pdf2table.frameworks.table_extraction_factory import TableExtractionFactory
from pdf2table.usecases.dtos import TableExtractionRequest

# Initialize the factory
factory = TableExtractionFactory()
adapter = factory.create_table_extraction_adapter()

# Extract tables from PDF
request = TableExtractionRequest(pdf_path="document.pdf", page_number=0)
response = adapter.extract_tables(request)

# Access extracted tables
for table in response.tables:
    print(f"Table with {len(table.grid.cells)} cells")
    print(f"Grid size: {table.grid.rows} x {table.grid.columns}")
    
    # Convert to structured format
    table_data = table.to_dict()
    print(table_data)
```

### High-Level Usage

For simpler integration, use the high-level `TableExtractionService`:

```python
from pdf2table.frameworks.table_extraction_factory import TableExtractionService

# Initialize the service
service = TableExtractionService(device="cpu")

# Extract tables from a single page
page_result = service.extract_tables_from_page("document.pdf", page_number=0)
print(f"Found {len(page_result['tables'])} tables on page 0")

# Extract tables from entire PDF
all_results = service.extract_tables_from_pdf("document.pdf")
for page_idx, page_result in enumerate(all_results):
    if page_result.get('success', True):
        tables = page_result.get('tables', [])
        print(f"Page {page_idx}: Found {len(tables)} tables")
        
        # Process each table
        for table_idx, table in enumerate(tables):
            print(f"  Table {table_idx + 1}: {table['rows']} rows x {table['columns']} columns")
    else:
        print(f"Page {page_idx}: Error - {page_result.get('error', 'Unknown error')}")
```

## 📋 Logging

The project includes comprehensive logging capabilities for debugging and monitoring:

**Log Files**: By default, logs are written to:
- `logs/pdf2table.log` - Main application log
- `logs/pdf2table_errors.log` - Error-only log

**Documentation**: See `docs/logging_guide.md` for detailed logging documentation.

## 🎯 Use Cases

### Document Processing Pipelines
- **Financial Reports**: Extract financial tables from annual reports and earnings statements
- **Research Papers**: Extract data tables from scientific publications
- **Invoice Processing**: Extract line items and totals from invoices
- **Government Documents**: Process regulatory filings and public documents

### Integration Scenarios
- **Data Analytics**: Feed extracted data into analytical workflows  
- **Document Management**: Enhance document search with structured table data
- **Compliance**: Automated extraction for regulatory compliance reporting
- **Business Intelligence**: Convert PDF reports into structured datasets for analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow Clean Architecture principles
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Microsoft Research**: Table Transformer models
- **Hugging Face**: TrOCR and Transformers library  
- **PyMuPDF Team**: Excellent PDF processing capabilities
