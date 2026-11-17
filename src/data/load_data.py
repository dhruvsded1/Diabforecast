"""
Data Loading Utilities for DiabForecast.
Provides safe, modular readers for WHO and GBD datasets.
"""
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Optional, Union
import logging
import pandas as pd

from src.utils.config import (
    WHO_DATA_PATH,
    PROCESSED_DATA_PATH,
    GBD_DATA_DIR,
    PAPERS_DIR,
)

logger = logging.getLogger(__name__)


def load_raw_who(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load raw WHO diabetes CSV file.

    Parameters
    ----------
    file_path : str or Path, optional
        Path to data.csv. Defaults to configured WHO_DATA_PATH.

    Returns
    -------
    pd.DataFrame
        Raw dataframe.
    """
    path = Path(file_path) if file_path else WHO_DATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Raw WHO dataset not found at: {path}")

    logger.info("Loading raw WHO data from %s", path)
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    return df


def load_processed_who(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load preprocessed WHO diabetes 18+ both sexes dataset.

    Parameters
    ----------
    file_path : str or Path, optional
        Path to cleaned CSV. Defaults to configured PROCESSED_DATA_PATH.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe sorted by location and year.
    """
    path = Path(file_path) if file_path else PROCESSED_DATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Processed dataset not found at: {path}. Run preprocessing first.")

    logger.info("Loading processed WHO data from %s", path)
    df = pd.read_csv(path)
    return df


def load_gbd_workbook(
    filename: str,
    sheet_name: Union[str, int] = 0,
    gbd_dir: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """
    Load a GBD 2023 Excel workbook.

    Parameters
    ----------
    filename : str
        Workbook file name (e.g., 'S1_Global_Age_Standardised_Prevalence_Rates.XLSX').
    sheet_name : str or int, default 0
        Sheet name or 0-indexed integer.
    gbd_dir : str or Path, optional
        Directory containing GBD files.

    Returns
    -------
    pd.DataFrame
        Loaded dataframe.
    """
    base_dir = Path(gbd_dir) if gbd_dir else GBD_DATA_DIR
    target = base_dir / filename
    if not target.exists():
        raise FileNotFoundError(f"GBD workbook not found: {target}")

    logger.info("Loading GBD workbook %s (sheet=%s)", filename, sheet_name)
    df = pd.read_excel(target, sheet_name=sheet_name)
    return df


def list_available_gbd_files(gbd_dir: Optional[Union[str, Path]] = None) -> list[str]:
    """Return sorted list of available GBD workbook filenames."""
    base_dir = Path(gbd_dir) if gbd_dir else GBD_DATA_DIR
    if not base_dir.exists():
        return []
    return sorted([f.name for f in base_dir.glob("*.XLSX")])


def list_available_papers(papers_dir: Optional[Union[str, Path]] = None) -> list[str]:
    """Return sorted list of available research paper PDF filenames."""
    base_dir = Path(papers_dir) if papers_dir else PAPERS_DIR
    if not base_dir.exists():
        return []
    return sorted([f.name for f in base_dir.glob("*.pdf")])

