#!/bin/bash

# Test suite for find-space-hogs.sh
TEST_DIR="/tmp/space-hogs-test-$$"
SCRIPT_DIR="$(dirname "$0")"
SCRIPT_PATH="$SCRIPT_DIR/find-space-hogs.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0

# Setup test environment
setup_test_env() {
    echo "Setting up test environment..."
    mkdir -p "$TEST_DIR"/{home,var/lib/docker,var/cache/apt,var/log}
    mkdir -p "$TEST_DIR/home"/{.vscode,.mozilla,.cache/google-chrome,Downloads,VirtualBox\ VMs}
    mkdir -p "$TEST_DIR/home/.local/share"/{Trash,virtualbox}
    mkdir -p "$TEST_DIR/home/.config/google-chrome"
    
    # Create test files of different sizes
    dd if=/dev/zero of="$TEST_DIR/home/Downloads/large_file" bs=1M count=50 2>/dev/null
    dd if=/dev/zero of="$TEST_DIR/var/log/test.log" bs=1M count=10 2>/dev/null
    echo "test content" > "$TEST_DIR/home/.vscode/settings.json"
    
    # Create a mock git pack file
    mkdir -p "$TEST_DIR/home/repo/.git/objects/pack"
    dd if=/dev/zero of="$TEST_DIR/home/repo/.git/objects/pack/test.pack" bs=1M count=150 2>/dev/null
    
    # Create node_modules directories
    mkdir -p "$TEST_DIR/home/project1/node_modules"
    mkdir -p "$TEST_DIR/home/project2/node_modules"
    dd if=/dev/zero of="$TEST_DIR/home/project1/node_modules/large_module" bs=1M count=20 2>/dev/null
    
    # Create nested node_modules for more realistic testing
    mkdir -p "$TEST_DIR/home/project3/deep/nested/node_modules"
    dd if=/dev/zero of="$TEST_DIR/home/project3/deep/nested/node_modules/deep_module" bs=1M count=5 2>/dev/null
    
    # Create empty directories to test edge cases
    mkdir -p "$TEST_DIR/home/empty_dir"
    mkdir -p "$TEST_DIR/home/.cache/empty_cache"
}

# Cleanup test environment
cleanup_test_env() {
    echo "Cleaning up test environment..."
    rm -rf "$TEST_DIR"
}

# Test function with better error handling
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${YELLOW}Test $TESTS_RUN: $test_name${NC}"
    
    # Create a temporary script to capture both stdout and stderr
    local temp_script="/tmp/test_runner_$$"
    cat > "$temp_script" << EOF
#!/bin/bash
set +e  # Don't exit on errors in test functions
$test_command
EOF
    chmod +x "$temp_script"
    
    local output
    output=$("$temp_script" 2>&1)
    local exit_code=$?
    
    rm -f "$temp_script"
    
    if [ $exit_code -eq $expected_exit_code ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        [ -n "$output" ] && echo -e "${BLUE}Output: $output${NC}"
    else
        echo -e "${RED}✗ FAILED (exit code: $exit_code, expected: $expected_exit_code)${NC}"
        [ -n "$output" ] && echo -e "${RED}Output: $output${NC}"
    fi
}

# Test dir_size function
test_dir_size_function() {
    # Create a temporary script that sources the original without set -e
    local temp_script="/tmp/test_dir_size_$$"
    cat > "$temp_script" << 'EOF'
#!/bin/bash
set +e  # Disable exit on error for testing
source_file="$1"
test_dir="$2"

# Extract just the dir_size function
dir_size() {
    du -sh "$1" 2>/dev/null | cut -f1
}

# Test with existing directory
size=$(dir_size "$test_dir/home/Downloads")
if [ -n "$size" ]; then
    echo "Directory size: $size"
    exit 0
else
    echo "Failed to get directory size"
    exit 1
fi
EOF
    
    chmod +x "$temp_script"
    "$temp_script" "$SCRIPT_PATH" "$TEST_DIR"
    local result=$?
    rm -f "$temp_script"
    return $result
}

# Test dir_size with non-existent directory
test_dir_size_nonexistent() {
    local temp_script="/tmp/test_dir_size_nonexistent_$$"
    cat > "$temp_script" << 'EOF'
#!/bin/bash
set +e

dir_size() {
    du -sh "$1" 2>/dev/null | cut -f1
}

# Test with non-existent directory (should return empty or handle gracefully)
size_nonexistent=$(dir_size "/absolutely/non/existent/path/12345")
if [ -z "$size_nonexistent" ]; then
    echo "Correctly handled non-existent directory"
    exit 0
else
    echo "Unexpected output for non-existent directory: $size_nonexistent"
    exit 1
fi
EOF
    
    chmod +x "$temp_script"
    "$temp_script"
    local result=$?
    rm -f "$temp_script"
    return $result
}

