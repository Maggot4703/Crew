"""
ScriptManager Module
===================

Handles all script-related functionality for the CrewGUI application, including:
- Script discovery and validation
- Script execution with proper threading and error handling
- Script menu population and management
- Script directory operations

This module separates script logic from the main GUI class for better maintainability.
"""

import os
import glob
import subprocess
import threading
import logging
from typing import Callable, Optional, List, Dict, Any, Tuple
import tkinter as tk
from tkinter import messagebox


class ScriptDiscovery:
    """Handle script discovery and validation - NO UI dependencies"""
    
    def __init__(self, scripts_dir: str):
        self.scripts_dir = scripts_dir
    
    def get_script_files(self) -> List[str]:
        """Get list of available script files"""
        if not os.path.exists(self.scripts_dir):
            return []
        
        try:
            script_files = glob.glob(os.path.join(self.scripts_dir, "*.py"))
            # Filter out potentially problematic files
            safe_scripts = []
            
            skip_patterns = ["__", "test_", "_test", "temp", "backup"]
            
            for script_path in script_files:
                script_name = os.path.basename(script_path).lower()
                
                # Skip files with problematic patterns
                if any(pattern in script_name for pattern in skip_patterns):
                    continue
                    
                # Basic safety check - ensure file is readable
                try:
                    with open(script_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline()
                        # Skip if it looks like a main execution script
                        if 'if __name__' in first_line:
                            continue
                except (IOError, UnicodeDecodeError):
                    continue
                
                safe_scripts.append(script_path)
            
            return sorted(safe_scripts)
            
        except Exception as e:
            logging.error(f"Error discovering scripts: {e}")
            return []
    
    def validate_script_dir(self) -> Tuple[bool, str]:
        """Validate scripts directory, return (is_valid, message)"""
        if not self.scripts_dir:
            return False, "Scripts dir not configured"
        
        if not os.path.exists(self.scripts_dir):
            return False, "Scripts dir missing"
        
        if not os.path.isdir(self.scripts_dir):
            return False, "Scripts path is not a directory"
        
        try:
            # Test if directory is accessible
            os.listdir(self.scripts_dir)
            return True, "OK"
        except PermissionError:
            return False, "Permission denied"
        except Exception as e:
            return False, f"Access error: {str(e)[:50]}"
    
    def get_script_info(self, script_path: str) -> Dict[str, Any]:
        """Get metadata about a script file"""
        try:
            script_name = os.path.basename(script_path)
            file_size = os.path.getsize(script_path)
            mod_time = os.path.getmtime(script_path)
            
            # Try to extract docstring or first comment
            description = "No description"
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Read first 500 chars
                    
                    # Look for docstring
                    if '"""' in content:
                        start = content.find('"""') + 3
                        end = content.find('"""', start)
                        if end > start:
                            description = content[start:end].strip()
                    elif "'''" in content:
                        start = content.find("'''") + 3
                        end = content.find("'''", start)
                        if end > start:
                            description = content[start:end].strip()
                    elif content.strip().startswith('#'):
                        # Use first comment line
                        first_line = content.split('\n')[0]
                        if first_line.startswith('#'):
                            description = first_line[1:].strip()
            except Exception:
                pass
            
            return {
                'name': script_name,
                'path': script_path,
                'size': file_size,
                'modified': mod_time,
                'description': description[:100]  # Limit length
            }
            
        except Exception as e:
            logging.error(f"Error getting script info for {script_path}: {e}")
            return {
                'name': os.path.basename(script_path),
                'path': script_path,
                'size': 0,
                'modified': 0,
                'description': f"Error: {str(e)[:50]}"
            }


class ScriptManager:
    """Enhanced ScriptManager with comprehensive script handling capabilities"""
    
    def __init__(self, scripts_dir: str, ui_callback: Callable[[str, bool], None]):
        """
        Args:
            scripts_dir: Path to scripts directory
            ui_callback: Function to update UI status (message, is_error)
        """
        self.scripts_dir = scripts_dir
        self.update_status = ui_callback  # Dependency injection for UI updates
        self.script_discovery = ScriptDiscovery(scripts_dir)
        
    def populate_script_menu(self, menu: tk.Menu, root: tk.Tk, 
                           run_callback: Optional[Callable[[str], None]] = None) -> None:
        """Populate the script menu with available scripts using enhanced discovery
        
        Args:
            menu: Menu to populate
            root: Root window for threading
            run_callback: Optional callback for script execution (defaults to self.run_script)
        """
        try:
            menu.delete(0, tk.END)  # Clear existing items
            
            # Use enhanced script discovery logic
            is_valid, message = self.script_discovery.validate_script_dir()
            if not is_valid:
                menu.add_command(label=f"({message})", state=tk.DISABLED)
                return
            
            script_files = self.script_discovery.get_script_files()
            
            if not script_files:
                menu.add_command(label="No scripts found", state=tk.DISABLED)
            else:
                # Use provided callback or default to self.run_script
                script_runner = run_callback if run_callback else lambda sp: self.run_script(sp, root)
                
                for script_path in script_files:
                    script_name = os.path.basename(script_path)
                    menu.add_command(
                        label=script_name,
                        command=lambda sp=script_path, runner=script_runner: runner(sp)
                    )
                    
            # Add management options
            menu.add_separator()
            menu.add_command(
                label="Refresh Scripts", 
                command=lambda: self.populate_script_menu(menu, root, run_callback)
            )
            menu.add_command(
                label="Open Scripts Folder...", 
                command=self.open_scripts_folder
            )
                
        except Exception as e:
            logging.error(f"Error populating script menu: {e}")
            menu.delete(0, tk.END)
            menu.add_command(label="(Error loading scripts)", state=tk.DISABLED)
            menu.add_separator()
            menu.add_command(
                label="Refresh Scripts", 
                command=lambda: self.populate_script_menu(menu, root, run_callback)
            )
            menu.add_command(
                label="Open Scripts Folder...", 
                command=self.open_scripts_folder
            )
    
    def run_script(self, script_path: str, root: tk.Tk) -> None:
        """Public method to run a script - main entry point"""
        try:
            script_name = os.path.basename(script_path)
            self.update_status(f"Running script: {script_name}...", False)
            
            def target():
                try:
                    result = self._execute_script(script_path)
                    # Schedule UI updates on main thread
                    root.after(0, lambda: self._handle_script_result(result, script_name))
                except Exception as e:
                    root.after(0, lambda: self._handle_script_error(e, script_name))
                    
            threading.Thread(target=target, daemon=True).start()
            
        except Exception as e:
            logging.error(f"Error preparing to run script {script_path}: {e}")
            script_name = os.path.basename(script_path)
            messagebox.showerror("Script Error", f"Could not run script {script_name}: {e}")
            self.update_status(f"Failed to start script {script_name}.", True)
    
    def _run_script_with_ui(self, script_path: str, root: tk.Tk) -> None:
        """Internal method for UI callback compatibility"""
        self.run_script(script_path, root)
    
    def _execute_script(self, script_path: str) -> dict:
        """Execute script and return result - enhanced with better error handling"""
        try:
            logging.info(f"Executing script: python '{script_path}'")
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            proc = subprocess.Popen(
                ['python', script_path], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, 
                text=True,
                creationflags=flags, 
                cwd=self.scripts_dir
            )
            out, err = proc.communicate()
            
            return {
                'returncode': proc.returncode,
                'stdout': out,
                'stderr': err,
                'script_name': os.path.basename(script_path)
            }
            
        except Exception as e:
            logging.error(f"Exception during script execution: {e}")
            return {
                'returncode': -1,
                'stdout': "",
                'stderr': str(e),
                'script_name': os.path.basename(script_path),
                'exception': e
            }
    
    def _handle_script_result(self, result: dict, script_name: str) -> None:
        """Handle successful script execution with enhanced feedback"""
        if result['returncode'] == 0:
            self.update_status(f"Script '{script_name}' finished.", False)
            if result['stdout'].strip():
                messagebox.showinfo(f"{script_name} Output", result['stdout'])
            else:
                messagebox.showinfo(
                    f"{script_name} Finished", 
                    f"Script '{script_name}' completed with no output."
                )
        else:
            msg = f"Script '{script_name}' failed."
            if result['stderr'].strip():
                msg += f"\n\nError:\n{result['stderr']}"
            messagebox.showerror(f"{script_name} Error", msg)
            self.update_status(f"Script '{script_name}' failed.", True)
    
    def _handle_script_error(self, error: Exception, script_name: str) -> None:
        """Handle script execution errors with enhanced logging"""
        logging.error(f"Exception while running script {script_name}: {error}")
        messagebox.showerror("Script Execution Error", str(error))
        self.update_status(f"Error running {script_name}.", True)
    
    def open_scripts_folder(self) -> None:
        """Open scripts folder in file manager with cross-platform support"""
        if not self.scripts_dir or not os.path.isdir(self.scripts_dir):
            messagebox.showwarning("Error", "Scripts directory not configured or missing.")
            logging.warning("scripts_dir not configured or missing when opening folder.")
            return
            
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['explorer', self.scripts_dir], check=True)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', self.scripts_dir], check=True)
            self.update_status(f"Opened scripts folder: {self.scripts_dir}", False)
        except Exception as e:
            logging.error(f"Failed to open scripts folder: {e}")
            messagebox.showerror("Error", f"Could not open scripts folder: {e}")
    
    def get_script_files(self) -> List[str]:
        """Get list of available script files"""
        return self.script_discovery.get_script_files()
    
    def validate_script_directory(self) -> Tuple[bool, str]:
        """Validate scripts directory"""
        return self.script_discovery.validate_script_dir()
    
    def get_script_info(self, script_path: str) -> Dict[str, Any]:
        """Get metadata about a script file"""
        return self.script_discovery.get_script_info(script_path)
    
    def ensure_scripts_directory(self) -> bool:
        """Ensure scripts directory exists with proper error handling"""
        try:
            if not self.scripts_dir:
                self.update_status("Scripts directory path not configured", True)
                return False
                
            os.makedirs(self.scripts_dir, exist_ok=True)
            
            # Verify directory is writable
            test_file = os.path.join(self.scripts_dir, ".write_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception:
                self.update_status("Scripts directory is not writable", True)
                return False
            
            return True
            
        except PermissionError:
            self.update_status("Cannot create/write to scripts directory: Permission denied", True)
            messagebox.showerror("Error", "Permission denied for scripts directory")
            return False
            
        except Exception as e:
            self.update_status(f"Scripts directory error: {e}", True)
            messagebox.showerror("Error", f"Cannot setup scripts directory: {e}")
            return False
    
    def create_sample_script(self) -> bool:
        """Create a sample script file for demonstration purposes"""
        try:
            if not self.ensure_scripts_directory():
                return False
                
            sample_script_path = os.path.join(self.scripts_dir, "sample_script.py")
            
            # Don't overwrite existing sample script
            if os.path.exists(sample_script_path):
                return True
                
            sample_content = '''# Sample script for CrewGUI
import time

print('Hello from sample_script.py!')
print('This script will run for a few seconds.')

for i in range(1, 4):
    print(f'Counting: {i}')
    time.sleep(1)

print('Sample script finished.')
'''
            
            with open(sample_script_path, "w") as f:
                f.write(sample_content)
                
            logging.info(f"Created sample script: {sample_script_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create sample script: {e}")
            return False