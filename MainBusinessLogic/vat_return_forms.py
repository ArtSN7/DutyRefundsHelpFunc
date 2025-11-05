"""Generate VAT return forms: Dutch VAT Return (IOSS + NL) and OSS Return."""

import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any
from datetime import datetime
from services import Services


class VATReturnForms:
    """Generate ready-to-file VAT return forms."""
    
    @staticmethod
    def generate_dutch_vat_return(
        lv_data: Dict[str, pd.DataFrame],
        hv_data: Dict[str, pd.DataFrame],
        return_period: str = "Q3 2024"
    ) -> pd.DataFrame:
        """
        Generate Dutch VAT Return form data (for IOSS + NL high value parcels).
        
        This form includes:
        - IOSS VAT (low value parcels ≤€150)
        - NL high value parcels that stayed in NL
        - Import VAT to reclaim (for parcels to other countries)
        - NL returns adjustments
        
        Args:
            lv_data: Low value data dictionary
            hv_data: High value data dictionary
            return_period: Tax period (e.g., "Q3 2024")
            
        Returns:
            DataFrame with Dutch VAT Return form data
        """
        
        # Extract data
        lv_vat_per_country = lv_data['vat_per_country']
        lv_return_vat = lv_data['return_vat_per_country']
        hv_vat_to_return_from_nl = hv_data['vat_to_return_from_nl']
        hv_vat_per_country = hv_data['vat_per_country']
        hv_return_vat = hv_data['return_vat_per_country']
        
        # SECTION 1: IOSS (Low Value) - All countries
        ioss_sales = lv_vat_per_country['Total VAT to Pay'].sum()
        ioss_returns = lv_return_vat['Total VAT Refund'].sum()
        ioss_net = ioss_sales - ioss_returns
        
        # SECTION 2: NL High Value (parcels that stayed in NL)
        nl_hv_sales = hv_vat_per_country[
            hv_vat_per_country['Country'] == 'NL'
        ]['Total VAT to Pay'].sum() if 'NL' in hv_vat_per_country['Country'].values else 0
        
        nl_hv_returns = hv_return_vat[
            hv_return_vat['Country'] == 'NL'
        ]['Total VAT Refund'].sum() if 'NL' in hv_return_vat['Country'].values else 0
        
        nl_hv_net = nl_hv_sales - nl_hv_returns
        
        # SECTION 3: Import VAT to Reclaim (for parcels to other countries)
        import_vat_reclaim = hv_vat_to_return_from_nl
        
        # Calculate totals
        output_vat = ioss_net + nl_hv_net  # Box 1: What you owe
        input_vat = import_vat_reclaim      # Box 5: What you can deduct
        net_vat = output_vat - input_vat    # Net position (negative = refund)
        
        # Create form data
        form_data = {
            'Section': [
                '1. OUTPUT VAT (Omzetbelasting)',
                '1a. IOSS Sales (Low Value ≤€150) - All Countries',
                '1b. IOSS Returns (Credit)',
                '1c. IOSS Net',
                '1d. NL High Value Sales (>€150 stayed in NL)',
                '1e. NL High Value Returns (Credit)',
                '1f. NL High Value Net',
                '1g. TOTAL OUTPUT VAT (Box 1)',
                '',
                '2. INPUT VAT (Voorbelasting)',
                '2a. Import VAT to Reclaim (parcels to other EU countries)',
                '2b. TOTAL INPUT VAT (Box 5)',
                '',
                '3. NET VAT POSITION',
                '3a. Output VAT - Input VAT',
                '3b. Status'
            ],
            'Amount (€)': [
                '',
                f'{ioss_sales:,.2f}',
                f'-{ioss_returns:,.2f}',
                f'{ioss_net:,.2f}',
                f'{nl_hv_sales:,.2f}',
                f'-{nl_hv_returns:,.2f}',
                f'{nl_hv_net:,.2f}',
                f'{output_vat:,.2f}',
                '',
                '',
                f'{import_vat_reclaim:,.2f}',
                f'{input_vat:,.2f}',
                '',
                '',
                f'{net_vat:,.2f}',
                'REFUND DUE' if net_vat < 0 else 'PAYMENT DUE'
            ],
            'Box Number': [
                '',
                '1a',
                '1a (credit)',
                '1a',
                '1a',
                '1a (credit)',
                '1a',
                'Box 1 Total',
                '',
                '',
                '5b',
                'Box 5 Total',
                '',
                '',
                'Net',
                ''
            ],
            'Notes': [
                'VAT collected from sales',
                'All IOSS countries combined',
                'Returns reduce output VAT',
                'Net IOSS to declare',
                'Parcels that stayed in Netherlands ( 0 - as broker already paid for them during import )',
                'NL customer returns ( VAT that could be claimed back for HV parcels that were returned from NL )',
                'Net NL high value',
                'Total VAT you owe ( what we need to invoice from PC ( if value is positive ) or return ( if values is negative ) )',
                '',
                'VAT you can deduct ( return money that were paid by broker during import )',
                'Reclaim from import VAT paid by broker ( need to return that amount for parcels that didnt stay in NL )',
                'Total deductible VAT',
                '',
                'Final calculation',
                'Output VAT minus Input VAT ( amount of money that we need to get from NL tax office or pay to them for operations within NL - no other EU countries )',
                'Automatic bank refund if negative'
            ]
        }
        
        df = pd.DataFrame(form_data)
        
        # Add metadata
        df.attrs['return_period'] = return_period
        df.attrs['generated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return df
    
    @staticmethod
    def generate_oss_return(
        hv_data: Dict[str, pd.DataFrame],
        return_period: str = "Q3 2024"
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate OSS VAT Return form data (for high value parcels to other EU countries).
        
        This form includes:
        - Sales to each EU country (excluding NL)
        - Returns from each EU country (as negative)
        
        Args:
            hv_data: High value data dictionary
            return_period: Tax period (e.g., "Q3 2024")
            
        Returns:
            Tuple of (detailed_form, summary_form)
        """
        
        # Extract data
        hv_vat_per_country = hv_data['vat_per_country']
        hv_return_vat = hv_data['return_vat_per_country']
        
        # Exclude NL (OSS is only for other countries)
        sales_data = hv_vat_per_country[
            hv_vat_per_country['Country'] != 'NL'
        ].copy()
        
        return_data = hv_return_vat[
            hv_return_vat['Country'] != 'NL'
        ].copy()
        
        # Merge sales and returns
        merged = pd.merge(
            sales_data,
            return_data[['Country', 'Total VAT Refund']],
            on='Country',
            how='outer'
        ).fillna(0)
        
        # Calculate net VAT per country
        merged['Net VAT Due'] = merged['Total VAT to Pay'] - merged['Total VAT Refund']
        
        # Rename for clarity
        merged = merged.rename(columns={
            'Total VAT to Pay': 'Sales VAT',
            'Total VAT Refund': 'Returns VAT (Credit)',
            'Total Consignment Value': 'Taxable Amount (excl VAT)'
        })
        
        # Reorder columns
        detailed_form = merged[[
            'Country',
            'VAT Rate',
            'Taxable Amount (excl VAT)',
            'Sales VAT',
            'Returns VAT (Credit)',
            'Net VAT Due'
        ]]
        
        # Create summary
        summary_data = {
            'Metric': [
                'Total Sales VAT',
                'Total Returns VAT (Credit)',
                'NET OSS VAT DUE',
                'Payment Deadline',
                'Member State of Identification'
            ],
            'Value': [
                f"€{detailed_form['Sales VAT'].sum():,.2f}",
                f"€{detailed_form['Returns VAT (Credit)'].sum():,.2f}",
                f"€{detailed_form['Net VAT Due'].sum():,.2f}",
                'End of month following quarter',
                'Netherlands (NL)'
            ]
        }
        
        summary_form = pd.DataFrame(summary_data)
        
        # Add metadata
        detailed_form.attrs['return_period'] = return_period
        detailed_form.attrs['generated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return detailed_form, summary_form
    
    @staticmethod
    def generate_duty_return_form(
        hv_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Generate Duty Return Claim form for returned parcels.
        
        This is a SEPARATE claim submitted to Dutch Customs (not tax office).
        NOTE: Ireland (IE) is EXCLUDED - duty cannot be reclaimed from IE.
        
        Args:
            hv_data: High value data dictionary
            
        Returns:
            DataFrame with duty return claim data
        """
        
        # FIX: Check if duty_returned_by_country exists and is a DataFrame
        if 'duty_returned_by_country' not in hv_data:
            print("⚠️  Warning: No duty return data found. Creating empty form.")
            return pd.DataFrame({
                'Country': [],
                'Total Returned Value': [],
                'Total Duty Returned': [],
            })
        
        duty_returns = hv_data['duty_returned_by_country']
        
        # FIX: Check if it's a DataFrame
        if not isinstance(duty_returns, pd.DataFrame):
            print(f"⚠️  Warning: duty_returned_by_country is {type(duty_returns)}, not DataFrame. Creating empty form.")
            return pd.DataFrame({
                'Country': [],
                'Total Returned Value': [],
                'Total Duty Returned': [],
            })
        
        # FIX: Make a copy to avoid modifying original
        form = duty_returns[[
            'Country',
            'Total Returned Value',
            'Total Duty Returned',
        ]].copy()
        
        # Add note about IE exclusion in the metadata/attrs instead of as a row
        form.attrs['note'] = 'Ireland (IE) excluded - duty cannot be reclaimed from IE'
        
        return form
    
    @staticmethod
    def save_all_forms(
        lv_data: Dict[str, pd.DataFrame],
        hv_data: Dict[str, pd.DataFrame],
        return_period: str = "Q3 2024"
    ) -> None:
        """Save all VAT return forms to Excel files."""
        
        # Create output directory
        forms_dir = Path("vat_returns")
        forms_dir.mkdir(exist_ok=True)
        
        print("\n📝 Generating VAT return forms...")
        
        # Generate Dutch VAT Return
        print("   ✅ Dutch VAT Return...")
        dutch_vat_return = VATReturnForms.generate_dutch_vat_return(
            lv_data, hv_data, return_period
        )
        
        # Generate OSS Return
        print("   ✅ OSS VAT Return...")
        oss_detailed, oss_summary = VATReturnForms.generate_oss_return(
            hv_data, return_period
        )
        
        # Generate Duty Return Claim
        print("   ✅ Duty Return Claim...")
        duty_return = VATReturnForms.generate_duty_return_form(hv_data)
        
        # Save to Excel files
        dutch_vat_return.to_excel(
            forms_dir / f"DUTCH_VAT_RETURN_{return_period.replace(' ', '_')}.xlsx",
            index=False,
            engine='openpyxl'
        )
        
        with pd.ExcelWriter(
            forms_dir / f"OSS_VAT_RETURN_{return_period.replace(' ', '_')}.xlsx",
            engine='openpyxl'
        ) as writer:
            oss_detailed.to_excel(writer, sheet_name='Detailed', index=False)
            oss_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        duty_return.to_excel(
            forms_dir / f"DUTY_RETURN_CLAIM_{return_period.replace(' ', '_')}.xlsx",
            index=False,
            engine='openpyxl'
        )
        
        print(f"\n✅ VAT Return Forms Generated:")
        print(f"   📄 Dutch VAT Return: {forms_dir / f'DUTCH_VAT_RETURN_{return_period.replace(' ', '_')}.xlsx'}")
        print(f"   📄 OSS VAT Return: {forms_dir / f'OSS_VAT_RETURN_{return_period.replace(' ', '_')}.xlsx'}")
        print(f"   📄 Duty Return Claim: {forms_dir / f'DUTY_RETURN_CLAIM_{return_period.replace(' ', '_')}.xlsx'}")
        
        # Generate financial summary from the forms
        print("\n💰 Generating Financial Summary...")
        Services.create_financial_summary(dutch_vat_return, oss_detailed, duty_return)
        print(f"   📄 Financial Summary: vat_returns/FINANCIAL_SUMMARY.xlsx")