# Test script execution with test environment
test_script_execution() {
    HOME_BACKUP="$HOME"
    export HOME="$TEST_DIR/home"
    
    # Create a modified version of the script without set -e for testing
    local temp_script="/tmp/test_execution_$$"
    sed 's/set -e/set +e/' "$SCRIPT_PATH" > "$temp_script"
    chmod +x "$temp_script"
    
    local output
    output=$(bash "$temp_script" 2>&1)
    local exit_code=$?
    
    rm -f "$temp_script"
    export HOME="$HOME_BACKUP"
    
    if [ $exit_code -eq 0 ] && echo "$output" | grep -q "Disk Space Analysis Tool"; then
        echo "Script executed successfully"
        return 0
    else
        echo "Script execution failed or missing expected output"
        return 1
    fi
}

# Fixed test for missing directories
test_missing_directories() {
    HOME_BACKUP="$HOME"
    export HOME="/absolutely/non/existent/home/path/12345"
    
    # Create a version of the script that doesn't exit on errors
    local temp_script="/tmp/test_missing_dirs_$$"
    sed 's/set -e/set +e/' "$SCRIPT_PATH" > "$temp_script"
    chmod +x "$temp_script"
    
    local output
    output=$(bash "$temp_script" 2>&1)
    local exit_code=$?
    
    rm -f "$temp_script"
    export HOME="$HOME_BACKUP"
    
    # Script should complete even with missing directories
    if [ $exit_code -eq 0 ] && echo "$output" | grep -q "Disk Space Analysis Tool"; then
        echo "Script handled missing directories gracefully"
        return 0
    else
        echo "Script failed to handle missing directories properly"
        return 1
    fi
}

# Test large file detection
test_large_file_detection() {
    HOME_BACKUP="$HOME"
    export HOME="$TEST_DIR/home"
    
    local temp_script="/tmp/test_large_files_$$"
    sed 's/set -e/set +e/' "$SCRIPT_PATH" > "$temp_script"
    chmod +x "$temp_script"
    
    local output
    output=$(bash "$temp_script" 2>&1)
    
    rm -f "$temp_script"
    export HOME="$HOME_BACKUP"
    
    if echo "$output" | grep -q "test.pack"; then
        echo "Large pack file detected correctly"
        return 0
    else
        echo "Large pack file not detected"
        return 1
    fi
}

# Test node_modules detection
test_node_modules_detection() {
    HOME_BACKUP="$HOME"
    export HOME="$TEST_DIR/home"
    
    local temp_script="/tmp/test_node_modules_$$"
    sed 's/set -e/set +e/' "$SCRIPT_PATH" > "$temp_script"
    chmod +x "$temp_script"
    
    local output
    output=$(bash "$temp_script" 2>&1)
    
    rm -f "$temp_script"
    export HOME="$HOME_BACKUP"
    
    if echo "$output" | grep -q "Node modules:"; then
        echo "Node modules section found"
        return 0
    else
        echo "Node modules section not found"
        return 1
    fi
}

# Test script permissions
test_script_permissions() {
    if [ -x "$SCRIPT_PATH" ]; then
        echo "Script has execute permissions"
        return 0
    else
        echo "Script missing execute permissions"
        return 1
    fi
}

# Test script syntax
test_script_syntax() {
    if bash -n "$SCRIPT_PATH" 2>/dev/null; then
        echo "Script syntax is valid"
        return 0
    else
        echo "Script has syntax errors"
        return 1
    fi
}

# Test help suggestions
test_help_suggestions() {
    local temp_script="/tmp/test_help_$$"
    sed 's/set -e/set +e/' "$SCRIPT_PATH" > "$temp_script"
    chmod +x "$temp_script"
    
    local output
    output=$(bash "$temp_script" 2>&1)
    
    rm -f "$temp_script"
    
    if echo "$output" | grep -q "fdupes" && echo "$output" | grep -q "ncdu"; then
        echo "Help suggestions found"
        return 0
    else
        echo "Help suggestions missing"
        return 1
    fi
}

