"""Shared services for VAT calculations and data storage."""

import pandas as pd
from pathlib import Path
import os
from config import Config

import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class Services:
    """Shared service methods used across processors."""

    @staticmethod
    def store_lv_data(lv_consignments, vat_per_country, return_vat_per_country, DR_revenue_table) -> None:
        """Save low value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path(Config.DATA_DIR)
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
        data_dir = Path(Config.DATA_DIR)
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
        """Create and save summary tables combining low and high value data."""
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)

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
        data_dir = Path(Config.VAT_RETURNS_DIR)
        data_dir.mkdir(exist_ok=True)
        
        # 1. OSS VAT DUE (sum of Net VAT Due from OSS return)
        oss_vat_due = oss_detailed['Net VAT Due'].sum() if len(oss_detailed) > 0 else 0
        
        # 2. Net VAT from Dutch Return (row 3a - "Output VAT - Input VAT")
        dutch_net_row = dutch_vat_return[dutch_vat_return['Section'] == '3a. Output VAT - Input VAT']
        if len(dutch_net_row) > 0:
            dutch_net_str = dutch_net_row['Amount (€)'].values[0]
            # Remove commas and convert to float
            dutch_net_vat = float(dutch_net_str.replace(',', ''))
        else:
            dutch_net_vat = 0
        
        # 3. Duty Revenue (use config rates: 80% general, 70% IE, but IE is excluded from duty)
        if len(duty_return) > 0:
            # Filter out any non-country rows (like 'NOTE', 'TOTAL', etc.)
            duty_return_copy = duty_return[
                ~duty_return['Country'].isin(['NOTE', 'TOTAL', 'note'])
            ].copy()
            
            # Ensure numeric columns are actually numeric
            duty_return_copy['Total Duty Returned'] = pd.to_numeric(
                duty_return_copy['Total Duty Returned'], 
                errors='coerce'
            ).fillna(0)
            
            # Calculate duty revenue (80% for most countries, 70% for IE)
            # Note: IE should already be excluded from the duty_return data
            duty_return_copy['Duty Revenue'] = duty_return_copy.apply(
                lambda row: row['Total Duty Returned'] * Config.get_duty_revenue_rate(row['Country'])
                if row['Country'] not in Config.DUTY_EXCLUDED_COUNTRIES
                else 0,
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
                'Duty Returned To Pro Carrier (80% general, IE excluded)',
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
                'Revenue from duty refunds claimed from customs (company share, IE excluded)',
                '',
                'Summary of key financial movements'
            ]
        }
        
        financial_summary = pd.DataFrame(summary_data)
        
        # Save to Excel in vat_returns folder
        financial_summary.to_excel(
            data_dir / "FINANCIAL_SUMMARY.xlsx",
            index=False,
            engine='openpyxl'
        )
        
        print(f"\n💰 Financial Summary:")
        print(f"   📊 OSS VAT Due: €{oss_vat_due:,.2f}")
        print(f"   📊 Dutch Net VAT: €{dutch_net_vat:,.2f}")
        print(f"   📊 Duty Revenue: €{duty_revenue_total:,.2f}")
        
        return financial_summary
    
    @staticmethod
    def create_enhanced_dr_revenue_table(
        lv_dr_revenue_table: pd.DataFrame,
        hv_dr_revenue_table: pd.DataFrame,
        lv_return_vat: pd.DataFrame,
        hv_combined_refunds: pd.DataFrame,
        return_period: str
    ) -> pd.DataFrame:
        """
        Create enhanced DR revenue table with detailed breakdown by country.
        
        Args:
            lv_dr_revenue_table: LV DR revenue by country
            hv_dr_revenue_table: HV DR revenue by country
            lv_return_vat: LV VAT refunds by country
            hv_combined_refunds: HV combined VAT and duty refunds
            return_period: Tax period
            
        Returns:
            Enhanced DR revenue DataFrame
        """
        # Collect all unique countries
        all_countries = set()
        if len(lv_dr_revenue_table) > 0:
            all_countries.update(lv_dr_revenue_table['Country'].unique())
        if len(hv_dr_revenue_table) > 0:
            all_countries.update(hv_dr_revenue_table['Country'].unique())
        if len(lv_return_vat) > 0:
            all_countries.update(lv_return_vat['Country'].unique())
        if len(hv_combined_refunds) > 0:
            all_countries.update(hv_combined_refunds['Country'].unique())
        
        # Build comprehensive table
        dr_data = []
        for country in sorted(all_countries):
            # LV data
            lv_revenue = lv_dr_revenue_table[lv_dr_revenue_table['Country'] == country]['Revenue'].sum() \
                if len(lv_dr_revenue_table) > 0 and country in lv_dr_revenue_table['Country'].values else 0
            
            lv_vat_refund = lv_return_vat[lv_return_vat['Country'] == country]['Total VAT Refund'].sum() \
                if len(lv_return_vat) > 0 and country in lv_return_vat['Country'].values else 0
            
            # HV data
            hv_revenue = hv_dr_revenue_table[hv_dr_revenue_table['Country'] == country]['Revenue'].sum() \
                if len(hv_dr_revenue_table) > 0 and country in hv_dr_revenue_table['Country'].values else 0
            
            hv_vat_refund = hv_combined_refunds[hv_combined_refunds['Country'] == country]['Total VAT Refund'].sum() \
                if len(hv_combined_refunds) > 0 and country in hv_combined_refunds['Country'].values else 0
            
            # For IE, duty is always 0 (cannot be reclaimed)
            hv_duty_refund = 0 if country in Config.DUTY_EXCLUDED_COUNTRIES else (
                hv_combined_refunds[hv_combined_refunds['Country'] == country]['Total Duty Returned'].sum()
                if len(hv_combined_refunds) > 0 and country in hv_combined_refunds['Country'].values else 0
            )
            
            # Calculate totals
            total_vat_refund = lv_vat_refund + hv_vat_refund
            total_revenue = lv_revenue + hv_revenue
            commission_rate = Config.get_commission_rate(country)
            
            # Add note for IE
            note = 'No duty reclaim' if country in Config.DUTY_EXCLUDED_COUNTRIES else ''
            
            dr_data.append({
                'Country': country,
                'LV VAT Refund (€)': f'{lv_vat_refund:,.2f}',
                'LV DR Revenue (€)': f'{lv_revenue:,.2f}',
                'HV VAT Refund (€)': f'{hv_vat_refund:,.2f}',
                'HV Duty Refund (€)': f'{hv_duty_refund:,.2f}',
                'HV DR Revenue (€)': f'{hv_revenue:,.2f}',
                'Total VAT Refund (€)': f'{total_vat_refund:,.2f}',
                'Total DR Revenue (€)': f'{total_revenue:,.2f}',
                'Commission Rate': f'{commission_rate*100:.0f}%',
                'Notes': note
            })
        
        dr_detailed = pd.DataFrame(dr_data)
        
        # Calculate numeric totals for the footer (excluding IE duty)
        lv_vat_total = sum([lv_return_vat[lv_return_vat['Country'] == c]['Total VAT Refund'].sum() 
                           for c in all_countries if c in lv_return_vat['Country'].values])
        lv_revenue_total = sum([lv_dr_revenue_table[lv_dr_revenue_table['Country'] == c]['Revenue'].sum() 
                               for c in all_countries if c in lv_dr_revenue_table['Country'].values])
        hv_vat_total = sum([hv_combined_refunds[hv_combined_refunds['Country'] == c]['Total VAT Refund'].sum() 
                           for c in all_countries if c in hv_combined_refunds['Country'].values])
        
        # Duty total excludes IE
        hv_duty_total = sum([
            hv_combined_refunds[hv_combined_refunds['Country'] == c]['Total Duty Returned'].sum() 
            for c in all_countries 
            if c not in Config.DUTY_EXCLUDED_COUNTRIES 
            and c in hv_combined_refunds['Country'].values
        ])
        
        hv_revenue_total = sum([hv_dr_revenue_table[hv_dr_revenue_table['Country'] == c]['Revenue'].sum() 
                               for c in all_countries if c in hv_dr_revenue_table['Country'].values])
        
        # Add totals row
        totals = {
            'Country': 'TOTAL',
            'LV VAT Refund (€)': f'{lv_vat_total:,.2f}',
            'LV DR Revenue (€)': f'{lv_revenue_total:,.2f}',
            'HV VAT Refund (€)': f'{hv_vat_total:,.2f}',
            'HV Duty Refund (€)': f'{hv_duty_total:,.2f}',
            'HV DR Revenue (€)': f'{hv_revenue_total:,.2f}',
            'Total VAT Refund (€)': f'{lv_vat_total + hv_vat_total:,.2f}',
            'Total DR Revenue (€)': f'{lv_revenue_total + hv_revenue_total:,.2f}',
            'Commission Rate': '',
            'Notes': 'IE duty excluded'
        }
        
        dr_detailed = pd.concat([dr_detailed, pd.DataFrame([totals])], ignore_index=True)
        
        # Save to vat_returns folder
        vat_returns_dir = Path(Config.VAT_RETURNS_DIR)
        vat_returns_dir.mkdir(exist_ok=True)
        
        period_str = return_period.replace(' ', '_')
        dr_detailed.to_excel(
            vat_returns_dir / f"DR_REVENUE_DETAILED_{period_str}.xlsx",
            index=False,
            engine='openpyxl'
        )
        
        print(f"   📄 Enhanced DR Revenue: {vat_returns_dir / f'DR_REVENUE_DETAILED_{period_str}.xlsx'}")
        
        return dr_detailed
    
    @staticmethod
    def create_pc_revenue_table(
        lv_dr_revenue_table: pd.DataFrame,
        hv_dr_revenue_table: pd.DataFrame,
        lv_return_vat: pd.DataFrame,
        hv_combined_refunds: pd.DataFrame,
        return_period: str
    ) -> pd.DataFrame:
        """
        Create PC (Pro Carrier) revenue table with duty refunds only.
        PC gets the full duty refunds (100% of duty returned).
        VAT refunds go to customers, with DR taking commission.
        
        Args:
            lv_dr_revenue_table: LV DR revenue by country (not used for PC)
            hv_dr_revenue_table: HV DR revenue by country (not used for PC)
            lv_return_vat: LV VAT refunds by country (not applicable for PC)
            hv_combined_refunds: HV combined VAT and duty refunds
            return_period: Tax period
            
        Returns:
            PC revenue DataFrame (duty only)
        """
        # Collect all unique countries from HV duty refunds
        all_countries = set()
        if len(hv_combined_refunds) > 0:
            all_countries.update(hv_combined_refunds['Country'].unique())
        
        # Build PC duty table
        pc_data = []
        for country in sorted(all_countries):
            # For IE, duty is always 0 (cannot be reclaimed)
            hv_duty_refund = 0 if country in Config.DUTY_EXCLUDED_COUNTRIES else (
                hv_combined_refunds[hv_combined_refunds['Country'] == country]['Total Duty Returned'].sum()
                if len(hv_combined_refunds) > 0 and country in hv_combined_refunds['Country'].values else 0
            )
            
            # PC gets 100% of duty refunds (no commission taken)
            pc_duty_revenue = hv_duty_refund
            
            # Add note for IE
            note = 'No duty reclaim' if country in Config.DUTY_EXCLUDED_COUNTRIES else ''
            
            pc_data.append({
                'Country': country,
                'HV Duty Refund (€)': f'{hv_duty_refund:,.2f}',
                'PC Revenue from Duty (€)': f'{pc_duty_revenue:,.2f}',
                'Rate': '100%',
                'Notes': note
            })
        
        pc_detailed = pd.DataFrame(pc_data)
        
        # Calculate totals (excluding IE duty)
        hv_duty_total = sum([
            hv_combined_refunds[hv_combined_refunds['Country'] == c]['Total Duty Returned'].sum() 
            for c in all_countries 
            if c not in Config.DUTY_EXCLUDED_COUNTRIES 
            and c in hv_combined_refunds['Country'].values
        ])
        
        # Add totals row
        totals = {
            'Country': 'TOTAL',
            'HV Duty Refund (€)': f'{hv_duty_total:,.2f}',
            'PC Revenue from Duty (€)': f'{hv_duty_total:,.2f}',
            'Rate': '100%',
            'Notes': 'IE duty excluded'
        }
        
        pc_detailed = pd.concat([pc_detailed, pd.DataFrame([totals])], ignore_index=True)
        
        # Save to vat_returns folder
        vat_returns_dir = Path(Config.VAT_RETURNS_DIR)
        vat_returns_dir.mkdir(exist_ok=True)
        
        period_str = return_period.replace(' ', '_')
        pc_detailed.to_excel(
            vat_returns_dir / f"PC_DUTY_REVENUE_{period_str}.xlsx",
            index=False,
            engine='openpyxl'
        )
        
        print(f"   📄 PC Duty Revenue: {vat_returns_dir / f'PC_DUTY_REVENUE_{period_str}.xlsx'}")
        
        return pc_detailed

