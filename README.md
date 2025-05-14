# TableRag

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

- `table_rag/`: Main package
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

## Usage

```python
from table_rag.usecases.indexing_pipeline import IndexingPipeline

# Initialize the pipeline
pipeline = IndexingPipeline(pdf_path="path/to/your.pdf", es_index="your-index-name")

# Run the pipeline
pipeline.run()
```

## API

The application exposes a FastAPI endpoint for PDF indexing:

```bash
# Start the API server
uvicorn table_rag.frameworks.main:app --reload
```

Then POST a PDF file to `/index-pdf/` to process it.

## Requirements

See requirements.txt for a complete list of dependencies.