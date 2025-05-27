# Script Selector Features

## Overview
Added a comprehensive script selector to the View menu that allows users to discover and run Python scripts from within the GUI application.

## Features Added

### 1. View Menu Integration
- **Location**: View > Run Script submenu
- **Refresh Option**: View > Refresh Scripts command
- **Auto-discovery**: Scripts are automatically discovered on startup

### 2. Script Discovery
- **Scope**: Recursively finds all `.py` files in the workspace
- **Exclusions**: Automatically excludes:
  - `gui.py` (the GUI itself)
  - Files in `__pycache__`, `.git`, `venv`, `env`, `node_modules`
- **Sorting**: Scripts are sorted alphabetically
- **Display**: Shows filename for simple scripts, full path for nested ones

### 3. Script Execution
- **Background Execution**: Scripts run in separate processes without blocking the GUI
- **Timeout Protection**: 5-minute execution timeout to prevent hanging
- **Status Updates**: Real-time status updates in the status bar
- **Error Handling**: Comprehensive error handling and reporting

### 4. Output Display
- **Output Dialog**: Custom dialog window showing script results
- **Tabbed Interface**:
  - "Standard Output" tab for normal output
  - "Error Output" tab for error messages
- **Success/Failure Indicators**: Visual indicators for script execution status
- **Read-only Display**: Output is displayed in read-only text widgets with syntax highlighting

### 5. Utility Features
- **Open Script Folder**: Quick access to open the workspace in file manager
- **Refresh Scripts**: Manual refresh of available scripts
- **Cross-platform**: Works on Windows, macOS, and Linux

## Methods Added

### Core Methods
- `_discover_scripts()` - Finds Python scripts in workspace
- `_update_script_menu()` - Populates the script menu
- `_run_script(script_path)` - Executes selected script
- `_show_script_output()` - Displays script results
- `_open_script_folder()` - Opens workspace in file manager

### Integration
- Updated `create_menu_bar()` to add script selector submenu
- Updated `bind_events()` to initialize script menu on startup

## Usage
1. **Access**: View > Run Script
2. **Select Script**: Click on any discovered Python script
3. **View Results**: Output automatically displayed in dialog
4. **Refresh**: Use View > Refresh Scripts to update available scripts
5. **Browse**: Use "Open Script Folder" to explore workspace

## Benefits
- **Integrated Workflow**: Run analysis scripts without leaving the GUI
- **User-Friendly**: No need to open terminal or command prompt
- **Safe Execution**: Timeout protection and error containment
- **Comprehensive Feedback**: Full output capture and display
- **Cross-Platform**: Works consistently across operating systems

## Example Scripts
- `test_script_demo.py` - Demonstrates successful execution
- `test_script_error.py` - Shows error handling capabilities
