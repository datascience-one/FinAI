"""
nse_data_fetcher package
========================

This package provides tools to automate the process of fetching, storing, and managing
corporate announcement data from the National Stock Exchange (NSE).

Modules
--------
1. db_operations
    Contains the `DatabaseHandler` class for managing database connections,
    creating tables, and performing CRUD operations related to NSE data.

2. fetcher
    Provides the `Corperate_Announcements` class (note: consider renaming to `CorporateAnnouncements`)
    which handles fetching and parsing corporate announcement data from the NSE website or API.

3. save_attachment
    Includes the `download_file` function to download and save attachments (e.g., PDFs, CSVs)
    related to NSE announcements.
"""

from .db_operations import DatabaseHandler
from .fetcher import Corperate_Announcements

__all__ = ["Corperate_Announcements"]
from .save_attachment import download_file
