# Pdf2Table

A RAG (Retrieval-Augmented Generation) application for detecting, extracting, and indexing tables from PDF documents and finally inferring on them.

## Overview

This project aims to provide a robust solution for extracting tabular data from PDF documents and indexing it for efficient retrieval. The application utilizes various technologies, including FastAPI for the web framework, Elasticsearch for indexing and searching, and LangChain for text chunking and processing.

## Technologies Used

- **FastAPI**: For building the web application.
- **Elasticsearch**: For storing and retrieving indexed data.
- **LangChain**: For text chunking and processing.
- **Table Transformer**: For recognizing table structures in PDF documents.
- **PyMuPDF**: For reading PDF files.

## Features

- PDF processing with page-by-page table detection
- Table structure recognition using Table Transformer
- Text chunking with LangChain's character splitter
- Elasticsearch indexing for structured retrieval
- Clean architecture with separation of concerns

## Project Structure

- `pdf2table/`: Main package
  - `adaptors/`: Interface with external systems (Elasticsearch, PDF reader, Table Transformer)
  - `entities/`: Domain models
  - `usecases/`: Application logic
  - `frameworks/`: UI and infrastructure (FastAPI)
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


## 🎯 Use Cases

### Document Processing Pipelines
- **Financial Reports**: Extract financial tables from annual reports and earnings statements
- **Research Papers**: Extract data tables from scientific publications
- **Invoice Processing**: Extract line items and totals from invoices
- **Government Documents**: Process regulatory filings and public documents

### Integration Scenarios
- **RAG Systems**: Index extracted tables for question-answering systems
- **Data Analytics**: Feed extracted data into analytical workflows  
- **Document Management**: Enhance document search with structured table data
- **Compliance**: Automated extraction for regulatory compliance reporting

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
