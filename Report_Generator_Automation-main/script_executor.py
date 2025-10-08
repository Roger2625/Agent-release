#!/usr/bin/env python3
"""
Safe Script Executor - Provides sandboxed execution of Python scripts
"""

import os
import sys
import subprocess
import tempfile
import shutil
import signal
import time
import threading
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import ast
import importlib.util
import builtins

@dataclass
class ScriptExecutionResult:
    """Result of script execution"""
    success: bool
    stdout: str
    stderr: str
    execution_time: float
    exit_code: int
    error_message: Optional[str] = None

class ScriptSecurityValidator:
    """Validates scripts for security concerns before execution"""
    
    FORBIDDEN_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'tempfile', 'signal',
        'threading', 'multiprocessing', 'socket', 'urllib', 'requests',
        'ftplib', 'smtplib', 'telnetlib', 'paramiko', 'pexpect',
        'ctypes', 'mmap', 'fcntl', 'pwd', 'grp', 'crypt', 'hashlib',
        'hmac', 'ssl', 'crypto', 'Crypto', 'pycrypto', 'bcrypt',
        'passlib', 'cryptography', 'nacl', 'libnacl'
    }
    
    FORBIDDEN_FUNCTIONS = {
        'eval', 'exec', 'compile', 'input', 'raw_input',
        'open', 'file', 'print', 'help', 'dir', 'vars',
        'locals', 'globals', 'getattr', 'setattr', 'delattr',
        'hasattr', 'isinstance', 'issubclass', 'super',
        'property', 'staticmethod', 'classmethod', 'abstractmethod'
    }
    
    FORBIDDEN_ATTRIBUTES = {
        '__import__', '__builtins__', '__dict__', '__class__',
        '__bases__', '__subclasses__', '__mro__', '__name__',
        '__module__', '__file__', '__path__', '__package__'
    }
    
    @classmethod
    def validate_script(cls, script_content: str) -> Tuple[bool, List[str]]:
        """Validate script content for security concerns"""
        errors = []
        
        try:
            # Parse the script
            tree = ast.parse(script_content)
            
            # Check for forbidden imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in cls.FORBIDDEN_MODULES:
                            errors.append(f"Forbidden import: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in cls.FORBIDDEN_MODULES:
                        errors.append(f"Forbidden import from: {node.module}")
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in cls.FORBIDDEN_FUNCTIONS:
                            errors.append(f"Forbidden function call: {node.func.id}")
                    
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in cls.FORBIDDEN_FUNCTIONS:
                            errors.append(f"Forbidden method call: {node.func.attr}")
                
                elif isinstance(node, ast.Attribute):
                    if node.attr in cls.FORBIDDEN_ATTRIBUTES:
                        errors.append(f"Forbidden attribute access: {node.attr}")
            
            # Check for exec/eval usage
            if 'exec(' in script_content or 'eval(' in script_content:
                errors.append("Forbidden: exec() or eval() usage")
            
            # Check for file operations
            if 'open(' in script_content:
                errors.append("Forbidden: file operations not allowed")
            
            # Check for subprocess usage
            if 'subprocess' in script_content or 'os.system' in script_content:
                errors.append("Forbidden: subprocess or system calls not allowed")
            
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def create_safe_environment(cls) -> Dict:
        """Create a safe execution environment"""
        # Create a restricted builtins dict
        safe_builtins = {}
        allowed_builtins = {
            'abs', 'all', 'any', 'bin', 'bool', 'chr', 'complex',
            'dict', 'divmod', 'enumerate', 'filter', 'float', 'format',
            'frozenset', 'hash', 'hex', 'int', 'isinstance', 'issubclass',
            'iter', 'len', 'list', 'map', 'max', 'min', 'next', 'oct',
            'ord', 'pow', 'print', 'range', 'repr', 'reversed', 'round',
            'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type',
            'zip', 'True', 'False', 'None'
        }
        
        for name in allowed_builtins:
            if hasattr(builtins, name):
                safe_builtins[name] = getattr(builtins, name)
        
        return {
            '__builtins__': safe_builtins,
            '__name__': '__main__',
            '__file__': None,
            '__doc__': None,
            '__package__': None
        }

class SafeScriptExecutor:
    """Executes Python scripts in a safe, sandboxed environment"""
    
    def __init__(self, timeout: int = 30, max_output_size: int = 1024 * 1024):
        """
        Initialize the script executor
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_size: Maximum output size in bytes
        """
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.validator = ScriptSecurityValidator()
    
    def execute_script(self, script_path: str) -> ScriptExecutionResult:
        """
        Execute a Python script safely
        
        Args:
            script_path: Path to the Python script file
            
        Returns:
            ScriptExecutionResult with execution details
        """
        start_time = time.time()
        
        try:
            # Read and validate script content
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Validate script security
            is_valid, errors = self.validator.validate_script(script_content)
            if not is_valid:
                return ScriptExecutionResult(
                    success=False,
                    stdout="",
                    stderr="\n".join(errors),
                    execution_time=time.time() - start_time,
                    exit_code=1,
                    error_message="Script validation failed"
                )
            
            # Create temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy script to temp directory
                temp_script_path = os.path.join(temp_dir, "script.py")
                with open(temp_script_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                
                # Execute in isolated environment
                result = self._execute_in_isolation(temp_script_path)
                result.execution_time = time.time() - start_time
                return result
                
        except Exception as e:
            return ScriptExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                exit_code=1,
                error_message=f"Execution error: {str(e)}"
            )
    
    def _execute_in_isolation(self, script_path: str) -> ScriptExecutionResult:
        """Execute script in isolated environment"""
        try:
            # Create safe environment
            safe_globals = self.validator.create_safe_environment()
            
            # Capture stdout/stderr
            import io
            import sys
            
            # Redirect stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            try:
                # Execute script with timeout
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_code = compile(f.read(), script_path, 'exec')
                
                # Execute in thread with timeout
                result_queue = []
                exception_queue = []
                
                def execute_script():
                    try:
                        exec(script_code, safe_globals)
                        result_queue.append(True)
                    except Exception as e:
                        exception_queue.append(e)
                
                thread = threading.Thread(target=execute_script)
                thread.daemon = True
                thread.start()
                thread.join(timeout=self.timeout)
                
                if thread.is_alive():
                    # Script timed out
                    return ScriptExecutionResult(
                        success=False,
                        stdout=stdout_capture.getvalue(),
                        stderr=stderr_capture.getvalue(),
                        execution_time=self.timeout,
                        exit_code=1,
                        error_message="Script execution timed out"
                    )
                
                if exception_queue:
                    # Script raised an exception
                    exc = exception_queue[0]
                    return ScriptExecutionResult(
                        success=False,
                        stdout=stdout_capture.getvalue(),
                        stderr=stderr_capture.getvalue() + f"\nException: {str(exc)}",
                        execution_time=0,
                        exit_code=1,
                        error_message=f"Script exception: {str(exc)}"
                    )
                
                # Success
                return ScriptExecutionResult(
                    success=True,
                    stdout=stdout_capture.getvalue(),
                    stderr=stderr_capture.getvalue(),
                    execution_time=0,
                    exit_code=0
                )
                
            finally:
                # Restore stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
        except Exception as e:
            return ScriptExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                execution_time=0,
                exit_code=1,
                error_message=f"Isolation error: {str(e)}"
            )
    
    def execute_scripts_sequentially(self, script_paths: List[str]) -> List[ScriptExecutionResult]:
        """
        Execute multiple scripts sequentially
        
        Args:
            script_paths: List of script file paths
            
        Returns:
            List of ScriptExecutionResult objects
        """
        results = []
        
        for i, script_path in enumerate(script_paths):
            print(f"Executing script {i+1}/{len(script_paths)}: {os.path.basename(script_path)}")
            
            result = self.execute_script(script_path)
            results.append(result)
            
            if not result.success:
                print(f"Script {i+1} failed: {result.error_message}")
                # Continue with next script even if one fails
                continue
            
            print(f"Script {i+1} completed successfully")
        
        return results

