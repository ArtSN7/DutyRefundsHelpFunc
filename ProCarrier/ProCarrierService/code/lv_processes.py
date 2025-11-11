from config import Config
import pandas as pd
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)


class LowValueProcessor:
    """Processes low value consignments (<=150€)."""

    @staticmethod
    def process_low_value_data(df: pd.DataFrame) -> pd.DataFrame:
        df = LowValueProcessor.clean_columns(df)

        vat_per_country = LowValueProcessor.calculate_vat_per_country(df)
        return_vat_per_country = LowValueProcessor.calculate_return_vat_per_country(df)

        combined_vat_per_country = LowValueProcessor.create_combined_vat_per_country(
            vat_per_country, return_vat_per_country
        )

        # Save reports to CSV files
        LowValueProcessor.store_lv_data(combined_vat_per_country)

        dr_lv_fee = LowValueProcessor.calculate_fee_lv(combined_vat_per_country)
        import_ioss = combined_vat_per_country["Total VAT to Pay"].sum()
        return_ioss = combined_vat_per_country["Total VAT Refund"].sum()

        return dr_lv_fee, import_ioss, return_ioss

    @staticmethod
    def calculate_fee_lv(combined_vat_per_country: pd.DataFrame) -> pd.DataFrame:
        combined_vat_per_country["Fee Rate"] = combined_vat_per_country["Country"].map(
            Config.COMMISSION_RATES
        )

        combined_vat_per_country["Fee"] = (
                combined_vat_per_country["Fee Rate"]
                * combined_vat_per_country["Total VAT Refund"]
        )

        # print(combined_vat_per_country[["Country", "Total VAT Refund", "Fee Rate", "Fee"]])

        return combined_vat_per_country["Fee"].sum()

    @staticmethod
    def create_combined_vat_per_country(
            vat_per_country: pd.DataFrame, return_vat_per_country: pd.DataFrame
    ) -> pd.DataFrame:
        combined_vat_per_country = pd.merge(
            vat_per_country,
            return_vat_per_country[
                ["Country", "Total Returned Value", "Total VAT Refund"]
            ],
            on="Country",
            how="outer",
        )

        combined_vat_per_country.fillna(0, inplace=True)

        combined_vat_per_country["NET VAT"] = (
                combined_vat_per_country["Total VAT to Pay"]
                - combined_vat_per_country["Total VAT Refund"]
        )

        return combined_vat_per_country[
            ["Country", "VAT Rate", "Total VAT to Pay", "Total VAT Refund", "NET VAT"]
        ]

    @staticmethod
    def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Keep only relevant columns for low value consignments."""
        return df[Config.low_value_columns]

    @staticmethod
    def calculate_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate total VAT to pay per country."""
        # Get unique MRN records (to avoid counting same consignment multiple times)
        unique_consignments = df.drop_duplicates(subset=["MRN"])

        # Calculate VAT amount for each consignment
        unique_consignments["VAT Amount"] = (
                unique_consignments["Consignment Value"] * unique_consignments["VAT Rate"]
        )

        # Group by Country and VAT Rate
        summary = (
            unique_consignments.groupby(["Consignee Country", "VAT Rate"])
            .agg({"Consignment Value": "sum", "VAT Amount": "sum"})
            .reset_index()
        )

        # Rename columns for clarity
        summary.columns = [
            "Country",
            "VAT Rate",
            "Total Consignment Value",
            "Total VAT to Pay",
        ]

        return summary

    @staticmethod
    def calculate_return_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT refunds for returned items per country."""
        # Filter rows where items were returned
        returned_df = df[df["Line Item Quantity Returned"] > 0].copy()

        # Calculate total returned value for each line item
        returned_df["Returned Item Value"] = (
                returned_df["Line Item Quantity Returned"]
                * returned_df["Line Item Unit Price"]
        )

        # Calculate VAT refund for each returned item
        returned_df["VAT Refund"] = (
                returned_df["Returned Item Value"] * returned_df["VAT Rate"]
        )

        # Group by Country and VAT Rate
        summary = (
            returned_df.groupby(["Consignee Country", "VAT Rate"])
            .agg({"Returned Item Value": "sum", "VAT Refund": "sum"})
            .reset_index()
        )

        # Rename columns for clarity
        summary.columns = [
            "Country",
            "VAT Rate",
            "Total Returned Value",
            "Total VAT Refund",
        ]

        return summary

    # cохраняем дату о стране и уплаченном/возвращенном VAT
    @staticmethod
    def store_lv_data(lv_vat_per_country) -> None:
        """Save low value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)

        # Save all dataframes to Excel format
        lv_vat_per_country.to_excel(
            data_dir / "IOSS_SUM.xlsx", index=False, engine="openpyxl"
        )
