"""
db_operations.py
================

This module defines the `DatabaseHandler` class, which provides a unified interface
for connecting to and managing various types of databases (PostgreSQL, MySQL, SQLite,
MSSQL, Oracle, MongoDB, Redis, Elasticsearch).

It automates configuration parsing, DataFrame preprocessing, and safe
save/append operations using SQLAlchemy (for relational databases) or
connection URLs for NoSQL systems.

Key Features
-------------
- Supports multiple database backends:
  - Relational: PostgreSQL, MySQL, SQLite, MSSQL, Oracle
  - Non-relational: MongoDB, Redis, Elasticsearch
- Reads configuration dynamically from a JSON file.
- Automatically converts unsupported Python objects (dicts, lists) to strings before storage.
- Prevents duplicate record insertion when appending.
- Safely checks for table existence before appending data.
- Uses SQLAlchemy for robust database engine handling.

"""

import os
import json
import datetime
import pandas as pd
from sqlalchemy import create_engine, MetaData
from sqlalchemy.exc import SQLAlchemyError

class DatabaseHandler:
    """
    A class to handle database operations including fetching configurations, saving, and appending data to various database types.

    Attributes:
    config_file (str): Path to the database configuration file.
    db_config (dict): Database configuration dictionary parsed from the config file.
    db_url (str): Database connection URL.

    Methods:
    get_db_config(): Retrieves and parses the database configuration from the provided config file.
    preprocess_dataframe(df): Preprocesses the DataFrame by converting objects like dicts and lists to strings.
    save_or_append_to_db(df, table_name, append=False): Saves or appends the DataFrame to the specified database table.
    table_exists(engine, table_name): Checks if the specified table exists in the database.
    """

    def __init__(self, config_file=None):
        """
        Initializes the DatabaseHandler with a configuration file.

        Args:
        config_file (str): Path to the database configuration file.
        """
        self.config_file = config_file
        self.db_config = None
        self.db_url = None

    def get_db_config(self):
        """
        Retrieves the database configuration from the configuration file and constructs the database URL.

        Returns:
        dict: A dictionary containing the database type and connection URL if the configuration is valid.
        None: If the configuration file is not found or invalid.
        """
        if not self.config_file or not os.path.exists(self.config_file):
            return None

        with open(self.config_file, 'r') as file:
            config = json.load(file)

        database_type = config.get('database')
        if not database_type:
            return None
            
        db_config = None

        if database_type == 'postgresql':
            db_config = {
                "type": "postgresql",
                "db_url": f"postgresql://{config['postgresql']['username']}:{config['postgresql']['password']}@{config['postgresql']['host']}:{config['postgresql']['port']}/{config['postgresql']['database']}"
            }

        elif database_type == 'mysql':
            db_config = {
                "type": "mysql",
                "db_url": f"mysql://{config['mysql']['username']}:{config['mysql']['password']}@{config['mysql']['host']}:{config['mysql']['port']}/{config['mysql']['database']}"
            }

        elif database_type == 'sqlite':
            db_config = {
                "type": "sqlite",
                "db_url": f"sqlite:///{config['sqlite']['database']}"
            }

        elif database_type == 'mssql':
            db_config = {
                "type": "mssql",
                "db_url": f"mssql+pyodbc://{config['mssql']['username']}:{config['mssql']['password']}@{config['mssql']['host']}:{config['mssql']['port']}/{config['mssql']['database']}?driver={config['mssql']['driver']}"
            }

        elif database_type == 'oracle':
            db_config = {
                "type": "oracle",
                "db_url": f"oracle+cx_oracle://{config['oracle']['username']}:{config['oracle']['password']}@{config['oracle']['host']}:{config['oracle']['port']}/{config['oracle']['service_name']}"
            }

        elif database_type == 'mongodb':
            db_config = {
                "type": "mongodb",
                "db_url": f"mongodb://{config['mongodb']['username']}:{config['mongodb']['password']}@{config['mongodb']['host']}:{config['mongodb']['port']}/{config['mongodb']['database']}",
                "collection_name": config['mongodb'].get('collection_name', None)
            }

        elif database_type == 'redis':
            db_config = {
                "type": "redis",
                "db_url": f"redis://{config['redis'].get('password', '')}@{config['redis']['host']}:{config['redis']['port']}/"
            }

        elif database_type == 'elasticsearch':
            db_config = {
                "type": "elasticsearch",
                "db_url": f"http://{config['elasticsearch']['username']}:{config['elasticsearch']['password']}@{config['elasticsearch']['host']}:{config['elasticsearch']['port']}/"
            }

        return db_config

    def preprocess_dataframe(self, df):
        """
        Preprocesses the DataFrame by converting any objects such as dicts and lists to strings.

        Args:
        df (pandas.DataFrame): The DataFrame to be preprocessed.

        Returns:
        pandas.DataFrame: The preprocessed DataFrame.
        """
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        return df

    def save_or_append_to_db(self, df, table_name, append=False):
        """
        Saves or appends the DataFrame to the specified table in the database.

        Args:
        df (pandas.DataFrame): The DataFrame to be saved or appended.
        table_name (str): The name of the table in the database.
        append (bool): Whether to append data to the table if it exists (default is False).

        Returns:
        None
        """
        if not self.db_config:
            self.db_config = self.get_db_config()
            if self.db_config:
                self.db_url = self.db_config.get("db_url")
            else:
                return

        engine = create_engine(self.db_url)

        with engine.connect() as connection:
            if append:
                if not self.table_exists(engine, table_name):
                    print(f"Table '{table_name}' does not exist. Cannot append data.")
                    return

                existing_data = pd.read_sql_table(table_name, con=connection)
                df = self.preprocess_dataframe(df)
                df = df.drop_duplicates().copy()

                if not set(df.columns).issubset(existing_data.columns):
                    raise KeyError("One or more columns from the DataFrame are not present in the existing table.")

                df['unique_id'] = df.apply(lambda row: hash(tuple(row)), axis=1)
                existing_data['unique_id'] = existing_data.apply(lambda row: hash(tuple(row)), axis=1)

                new_data = df[~df['unique_id'].isin(existing_data['unique_id'])].copy()
                new_data.drop(columns='unique_id', inplace=True)

                if not new_data.empty:
                    new_data.to_sql(table_name, con=connection, if_exists='append', index=False)
                else:
                    pass

            else:
                df = self.preprocess_dataframe(df)
                try:
                    df.to_sql(table_name, con=connection, if_exists='replace', index=False)
                except SQLAlchemyError as e:
                    print(f"An error occurred: {e}")

    def table_exists(self, engine, table_name):
        """
        Checks if the specified table exists in the database.

        Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine connected to the database.
        table_name (str): The name of the table to check.

        Returns:
        bool: True if the table exists, False otherwise.
        """
        metadata = MetaData()
        metadata.reflect(bind=engine)
        return table_name in metadata.tables