class ScriptManager:
    """Manages script uploads, storage, and execution"""
    
    def __init__(self, base_directory: str = None):
        """
        Initialize script manager
        
        Args:
            base_directory: Base directory for script storage
        """
        if base_directory is None:
            base_directory = os.path.join(os.getcwd(), "uploaded_scripts")
        
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(exist_ok=True)
        
        self.executor = SafeScriptExecutor()
        self.uploaded_scripts = {}  # {script_id: script_info}
    
    def upload_script(self, file_path: str, section_name: str = None, step_name: str = None) -> str:
        """
        Upload and store a Python script
        
        Args:
            file_path: Path to the Python script file
            section_name: Optional section name for organization
            step_name: Optional step name for organization
            
        Returns:
            Script ID for reference
        """
        import uuid
        
        # Generate unique script ID
        script_id = str(uuid.uuid4())
        
        # Create directory structure
        script_dir = self.base_directory
        if section_name:
            script_dir = script_dir / section_name
        if step_name:
            script_dir = script_dir / step_name
        
        script_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy script to storage
        script_filename = f"{script_id}_{os.path.basename(file_path)}"
        script_path = script_dir / script_filename
        
        shutil.copy2(file_path, script_path)
        
        # Store script info
        self.uploaded_scripts[script_id] = {
            'id': script_id,
            'original_path': file_path,
            'stored_path': str(script_path),
            'filename': os.path.basename(file_path),
            'section_name': section_name,
            'step_name': step_name,
            'upload_time': time.time()
        }
        
        return script_id
    
    def get_script_info(self, script_id: str) -> Optional[Dict]:
        """Get information about an uploaded script"""
        return self.uploaded_scripts.get(script_id)
    
    def execute_script(self, script_id: str) -> ScriptExecutionResult:
        """Execute a specific script by ID"""
        script_info = self.get_script_info(script_id)
        if not script_info:
            return ScriptExecutionResult(
                success=False,
                stdout="",
                stderr="Script not found",
                execution_time=0,
                exit_code=1,
                error_message="Script ID not found"
            )
        
        return self.executor.execute_script(script_info['stored_path'])
    
    def execute_section_scripts(self, section_name: str) -> List[ScriptExecutionResult]:
        """Execute all scripts for a specific section"""
        section_scripts = [
            script_info['stored_path'] 
            for script_info in self.uploaded_scripts.values()
            if script_info['section_name'] == section_name
        ]
        
        # Sort by upload time to maintain order
        section_scripts.sort(key=lambda x: self.uploaded_scripts.get(
            os.path.basename(x).split('_')[0], {}).get('upload_time', 0)
        )
        
        return self.executor.execute_scripts_sequentially(section_scripts)
    
    def remove_script(self, script_id: str) -> bool:
        """Remove a script from storage"""
        script_info = self.get_script_info(script_id)
        if not script_info:
            return False
        
        try:
            os.remove(script_info['stored_path'])
            del self.uploaded_scripts[script_id]
            return True
        except Exception:
            return False
    
    def get_all_scripts(self) -> List[Dict]:
        """Get all uploaded scripts"""
        return list(self.uploaded_scripts.values())
    
    def get_scripts_by_section(self, section_name: str) -> List[Dict]:
        """Get all scripts for a specific section"""
        return [
            script_info for script_info in self.uploaded_scripts.values()
            if script_info['section_name'] == section_name
        ] 