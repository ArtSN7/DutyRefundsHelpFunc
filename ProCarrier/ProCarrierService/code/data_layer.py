import pandas as pd
from typing import Tuple
from ProCarrier.ProCarrierService.code.config import Config
import warnings

warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class DataLayer:
    """Handles data loading, cleaning and preparation."""

    @staticmethod
    def load_excel(excel_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        df = pd.read_excel(excel_path, sheet_name='Sheet1')

        # If multiple sheets were requested/returned, pick the first sheet's DataFrame
        if isinstance(df, dict):
            df = next(iter(df.values()))

        df = DataLayer.clean_data(df)
        df = DataLayer.add_calculated_fields(df)
        low_value_df, high_value_df = DataLayer.separate_data(df, Config.CONSIGNMENT_THRESHOLD)
        return low_value_df, high_value_df

    @staticmethod
    def load_data(csv_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        df = pd.read_csv(csv_path)
        df = DataLayer.clean_data(df)
        df = DataLayer.add_calculated_fields(df)
        low_value_df, high_value_df = DataLayer.separate_data(df, Config.CONSIGNMENT_THRESHOLD)
        return low_value_df, high_value_df

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        # Exclude IC and CH countries
        df = df[~df['Consignee Country'].isin(['IC', 'CH'])]

        # Standardize missing values
        df['MRN'] = df['MRN'].replace(['#N/A', 'N/A', 'NA', 'na', ''], pd.NA)

        # Copy Parcel ID where MRN is missing
        df.loc[df['MRN'].isna(), 'MRN'] = df.loc[df['MRN'].isna(), 'Parcel ID']

        return df

    @staticmethod
    def add_calculated_fields(df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated fields: Line Item Total Value, Consignment Value, VAT Rate."""
        # Calculate line item total value (quantity × unit price)
        df['Line Item Total Value'] = df['Line Item Quantity Imported'] * df['Line Item Unit Price']

        # Consignment Value: sum of all line item total values per MRN
        df['Consignment Value'] = df.groupby('MRN')['Line Item Total Value'].transform('sum')

        # Map VAT rates by country
        df['VAT Rate'] = df['Consignee Country'].map(Config.VAT_RATES)

        if df['VAT Rate'].isna().any():
            missing_countries = df[df['VAT Rate'].isna()]['Consignee Country'].unique()
            print(f"⚠️ WARNING: Missing VAT rates for countries: {missing_countries}")

        return df

    @staticmethod
    def separate_data(df: pd.DataFrame, threshold: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Separate data into low value and high value based on consignment value threshold."""
        high_value_df = df[df['Consignment Value'] > threshold].copy()
        low_value_df = df[df['Consignment Value'] <= threshold].copy()
        return low_value_df, high_value_df
