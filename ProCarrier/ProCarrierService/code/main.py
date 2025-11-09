"""Main application entry point - VAT Analysis Tool."""

import pandas as pd
from ProCarrier.ProCarrierService.code.data_layer import DataLayer
from ProCarrier.ProCarrierService.code.low_value_processor import LowValueProcessor
from ProCarrier.ProCarrierService.code.high_value_processor import HighValueProcessor
from ProCarrier.ProCarrierService.code.duty_processor import DutyProcessor
from services import Services
from ProCarrier.ProCarrierService.code.config import Config
import warnings
from pathlib import Path

warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


def process_data(file_name: str, data_type: str, output_folder):
    """
    Process VAT and duty data from a given file.
    
    Args:
        file_name: Name or path of the file to process (e.g., "JUL-SEP DATA.csv" or "OCT DATA.xlsx")
        data_type: Type of the data file - either "csv" or "xlsx"
        output_folder: Name of the folder where results should be saved (optional, defaults to "data")
    
    Returns:
        Dictionary containing all processed data
    """
    # Validate data type
    if data_type not in ['csv', 'xlsx']:
        raise ValueError(f"Invalid data_type: {data_type}. Must be 'csv' or 'xlsx'")
    

    output_dir = f"../{output_folder}/"
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    Config.DATA_DIR = output_dir
    
    try:
        # ==================== PROCESS DUTY DATA ====================
        duty_data = pd.read_excel(Config.DEFAULT_DUTY_EXCEL_PATH)
        duty_dict = DutyProcessor.process_duty_data(duty_data)

        # ==================== LOAD CONSIGNMENT DATA ====================
        print(f"📂 Loading {data_type.upper()} file: {file_name}")
        
        if data_type == 'csv':
            low_value_df, high_value_df = DataLayer.load_data(file_name)
        elif data_type == 'xlsx':
            low_value_df, high_value_df = DataLayer.load_excel(file_name)

        # ==================== PROCESS LV and HV consignments ====================
        print("⚙️  Processing low-value consignments...")
        lv_vat_per_country_df = LowValueProcessor.process_low_value_data(low_value_df)

        print("⚙️  Processing high-value consignments...")
        # return [vat_that_was_paid_by_broker_in_nl, vat_to_return_from_nl, combined_vat_per_country, combined_refunds]
        nl_values, ie_values = HighValueProcessor.process_high_value_data(high_value_df, duty_dict)

        vat_that_was_paid_by_broker_in_nl, vat_to_return_from_nl, hv_vat_per_country, nl_combined_refunds = nl_values
        ie_combined_refunds = ie_values[0]


        # ==================== GENERATE FORMS ====================
        print("📊 Generating summary and revenue tables...")

        form = {
            # stats only
            'VAT_PAID_DURING_IMPORT_TO_NL': vat_that_was_paid_by_broker_in_nl,

            # VAT form
            'VAT_TO_RETURN_FROM_NL_FOR_IMPORT': vat_to_return_from_nl,
            'LV_VAT_DF': lv_vat_per_country_df,

            # OSS VAT form
            'OSS_HV_VAT_DF': hv_vat_per_country,

            # Combined refunds
            'IE_REFUNDS': ie_combined_refunds,
            'NL_REFUNDS': nl_combined_refunds,
        }

        Services.generate_summary_table(form)

        print(f'✅ DONE! Results saved to: {output_dir}')
        
        return form
    finally:
        print("DONE")


def main():
    """Default execution with hardcoded values."""
    process_data(
        file_name="../OCT DATA.xlsx",
        data_type='xlsx',
        output_folder='./OCT_RESULTS'
    )


if __name__ == "__main__":
    main()