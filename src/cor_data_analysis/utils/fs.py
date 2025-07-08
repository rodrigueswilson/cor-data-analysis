"""File system utilities for COR Data Analysis.

This module provides helper functions for working with files and directories,
including safe path operations, file type detection, and batch processing.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Set, Union

from cor_data_analysis.utils.logging import get_logger

logger = get_logger(__name__)


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    
    Raises:
        OSError: If directory cannot be created
    """
    path_obj = Path(path)
    if not path_obj.exists():
        logger.info(f"Creating directory: {path_obj}")
        path_obj.mkdir(parents=True, exist_ok=True)
    elif not path_obj.is_dir():
        raise OSError(f"Path exists but is not a directory: {path_obj}")
    
    return path_obj


def safe_filename(filename: str) -> str:
    """Convert a string to a safe filename by removing invalid characters.
    
    Args:
        filename: Original filename string
        
    Returns:
        Safe filename string
    """
    invalid_chars = '<>:"/\\|?*'
    safe_name = ""
    for c in filename:
        if c in invalid_chars:
            safe_name += "_"
        else:
            safe_name += c
    return safe_name


def list_files(
    directory: Union[str, Path],
    extensions: Optional[Set[str]] = None,
    recursive: bool = False,
    include_dirs: bool = False,
) -> List[Path]:
    """List files in a directory, optionally filtering by extension.
    
    Args:
        directory: Directory to search
        extensions: Set of file extensions to include (lowercase, without dot)
        recursive: Whether to search subdirectories
        include_dirs: Whether to include directories in results
        
    Returns:
        List of Path objects for matching files
        
    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")
    
    # Convert extensions to lowercase
    if extensions:
        extensions = {ext.lower().lstrip('.') for ext in extensions}
    
    result = []
    
    if recursive:
        for root, dirs, files in os.walk(directory_path):
            root_path = Path(root)
            
            if include_dirs:
                result.extend([root_path / d for d in dirs])
                
            for file in files:
                file_path = root_path / file
                if not extensions or file_path.suffix.lower().lstrip('.') in extensions:
                    result.append(file_path)
    else:
        for item in directory_path.iterdir():
            if item.is_dir() and include_dirs:
                result.append(item)
            elif item.is_file():
                if not extensions or item.suffix.lower().lstrip('.') in extensions:
                    result.append(item)
    
    return result


def safe_delete(path: Union[str, Path]) -> bool:
    """Safely delete a file or directory, logging the operation.
    
    Args:
        path: Path to delete
        
    Returns:
        True if deletion succeeded, False otherwise
    """
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            logger.warning(f"Cannot delete non-existent path: {path_obj}")
            return False
            
        if path_obj.is_dir():
            logger.info(f"Deleting directory: {path_obj}")
            shutil.rmtree(path_obj)
        else:
            logger.info(f"Deleting file: {path_obj}")
            path_obj.unlink()
            
        return True
    except Exception as e:
        logger.error(f"Error deleting {path}: {str(e)}")
        return False


def safe_copy(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> bool:
    """Safely copy a file or directory, logging the operation.
    
    Args:
        src: Source path
        dst: Destination path
        overwrite: Whether to overwrite destination if it exists
        
    Returns:
        True if copy succeeded, False otherwise
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            logger.error(f"Source path does not exist: {src_path}")
            return False
            
        if dst_path.exists() and not overwrite:
            logger.warning(f"Destination path exists and overwrite=False: {dst_path}")
            return False
            
        if src_path.is_dir():
            if dst_path.exists() and overwrite:
                shutil.rmtree(dst_path)
            logger.info(f"Copying directory from {src_path} to {dst_path}")
            shutil.copytree(src_path, dst_path)
        else:
            logger.info(f"Copying file from {src_path} to {dst_path}")
            # Ensure parent directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            
        return True
    except Exception as e:
        logger.error(f"Error copying from {src} to {dst}: {str(e)}")
        return False


def batch_process_files(
    directory: Union[str, Path],
    process_func: Callable[[Path], None],
    extensions: Optional[Set[str]] = None,
    recursive: bool = False,
) -> int:
    """Process files in a directory using the provided function.
    
    Args:
        directory: Directory to search for files
        process_func: Function to call on each file
        extensions: Set of file extensions to include (lowercase, without dot)
        recursive: Whether to search subdirectories
        
    Returns:
        Number of files processed
        
    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    files = list_files(directory, extensions, recursive)
    processed_count = 0
    
    for file_path in files:
        try:
            logger.debug(f"Processing file: {file_path}")
            process_func(file_path)
            processed_count += 1
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    logger.info(f"Processed {processed_count} of {len(files)} files from {directory}")
    return processed_count


def create_temp_directory() -> Path:
    """Create a temporary directory that will be automatically cleaned up.
    
    Returns:
        Path object for the temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix="cor_data_")
    logger.debug(f"Created temporary directory: {temp_dir}")
    return Path(temp_dir)


def file_size_format(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string with appropriate units
    """
    if size_bytes == 0:
        return "0B"
        
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    unit_index = 0
    power = 1024
    
    while size_bytes >= power and unit_index < len(units) - 1:
        size_bytes /= power
        unit_index += 1
        
    return f"{size_bytes:.2f} {units[unit_index]}"
