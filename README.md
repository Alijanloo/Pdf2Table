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
from pdf2table.frameworks.pipeline import create_pipeline

# Create the extraction pipeline with configuration
pipeline = create_pipeline(
    device="cpu",
    detection_threshold=0.9,
    structure_threshold=0.6,
    pdf_dpi=300,
    load_ocr=False,
    visualize=False
)

# Extract tables from a specific page
tables = pipeline.extract_tables(pdf_path="document.pdf", page_number=0)

# Or extract tables from all pages
all_tables = pipeline.extract_tables(pdf_path="document.pdf")

# Access extracted tables
for table in tables:
    print(f"Table with {len(table.grid.cells)} cells")
    print(f"Grid size: {table.grid.n_rows} x {table.grid.n_cols}")
    
    # Convert to structured format
    table_data = table.to_dict()
    print(table_data)
```

### Configuration Options

The `create_pipeline()` method accepts the following parameters:

- `device` (str): Device for ML models - "cpu" or "cuda" (default: "cpu")
- `detection_threshold` (float): Confidence threshold for table detection (default: 0.9)
- `structure_threshold` (float): Confidence threshold for structure recognition (default: 0.6)
- `pdf_dpi` (int): DPI for PDF page rendering (default: 300)
- `load_ocr` (bool): Whether to load OCR service (default: False)
- `visualize` (bool): Whether to enable visualization (default: False)
- `visualization_save_dir` (str): Directory to save visualizations (default: "data/table_visualizations")

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
