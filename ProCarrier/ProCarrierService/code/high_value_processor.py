"""High value consignment processor (>150€)."""

import pandas as pd
from typing import Any, Dict
from ProCarrier.ProCarrierService.code.config import Config
from services import Services

import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)



class HighValueProcessor:
    """Processes high value consignments (>150€)."""

    @staticmethod
    def process_high_value_data(df: pd.DataFrame, duty_dict: Dict[str, float]) -> tuple[list[Any], Any]:
        df = HighValueProcessor.clean_columns(df)

        # calculate duty paid first
        df = HighValueProcessor.duty_paid(df, duty_dict)

        # Separate HV consignments declared in IE vs NL
        hv_declared_in_IE , hv_declared_in_NL = HighValueProcessor.separate_by_declaration_country(df)

        # ==================== HV DECLARED IN NL ==============================
        nl_results = HighValueProcessor.hv_nl_processing(hv_declared_in_NL, duty_dict)

        # ==================== HV DECLARED IN IE ==============================
        ie_results = HighValueProcessor.hv_ie_processing(hv_declared_in_IE, duty_dict)

        return (nl_results, ie_results)


    @staticmethod
    def hv_ie_processing(hv_declared_in_IE: pd.DataFrame, duty_dict: Dict[str, float]) -> list[Any]:
        return_rgr= HighValueProcessor.calculate_rgr_vat_return(hv_declared_in_IE, Config.VAT_RATES['IE']) # for rgr IE form
        return_rgr['Total Refund'] = return_rgr['Total VAT Refund']

        Services.store_ie_hv_data(return_rgr)

        return [return_rgr]


    @staticmethod
    def hv_nl_processing(hv_declared_in_NL: pd.DataFrame, duty_dict: Dict[str, float]) -> list[Any]:
        # Calculate import VAT that was paid by broker in NL
        vat_that_was_paid_by_broker_in_nl = HighValueProcessor.calculate_vat_paid_by_broker_in_nl(hv_declared_in_NL) # for summary

        # Calculate import VAT that was paid by broker to return from NL
        vat_to_return_from_nl = HighValueProcessor.calculate_vat_to_return_from_nl(hv_declared_in_NL) # for dutch vat form

        # Calculate VAT per country to submit to NL for OSS ( excluding NL shipments, as for them broker already paid vat )
        vat_per_country = HighValueProcessor.calculate_vat_per_country(hv_declared_in_NL) # for oss form import

        # calculate return VAT per country to subtract from OSS declaration as returned
        return_vat_per_country = HighValueProcessor.calculate_return_vat_per_country(hv_declared_in_NL) # for oss form returns

        # combine both to create final vat per country for oss form
        combined_vat_per_country = HighValueProcessor.create_combined_vat_per_country(vat_per_country, return_vat_per_country)

        # Calculate VAT refunds for returned items for RGR NL form ( based on imported vat and duty paid )
        return_rgr= HighValueProcessor.calculate_rgr_vat_return(hv_declared_in_NL, Config.VAT_RATES['NL']) # for rgr nl form
        duty_returned_by_country = HighValueProcessor.calculate_duty_for_returned_items(hv_declared_in_NL, duty_dict)
        # Merge duty and VAT refunds by country
        combined_refunds = HighValueProcessor.duty_vat_hv_merge(return_rgr, duty_returned_by_country)

        # Save reports to CSV files
        Services.store_hv_data(combined_vat_per_country, combined_refunds) # ALSO NEED TO PRODUCE A RGR FILE FOR EACH RETURNED PARCEL

        return [vat_that_was_paid_by_broker_in_nl, vat_to_return_from_nl, combined_vat_per_country, combined_refunds]


    @staticmethod
    def calculate_rgr_vat_return(df: pd.DataFrame, vat_rate : float) -> pd.DataFrame:
        """Calculate VAT refunds for returned items per country."""
        # Filter rows where items were returned
        returned_df = df[df['Line Item Quantity Returned'] > 0].copy()

        # Calculate total returned value for each line item
        returned_df['Returned Item Value'] = (
                returned_df['Line Item Quantity Returned'] *
                returned_df['Line Item Unit Price']
        )

        # Calculate VAT refund for each returned item
        returned_df['VAT Refund'] = returned_df['Returned Item Value'] * vat_rate

        # Group by Country and VAT Rate
        summary = returned_df.groupby(['Consignee Country', 'VAT Rate']).agg({
            'Returned Item Value': 'sum',
            'VAT Refund': 'sum'
        }).reset_index()

        # Rename columns for clarity
        summary.columns = ['Country', 'VAT Rate', 'Total Returned Value', 'Total VAT Refund']

        return summary


    @staticmethod
    def create_combined_vat_per_country(vat_per_country: pd.DataFrame,
                                        return_vat_per_country: pd.DataFrame) -> pd.DataFrame:
        combined_vat_per_country = pd.merge(
            vat_per_country,
            return_vat_per_country[['Country', 'Total VAT Refund']],
            on='Country',
            how='outer'
        )
        # Fill NaN values with 0
        combined_vat_per_country = combined_vat_per_country.fillna({
            'VAT Rate': 0,
            'Total Consignment Value': 0,
            'Total VAT to Pay': 0,
            'Total VAT Refund': 0
        })
        combined_vat_per_country['NET VAT'] = combined_vat_per_country['Total VAT to Pay'] - combined_vat_per_country['Total VAT Refund']

        return combined_vat_per_country[['Country', 'VAT Rate', 'Total VAT to Pay', 'Total VAT Refund', 'NET VAT']]


    @staticmethod
    def calculate_return_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT refunds for returned items."""
        df = df[df['Consignee Country'] != 'NL']  # Exclude NL shipments
        return Services.calculate_return_vat_per_country(df)


    @staticmethod
    def duty_paid(df: pd.DataFrame, duty_dict: Dict[str, float]) -> pd.DataFrame:
        """Calculate duty paid for high value consignments."""
        # Extract first 4 digits from HS CODE
        df['Goods_Code_4'] = df['HS CODE'].astype(str).str[:4]

        # Map duty rates
        df['Duty Rate'] = df['Goods_Code_4'].map(duty_dict)

        # Calculate item value
        df['Item Value'] = (
            df['Line Item Quantity Imported'] *
            df['Line Item Unit Price']
        )

        # Calculate Duty
        df['Duty'] = df['Item Value'] * df['Duty Rate']

        return df


    @staticmethod
    def separate_by_declaration_country(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        df['decl_country'] = df['MRN'].str[2:4].str.upper()
        hv_declared_in_IE = df[df['decl_country'] == 'IE'].copy()
        hv_declared_in_nl = df[df['decl_country'] != 'IE'].copy()
        hv_declared_in_IE.drop(columns=['decl_country'], inplace=True)
        hv_declared_in_nl.drop(columns=['decl_country'], inplace=True)
        return hv_declared_in_IE, hv_declared_in_nl


    @staticmethod
    def calculate_vat_difference_payment_txt(df: pd.DataFrame) -> str:
        """Calculate VAT difference payment text."""
        vat_in_nl = df['VAT Paid In NL'].sum()
        vat_in_consignee_country = df['VAT Paid In Consignee Country'].sum()
        difference = vat_in_nl - vat_in_consignee_country

        if difference > 0:
            return f'DR needs to return PC an amount of €{difference:.4f} for VAT differences.'
        return f'PC needs to pay DR extra an amount of €{abs(difference):.4f} for VAT differences.'

    @staticmethod
    def create_vat_difference_table(vat_per_country: pd.DataFrame) -> pd.DataFrame:
        """Create VAT difference table comparing NL VAT vs consignee country VAT."""
        vat_difference_table = vat_per_country.copy()

        # Calculate VAT that was paid in NL (21% of consignment value)
        vat_difference_table['VAT Paid In NL'] = vat_difference_table['Total Consignment Value'] * Config.NL_VAT_RATE

        # Rename for clarity
        vat_difference_table = vat_difference_table.rename(columns={
            'Total VAT to Pay': 'VAT Paid In Consignee Country'
        })

        # Reorder columns
        vat_difference_table = vat_difference_table[
            ['Country', 'VAT Rate', 'Total Consignment Value', 'VAT Paid In NL', 'VAT Paid In Consignee Country']]

        return vat_difference_table


    @staticmethod
    def duty_vat_hv_merge(vat_df: pd.DataFrame, duty_df: pd.DataFrame) -> pd.DataFrame:
        """Merge VAT and Duty refund dataframes."""
        merged_df = pd.merge(
            vat_df,
            duty_df[['Country', 'Total Duty Returned']],
            on='Country',
            how='outer'
        )

        # Fill NaN with 0
        merged_df = merged_df.fillna({
            'VAT Rate': 0,
            'Total Returned Value': 0,
            'Total VAT Refund': 0,
            'Total Duty Returned': 0
        })

        # Calculate Total Refund (VAT + Duty)
        merged_df['Total Refund'] = merged_df['Total VAT Refund'] + merged_df['Total Duty Returned']

        # Reorder columns
        merged_df = merged_df[[
            'Country', 'VAT Rate', 'Total Returned Value',
            'Total VAT Refund', 'Total Duty Returned', 'Total Refund'
        ]]

        merged_df['VAT Rate'] = 0.21

        return merged_df

    @staticmethod
    def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Keep only relevant columns for high value consignments."""
        return df[Config.high_value_columns]

    @staticmethod
    def calculate_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT per country."""
        df = df[df['Consignee Country'] != 'NL']  # Exclude NL shipments
        return Services.calculate_vat_per_country(df)


    @staticmethod
    def calculate_duty_for_returned_items(df: pd.DataFrame, duty_dict: Dict[str, float]) -> pd.DataFrame:
        """Calculate duty refunds for returned items."""
        returned_df = df[df['Line Item Quantity Returned'] > 0].copy()

        # EXCLUDE IE - Duty cannot be reclaimed from Ireland
        returned_df = returned_df[~returned_df['Consignee Country'].isin(Config.DUTY_EXCLUDED_COUNTRIES)]

        # Extract first 4 digits from HS CODE
        returned_df['Goods_Code_4'] = returned_df['HS CODE'].astype(str).str[:4]

        # Map duty rates
        returned_df['Duty Rate'] = returned_df['Goods_Code_4'].map(duty_dict)

        # Calculate returned value
        returned_df['Returned Item Value'] = (
            returned_df['Line Item Quantity Returned'] *
            returned_df['Line Item Unit Price']
        )

        # Calculate Duty
        returned_df['Duty Amount'] = returned_df['Returned Item Value'] * returned_df['Duty Rate']

        # Group by country
        duty_by_country = returned_df.groupby('Consignee Country').agg({
            'Returned Item Value': 'sum',
            'Duty Amount': 'sum'
        }).reset_index()

        duty_by_country.columns = ['Country', 'Total Returned Value', 'Total Duty Returned']

        return duty_by_country

    @staticmethod
    def calculate_vat_to_return_from_nl(df: pd.DataFrame) -> float:
        """Calculate total NL VAT to be returned."""
        unique_consignments = df.drop_duplicates(subset=['MRN'])
        # remove everything shipped to NL, as VAT was already been paid
        unique_consignments = unique_consignments[unique_consignments['Consignee Country'] != 'NL']
        unique_consignments['VAT Amount'] = ( unique_consignments['Consignment Value'] + unique_consignments['Duty'] ) * Config.VAT_RATES['NL']
        total_nl_vat = unique_consignments['VAT Amount'].sum()
        return total_nl_vat

    @staticmethod
    def calculate_vat_paid_by_broker_in_nl(df: pd.DataFrame) -> float:
        unique_consignments = df.drop_duplicates(subset=['MRN'])
        unique_consignments['VAT Amount'] = ( unique_consignments['Consignment Value'] + unique_consignments['Duty'] ) * Config.VAT_RATES['NL']
        total_vat_paid = unique_consignments['VAT Amount'].sum()
        return total_vat_paid

