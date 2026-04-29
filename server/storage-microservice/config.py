#!/usr/bin/python
from configparser import ConfigParser
import os


def config(filename='database.ini', section='postgresql'):
    # Use absolute path relative to this file's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found: {filepath}")
    
    # create a parser
    parser = ConfigParser()
    # read config file
    files_read = parser.read(filepath)
    
    if not files_read:
        raise Exception(f'Failed to read config file: {filepath}')

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filepath}')

    return db