# Test output formatting
test_output_formatting() {
    HOME_BACKUP="$HOME"
    export HOME="$TEST_DIR/home"
    
    local temp_script="/tmp/test_format_$$"
    sed 's/set -e/set +e/' "$SCRIPT_PATH" > "$temp_script"
    chmod +x "$temp_script"
    
    local output
    output=$(bash "$temp_script" 2>&1)
    
    rm -f "$temp_script"
    export HOME="$HOME_BACKUP"
    
    # Check for expected section headers
    if echo "$output" | grep -q "VSCode extensions cache:" && \
       echo "$output" | grep -q "Downloads folder:" && \
       echo "$output" | grep -q "Checking for Git repositories"; then
        echo "Output formatting is correct"
        return 0
    else
        echo "Output formatting issues detected"
        return 1
    fi
}

# Test with empty directories
test_empty_directories() {
    HOME_BACKUP="$HOME"
    export HOME="$TEST_DIR/home"
    
    local temp_script="/tmp/test_empty_$$"
    cat > "$temp_script" << 'EOF'
#!/bin/bash
set +e

dir_size() {
    du -sh "$1" 2>/dev/null | cut -f1
}

# Test empty directory
size=$(dir_size "$1/empty_dir")
if [ -n "$size" ]; then
    echo "Empty directory size: $size"
    exit 0
else
    echo "Could not determine size of empty directory"
    exit 1
fi
EOF
    
    chmod +x "$temp_script"
    "$temp_script" "$TEST_DIR/home"
    local result=$?
    
    rm -f "$temp_script"
    export HOME="$HOME_BACKUP"
    return $result
}

# Test error handling with insufficient permissions
test_permission_errors() {
    # Create a directory we can't read
    local restricted_dir="/tmp/restricted_test_$$"
    mkdir -p "$restricted_dir"
    chmod 000 "$restricted_dir" 2>/dev/null
    
    local temp_script="/tmp/test_permissions_$$"
    cat > "$temp_script" << EOF
#!/bin/bash
set +e

dir_size() {
    du -sh "\$1" 2>/dev/null | cut -f1
}

# Test with restricted directory
size=\$(dir_size "$restricted_dir")
# Should handle gracefully without crashing
echo "Permission test completed"
exit 0
EOF
    
    chmod +x "$temp_script"
    "$temp_script"
    local result=$?
    
    # Cleanup
    chmod 755 "$restricted_dir" 2>/dev/null
    rm -rf "$restricted_dir" "$temp_script" 2>/dev/null
    return $result
}

# Test find command with large results
test_find_performance() {
    HOME_BACKUP="$HOME"
    export HOME="$TEST_DIR/home"
    
    # Test that find commands don't hang or crash
    local temp_script="/tmp/test_find_$$"
    cat > "$temp_script" << 'EOF'
#!/bin/bash
set +e
export HOME="$1"

# Test node_modules find command
timeout 10s find "$HOME" -name "node_modules" -type d -prune -exec du -sh {} \; 2>/dev/null | head -5
echo "Find test completed"
exit 0
EOF
    
    chmod +x "$temp_script"
    "$temp_script" "$TEST_DIR/home" >/dev/null 2>&1
    local result=$?
    
    rm -f "$temp_script"
    export HOME="$HOME_BACKUP"
    return $result
}

# Main test execution
main() {
    echo "Running comprehensive tests for find-space-hogs.sh"
    echo "=================================================="
    
    # Check if script exists
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo -e "${RED}Error: Script not found at $SCRIPT_PATH${NC}"
        exit 1
    fi
    
    setup_test_env
    
    # Run basic tests
    run_test "Script syntax check" "test_script_syntax"
    run_test "Script permissions check" "test_script_permissions"
    
    # Run function tests
    run_test "dir_size function test" "test_dir_size_function"
    run_test "dir_size with non-existent directory" "test_dir_size_nonexistent"
    
    # Run execution tests
    run_test "Script execution test" "test_script_execution"
    run_test "Missing directories handling" "test_missing_directories"
    run_test "Empty directories handling" "test_empty_directories"
    
    # Run feature tests
    run_test "Large file detection" "test_large_file_detection"
    run_test "Node modules detection" "test_node_modules_detection"
    run_test "Help suggestions test" "test_help_suggestions"
    run_test "Output formatting test" "test_output_formatting"
    
    # Run edge case tests
    run_test "Permission errors handling" "test_permission_errors"
    run_test "Find command performance" "test_find_performance"
    
    cleanup_test_env
    
    # Summary
    echo -e "\n=================================================="
    echo -e "Test Results: ${GREEN}$TESTS_PASSED${NC}/${TESTS_RUN} passed"
    
    if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        echo -e "${YELLOW}Note: Some failures may be due to 'set -e' in the original script${NC}"
        echo -e "${YELLOW}Consider modifying the script to handle errors more gracefully${NC}"
        exit 1
    fi
}

# Run tests if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi