"""Low value consignment processor (<=150€)."""

import pandas as pd
from typing import Any
from ProCarrier.ProCarrierService.code.config import Config
from services import Services

import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class LowValueProcessor:
    """Processes low value consignments (<=150€)."""

    @staticmethod
    def process_low_value_data(df: pd.DataFrame) -> list[Any]:
        """
        Process low value consignment data.

        Returns:
            List containing [DR_revenue, PC_return, total_vat_from_returns, total_import_vat]
        """
        df = LowValueProcessor.clean_columns(df)

        vat_per_country = LowValueProcessor.calculate_vat_per_country(df)
        return_vat_per_country = LowValueProcessor.calculate_return_vat_per_country(df)

        combined_vat_per_country = LowValueProcessor.create_combined_vat_per_country(vat_per_country, return_vat_per_country)

        # Save reports to CSV files
        Services.store_lv_data(combined_vat_per_country)

        return [vat_per_country, return_vat_per_country]

    @staticmethod
    def create_combined_vat_per_country(vat_per_country: pd.DataFrame, return_vat_per_country: pd.DataFrame) -> pd.DataFrame:
        """Create combined VAT per country dataframe."""
        combined_vat_per_country = pd.merge(
            vat_per_country,
            return_vat_per_country[['Country', 'Total VAT Refund']],
            on='Country',
            how='outer'
        )

        combined_vat_per_country.fillna(0, inplace=True)

        combined_vat_per_country['NET VAT'] = combined_vat_per_country['Total VAT to Pay'] - combined_vat_per_country['Total VAT Refund']

        return combined_vat_per_country

    @staticmethod
    def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Keep only relevant columns for low value consignments."""
        return df[Config.low_value_columns]

    @staticmethod
    def calculate_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT per country."""
        return Services.calculate_vat_per_country(df)

    @staticmethod
    def calculate_return_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT refunds for returned items."""
        return Services.calculate_return_vat_per_country(df)


