# -*- coding: utf-8 -*-
import logging
import pandas as pd
import json

from typing import List


def get_logger() -> logging.Logger:
    """
    Get logger instance.
    """
    level = logging.INFO
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    logger.propagate = False
    logger.handlers = []
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def safe_json_loads(s):
    """
    Safely loads a JSON string, replacing single quotes with double quotes, and returns a JSON string.
    """
    try:
        # Convert to valid JSON format and parse
        parsed = json.loads(s.replace("'", '"'))
        return json.dumps(parsed)  # Convert back to JSON string
    except json.JSONDecodeError:
        # Handle or log the error if needed
        return json.dumps([])  # Return an empty JSON array as a string


def expand_json(row, idx):
    """
    Normalize and Expand the JSON-like strings or already parsed JSON.
    """
    if isinstance(row, str):
        parsed_row = json.loads(row)
    elif isinstance(row, list):
        parsed_row = row
    else:
        parsed_row = []

    expanded = pd.json_normalize(parsed_row)
    expanded["original_index"] = idx
    return expanded


class ProjectAllocator:
    def __init__(self, total_amount, min_amount, quorum) -> None:
        """
        Initialize the ProjectAllocator.
        """
        self.total_amount = total_amount
        self.min_amount = min_amount
        self.quorum = quorum

    def calculate_initial_allocation(self, df) -> pd.DataFrame:
        """
        Calculate the raw allocation amount of each project.
        """
        # get the number of votes and median amount for each project
        project_allocation = df.groupby("project_id").agg(
            votes_count=("voter_address", "count"), median_amount=("amount", "median")
        )

        # filter out projects that do not meet the quorum
        return project_allocation[
            project_allocation["votes_count"] >= self.quorum
        ].sort_values("median_amount", ascending=False)

    # scaling the total to RPGF OP total by project and filter out those with < min OP requirement
    def scale_allocations(self, df) -> pd.DataFrame:
        """
        Scale the allocations to the total amount of OP and filter out those with less than 1500 OP.
        """
        scale_factor = self.total_amount / df["median_amount"].sum()
        df["scaled_amount"] = df["median_amount"] * scale_factor

        df = df[df["scaled_amount"] > self.min_amount]

        return df
