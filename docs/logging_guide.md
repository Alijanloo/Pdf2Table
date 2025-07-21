# Logging Setup for Pdf2Table

This document describes the logging configuration and usage for the Pdf2Table project.

## Overview

The project uses a centralized logging system that follows Clean Architecture principles. The logging configuration is located in the frameworks layer (`pdf2table/frameworks/logging_config.py`) as it's an infrastructure concern.

## Features

- **Centralized Configuration**: Single point for logging setup
- **Multiple Output Targets**: Console and file output
- **Log Rotation**: Automatic log file rotation with configurable size limits
- **Multiple Log Levels**: Support for DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Flexible Formatting**: Simple, detailed, and JSON-style formats
- **Context Managers**: Temporary log level changes
- **Decorators**: Automatic function call and execution time logging
- **Environment Configuration**: Configure via environment variables

## Quick Start

### Usage

```python
from pdf2table import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Log messages
logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")
```

## Colored Console Output

The logging system includes colored console output to make log levels easily distinguishable. The entire log header (timestamp, logger name, level, filename, and function) is colored according to the log level:

- **DEBUG**: Cyan header
- **INFO**: Green header
- **WARNING**: Yellow header
- **ERROR**: Red header
- **CRITICAL**: Magenta header

All headers are displayed in **bold** for better visibility. Only the message portion remains uncolored for readability.

## Log Files

By default, logs are written to the `logs/` directory in the project root:

- `pdf2table.log`: Main application log (all levels)
- `pdf2table_errors.log`: Error-only log (ERROR and CRITICAL levels)

## Configuration Options

### Log Levels

- `DEBUG`: Detailed information for diagnosing problems
- `INFO`: General information about program execution
- `WARNING`: Something unexpected happened, but the software is still working
- `ERROR`: A serious problem occurred
- `CRITICAL`: A very serious error occurred

### Format Types

- `simple`: Basic timestamp, logger name, level, and message
- `detailed`: Includes filename, line number, and function name
- `json`: Pipe-separated format for easy parsing

### Environment Variables

You can configure logging using environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export PDF2TABLE_LOG_LEVEL=DEBUG

# Log directory (optional, defaults to project_root/logs)
export PDF2TABLE_LOG_DIR=/path/to/custom/logs

# Enable/disable console output (true/false)
export PDF2TABLE_CONSOLE_OUTPUT=true

# Enable/disable file output (true/false)
export PDF2TABLE_FILE_OUTPUT=true

# Log format type (simple, detailed, json)
export PDF2TABLE_LOG_FORMAT=detailed

# Enable/disable colored console output (true/false)
export PDF2TABLE_USE_COLORS=true

# Maximum log file size in bytes (default: 10MB)
export PDF2TABLE_LOG_MAX_BYTES=10485760

# Number of backup log files to keep (default: 5)
export PDF2TABLE_LOG_BACKUP_COUNT=5
```

## Usage Examples

### Using Decorators

```python
from pdf2table.frameworks.logging_config import log_function_call, log_execution_time

@log_function_call(level="INFO")
@log_execution_time(level="INFO")
def my_function():
    # Function automatically logs entry/exit and execution time
    pass
```

### Context Managers

```python
from pdf2table import get_logger
from pdf2table.frameworks.logging_config import LogLevel

logger = get_logger(__name__)

# Temporarily change log level
with LogLevel(logger, "DEBUG"):
    logger.debug("This debug message will be shown")
```

## Integration with Existing Code

The logging system is automatically initialized when you import the `pdf2table` package. Existing modules can easily add logging by:

1. Import the logger: `from pdf2table import get_logger`
2. Create a logger instance: `logger = get_logger(__name__)`
3. Use the logger: `logger.info("Message")`

## Troubleshooting

### Log Files Not Created

- Check that the logs directory exists and is writable
- Verify file_output is enabled in configuration
- Check disk space

### Performance Concerns

- Avoid DEBUG level in production
- Use log rotation to manage file sizes
- Consider disabling file output for high-performance scenarios
