"""Shared services for VAT calculations and data storage."""

import pandas as pd
from typing import Any

import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class Services:
    """Shared service methods used across processors."""

    @staticmethod
    def store_lv_data(lv_consignments, vat_per_country, return_vat_per_country, DR_revenue_table) -> None:
        """Save low value consignment data to CSV files."""
        lv_consignments.to_csv("lv_consignments_data.csv", index=False)
        vat_per_country.to_csv("lv_vat_per_country_summary.csv", index=False)
        return_vat_per_country.to_csv("lv_returned_vat_per_country_summary.csv", index=False)
        DR_revenue_table.to_csv("lv_DR_revenue_summary.csv", index=False)

    @staticmethod
    def store_hv_data(hv_consignments, vat_per_country, vat_difference_table, return_vat_per_country,
                      combined_refunds, DR_revenue_table) -> None:
        """Save high value consignment data to CSV files."""
        hv_consignments.to_csv("hv_consignments_data.csv", index=False)
        vat_per_country.to_csv("hv_vat_per_country_summary.csv", index=False)
        vat_difference_table.to_csv("hv_vat_difference_summary.csv", index=False)
        return_vat_per_country.to_csv("hv_returned_vat_per_country_summary.csv", index=False)
        combined_refunds.to_csv("hv_duty_and_vat__returned_values_summary.csv", index=False)
        DR_revenue_table.to_csv("hv_DR_revenue_summary.csv", index=False)

    @staticmethod
    def summary_table(lv_list, hv_list):
        """Create and save summary tables combining low and high value data."""
        # Extract values from lists
        lv_dr_revenue = lv_list[0]
        lv_pc_return = lv_list[1]
        lv_total_vat_from_returns = lv_list[2]
        lv_total_import_vat = lv_list[3]

        hv_vat_return_from_nl = hv_list[0]
        hv_dr_revenue = hv_list[1]
        hv_vat_difference_txt = hv_list[2]
        hv_vat_to_pay_total = hv_list[3]

        # Calculate combined DR revenue
        total_dr_revenue = lv_dr_revenue + hv_dr_revenue

        # Create summary data
        summary_data = {
            'Category': ['Low Value', 'High Value', 'Combined'],
            'DR Revenue': [lv_dr_revenue, hv_dr_revenue, total_dr_revenue]
        }

        # Create DataFrame
        summary_df = pd.DataFrame(summary_data)

        # Add additional fields as separate rows for clarity
        additional_info = pd.DataFrame({
            'Metric': [
                'LV: PC Money to Return from Returns',
                'LV: Total VAT from Returns',
                'LV: Total import VAT Needs To Be Paid',
                'HV: VAT to Return from NL',
                'HV: VAT to Pay NL for distribution to other countries',
                'HV: VAT Difference Status'
            ],
            'Value': [
                f'€{lv_pc_return:.2f}',
                f'€{lv_total_vat_from_returns:.2f}',
                f'€{lv_total_import_vat:.2f}',
                f'€{hv_vat_return_from_nl:.2f}',
                f'€{hv_vat_to_pay_total:.2f}',
                hv_vat_difference_txt
            ]
        })

        # Save both tables to CSV
        summary_df.to_csv("summary_revenue_table.csv", index=False)
        additional_info.to_csv("summary_additional_info.csv", index=False)

    @staticmethod
    def calculate_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate total VAT to pay per country."""
        # Get unique MRN records (to avoid counting same consignment multiple times)
        unique_consignments = df.drop_duplicates(subset=['MRN'])

        # Calculate VAT amount for each consignment
        unique_consignments['VAT Amount'] = unique_consignments['Consignment Value'] * unique_consignments['VAT Rate']

        # Group by Country and VAT Rate
        summary = unique_consignments.groupby(['Consignee Country', 'VAT Rate']).agg({
            'Consignment Value': 'sum',
            'VAT Amount': 'sum'
        }).reset_index()

        # Rename columns for clarity
        summary.columns = ['Country', 'VAT Rate', 'Total Consignment Value', 'Total VAT to Pay']

        return summary

    @staticmethod
    def calculate_return_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT refunds for returned items per country."""
        # Filter rows where items were returned
        returned_df = df[df['Line Item Quantity Returned'] > 0].copy()

        # Calculate total returned value for each line item
        returned_df['Returned Item Value'] = (
            returned_df['Line Item Quantity Returned'] *
            returned_df['Line Item Unit Price']
        )

        # Calculate VAT refund for each returned item
        returned_df['VAT Refund'] = returned_df['Returned Item Value'] * returned_df['VAT Rate']

        # Group by Country and VAT Rate
        summary = returned_df.groupby(['Consignee Country', 'VAT Rate']).agg({
            'Returned Item Value': 'sum',
            'VAT Refund': 'sum'
        }).reset_index()

        # Rename columns for clarity
        summary.columns = ['Country', 'VAT Rate', 'Total Returned Value', 'Total VAT Refund']

        return summary

