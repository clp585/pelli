"""
Generate metadata CSV from a folder containing multiple PDF files.

This script scans a folder for all .pdf files and creates a metadata CSV
where each PDF file becomes one row in the DataFrame.

Usage:
    python generate_metadata_from_folder.py --folder_path PATH --output_csv PATH --project-id PROJECT_ID
"""

import argparse
import os
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def safe_path_join(*parts):
    """Normalize path joining to handle cross-platform issues."""
    return os.path.normpath(os.path.join(*parts))


def scan_folder_for_pdfs(folder_path: str) -> list:
    """
    Scan a folder for all PDF files.
    
    Args:
        folder_path: Path to the folder to scan
        
    Returns:
        List of full paths to PDF files found
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    if not os.path.isdir(folder_path):
        raise ValueError(f"Path is not a directory: {folder_path}")
    
    pdf_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                pdf_files.append(full_path)
    
    return sorted(pdf_files)


def generate_metadata_from_folder(folder_path: str, output_csv: str, project_id: str):
    """
    Generate metadata CSV from all PDF files in a folder.
    
    Args:
        folder_path: Path to folder containing PDF files
        output_csv: Path where the output CSV will be saved
        project_id: Project identifier to include in metadata
    """
    logger.info(f"Scanning folder for PDF files: {folder_path}")
    
    # Scan for PDF files
    pdf_files = scan_folder_for_pdfs(folder_path)
    
    if not pdf_files:
        logger.warning(f"No PDF files found in: {folder_path}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF file(s)")
    
    # Prepare data for DataFrame
    rows = []
    
    for pdf_file in pdf_files:
        # Get filename (with extension) for file_path
        filename = os.path.basename(pdf_file)
        # Normalize path separators
        filename = os.path.normpath(filename)
        
        # Get filename without extension for sheet_id
        sheet_id = os.path.splitext(filename)[0]
        
        # Create row data
        row = {
            'sheet_id': sheet_id,
            'file_path': filename,  # Just the filename (CSV lives in same folder)
            'page_number': 0,  # Each file is treated as page 0
            'project_id': project_id,
            'discipline': '',  # Empty for now
            'sheet_type': '',  # Empty for now
            'sheet_title': sheet_id,  # Use filename as title
            'version': 'v1',
            'keywords': ''  # Empty for now
        }
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved metadata CSV to: {output_csv}")
    logger.info(f"Total rows: {len(df)}")
    
    # Print preview
    logger.info("\nFirst 5 rows preview:")
    for idx, row in df.head().iterrows():
        logger.info(f"  {row['sheet_id']} -> {row['file_path']} (page {row['page_number']})")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate metadata CSV from a folder containing PDF files"
    )
    parser.add_argument(
        '--folder_path',
        required=True,
        help='Path to folder containing PDF files'
    )
    parser.add_argument(
        '--output_csv',
        required=True,
        help='Path where the output CSV will be saved'
    )
    parser.add_argument(
        '--project-id',
        required=True,
        dest='project_id',
        help='Project identifier'
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        generate_metadata_from_folder(
            folder_path=args.folder_path,
            output_csv=args.output_csv,
            project_id=args.project_id
        )
        logger.info("\n[OK] Metadata generation complete!")
    except Exception as e:
        logger.error(f"\n[ERROR] Failed to generate metadata: {e}")
        raise


if __name__ == "__main__":
    main()

