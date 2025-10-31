"""Duty calculation and processing logic."""

import pandas as pd
import numpy as np
import re
from typing import Dict

import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class DutyProcessor:
    """Processes duty data from Excel files and calculates duty rates."""

    @staticmethod
    def process_duty_data(df: pd.DataFrame) -> Dict[str, float]:
        """
        Process duty data and return a dictionary of max duty rates per goods code.

        Args:
            df: DataFrame with duty information

        Returns:
            Dictionary mapping 4-digit goods codes to their maximum duty rates
        """
        # Extract first 4 digits from Goods code
        df['Goods_Code_4'] = df['Goods code'].astype(str).str[:4]

        df = df[df['Origin'] == 'ERGA OMNES']

        # Create new column with parsed duty rate
        df['Duty_rate'] = df['Duty'].apply(DutyProcessor.parse_duty_rate)

        # Summary of parsing
        total_rows = len(df)
        parsed_count = df['Duty_rate'].notna().sum()
        unparsed_count = total_rows - parsed_count
        print(f"Duty parsing: {parsed_count}/{total_rows} parsed, {unparsed_count} unparsed (set as NaN).")

        # Pick the biggest (max) duty rate per 4-digit goods code
        max_duty = df.groupby('Goods_Code_4')['Duty_rate'].max()

        # Remove codes without a numeric duty rate (NaN values)
        max_duty = max_duty.dropna()

        # Convert to dictionary
        duty_dict = max_duty.to_dict()

        return duty_dict

    @staticmethod
    def parse_duty_rate(val):
        """
        Parse duty strings and return duty rate as float (e.g. '12.000 %' -> 0.12).
        Returns np.nan when no percentage can be found (e.g. 'NAR', 'Cond: ...').
        """
        if pd.isna(val):
            return np.nan
        s = str(val).strip()
        # Look for percentage like '12.000 %' or '12%' with optional spaces and commas
        m = re.search(r'([\d]+[.,]?\d*)\s*%', s)
        if m:
            num = m.group(1).replace(',', '.')
            try:
                return float(num) / 100.0
            except ValueError:
                return np.nan
        # Fallback: if string is purely numeric (no percent sign) take it as percent
        m2 = re.search(r'^([\d]+[.,]?\d*)$', s)
        if m2:
            num = m2.group(1).replace(',', '.')
            try:
                return float(num) / 100.0
            except ValueError:
                return np.nan
        # No quantitative value found
        return np.nan

