"""Shared services for VAT calculations and data storage."""

import pandas as pd
from pathlib import Path
import os

import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class Services:
    """Shared service methods used across processors."""

    @staticmethod
    def store_lv_data(lv_consignments, vat_per_country, return_vat_per_country, DR_revenue_table) -> None:
        """Save low value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # Save all dataframes to Excel format
        lv_consignments.to_excel(data_dir / "lv_consignments_data.xlsx", index=False, engine='openpyxl')
        vat_per_country.to_excel(data_dir / "lv_vat_per_country_summary.xlsx", index=False, engine='openpyxl')
        return_vat_per_country.to_excel(data_dir / "lv_returned_vat_per_country_summary.xlsx", index=False, engine='openpyxl')
        DR_revenue_table.to_excel(data_dir / "lv_DR_revenue_summary.xlsx", index=False, engine='openpyxl')

    @staticmethod
    def store_hv_data(hv_consignments, vat_per_country, vat_difference_table, return_vat_per_country,
                      combined_refunds, DR_revenue_table) -> None:
        """Save high value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # Save all dataframes to Excel format
        hv_consignments.to_excel(data_dir / "hv_consignments_data.xlsx", index=False, engine='openpyxl')
        vat_per_country.to_excel(data_dir / "hv_vat_per_country_summary.xlsx", index=False, engine='openpyxl')
        vat_difference_table.to_excel(data_dir / "hv_vat_difference_summary.xlsx", index=False, engine='openpyxl')
        return_vat_per_country.to_excel(data_dir / "hv_returned_vat_per_country_summary.xlsx", index=False, engine='openpyxl')
        combined_refunds.to_excel(data_dir / "hv_duty_and_vat_returned_values_summary.xlsx", index=False, engine='openpyxl')
        DR_revenue_table.to_excel(data_dir / "hv_DR_revenue_summary.xlsx", index=False, engine='openpyxl')

    @staticmethod
    def summary_table(lv_list, hv_list):

        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

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
        summary_df.to_excel(data_dir / "summary_revenue_table.xlsx", index=False, engine='openpyxl')

        additional_info.to_excel(data_dir / "summary_additional_info.xlsx", index=False, engine='openpyxl')

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

    @staticmethod
    def create_financial_summary(
        dutch_vat_return: pd.DataFrame,
        oss_detailed: pd.DataFrame,
        duty_return: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Create financial summary from VAT return forms.
        
        Args:
            dutch_vat_return: Dutch VAT Return form
            oss_detailed: OSS VAT Return detailed form
            duty_return: Duty Return Claim form
            
        Returns:
            DataFrame with financial summary
        """
        data_dir = Path("vat_returns")
        data_dir.mkdir(exist_ok=True)
        
        # 1. OSS VAT DUE (sum of Net VAT Due from OSS return)
        oss_vat_due = oss_detailed['Net VAT Due'].sum() if len(oss_detailed) > 0 else 0
        
        # 2. Net VAT from Dutch Return (row 3a - "Output VAT - Input VAT")
        # Find the row with '3a. Output VAT - Input VAT'
        dutch_net_row = dutch_vat_return[dutch_vat_return['Section'] == '3a. Output VAT - Input VAT']
        if len(dutch_net_row) > 0:
            dutch_net_str = dutch_net_row['Amount (€)'].values[0]
            # Remove commas and convert to float
            dutch_net_vat = float(dutch_net_str.replace(',', ''))
        else:
            dutch_net_vat = 0
        
        # 3. Duty Revenue (80% for most countries, 70% for Ireland)
        if len(duty_return) > 0:
            duty_return_copy = duty_return.copy()
            duty_return_copy['Duty Revenue'] = duty_return_copy.apply(
                lambda row: row['Total Duty Returned'] * 0.70 if row['Country'] == 'IE'
                else row['Total Duty Returned'] * 0.80,
                axis=1
            )
            duty_revenue_total = duty_return_copy['Duty Revenue'].sum()
        else:
            duty_revenue_total = 0
        
        # Create summary table
        summary_data = {
            'Financial Item': [
                'VAT to Pay to OSS (HV parcels to other EU countries)',
                'Net VAT from Dutch Return (IOSS + NL operations)',
                'Duty Returned To Pro Carrier (80% general, 70% IE)',
                '',
                'TOTAL AMOUNTS'
            ],
            'Amount (€)': [
                f'{oss_vat_due:,.2f}',
                f'{dutch_net_vat:,.2f}',
                f'{duty_revenue_total:,.2f}',
                '',
                ''
            ],
            'Description': [
                'Payment due for OSS quarterly return (HV parcels shipped to other EU countries)',
                'Amount to claim from broker (positive) or pay (negative) - includes IOSS VAT, NL returns, and broker import VAT',
                'Revenue from duty refunds claimed from customs (company share)',
                '',
                'Summary of key financial movements'
            ]
        }
        
        financial_summary = pd.DataFrame(summary_data)
        
        # Save to Excel
        financial_summary.to_excel(
            data_dir / "financial_summary_from_returns.xlsx",
            index=False,
            engine='openpyxl'
        )
        
        print(f"\n💰 Financial Summary:")
        print(f"   📊 OSS VAT Due: €{oss_vat_due:,.2f}")
        print(f"   📊 Dutch Net VAT: €{dutch_net_vat:,.2f}")
        print(f"   📊 Duty Revenue: €{duty_revenue_total:,.2f}")
        
        return financial_summary

