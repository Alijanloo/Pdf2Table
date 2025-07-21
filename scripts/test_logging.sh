#!/bin/bash
# Test script for validating the logging setup using uv run.
# This script demonstrates the recommended way to run Python code in this project.

echo "Pdf2Table Logging Setup Test"
echo "============================="

# Test basic logging import and functionality
echo "1. Testing basic logging setup..."
cat > /tmp/test_basic_logging.py << 'EOF'
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

try:
    from pdf2table import get_logger, setup_logging
    logger = get_logger('test')
    logger.info('✓ Logging setup test successful')
    print('✓ Logging imports work correctly')
    print('✓ Logger created successfully') 
    print('✓ Log message sent')
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)
EOF

uv run /tmp/test_basic_logging.py

if [ $? -eq 0 ]; then
    echo "✓ Basic logging test passed"
else
    echo "✗ Basic logging test failed"
    exit 1
fi

# Test with debug level
echo ""
echo "2. Testing debug level logging..."
cat > /tmp/test_debug_logging.py << 'EOF'
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
from pathlib import Path

project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from pdf2table import get_logger
logger = get_logger('debug_test')
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
print('✓ Debug level logging test completed')
EOF

PDF2TABLE_LOG_LEVEL=DEBUG uv run /tmp/test_debug_logging.py

# Test logging demo script
echo ""
echo "3. Testing simple logging test script..."
if [ -f "examples/simple_logging_test.py" ]; then
    echo "Running simple logging test with uv run..."
    uv run examples/simple_logging_test.py > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Simple logging test script executed successfully"
    else
        echo "✗ Simple logging test script failed"
        exit 1
    fi
else
    echo "✗ Simple logging test script not found"
    exit 1
fi

# Check if log files were created
echo ""
echo "4. Checking log file creation..."
if [ -d "logs" ]; then
    if [ -f "logs/pdf2table.log" ]; then
        echo "✓ Main log file created: logs/pdf2table.log"
        echo "  Last few entries:"
        tail -3 logs/pdf2table.log | sed 's/^/    /'
    else
        echo "? Main log file not found (may not have been created yet)"
    fi
    
    if [ -f "logs/pdf2table_errors.log" ]; then
        echo "✓ Error log file exists: logs/pdf2table_errors.log"
    else
        echo "? Error log file not found (normal if no errors occurred)"
    fi
else
    echo "? Logs directory not found (may be created on first use)"
fi

echo ""
echo "============================="
echo "Logging setup validation completed!"
echo ""
echo "Usage examples:"
echo "  uv run examples/simple_logging_test.py"
echo "  PDF2TABLE_LOG_LEVEL=DEBUG uv run examples/simple_logging_test.py"
echo "  uv run --python 3.11 examples/simple_logging_test.py"
echo ""
echo "Cleanup temporary files..."
rm -f /tmp/test_basic_logging.py /tmp/test_debug_logging.py
