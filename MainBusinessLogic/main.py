import pandas as pd
from data_layer import DataLayer
from low_value_processor import LowValueProcessor
from high_value_processor import HighValueProcessor
from duty_processor import DutyProcessor
from services import Services
from vat_return_forms import VATReturnForms
import warnings

warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


def main():
    """Main application function."""
    csv_path = "TED BAKER DUTY CLAIM BACK Jul-Sep v2.csv"
    duty_excel_path = "Duties Import Jan 99.xlsx"

    print("📊 Starting VAT Analysis...")

    # Process duty data
    print("📦 Processing duty data...")
    duty_data = pd.read_excel(duty_excel_path)
    duty_dict = DutyProcessor.process_duty_data(duty_data)

    # Load and separate data
    low_value_df, high_value_df = DataLayer.load_data(csv_path)

    # Process low value consignments
    print("💶 Processing low value consignments...")
    low_values_data, lv_data_for_form = LowValueProcessor.process_low_value_data(low_value_df)

    # Process high value consignments
    print("💷 Processing high value consignments...")
    high_values_data, hv_data_for_form = HighValueProcessor.process_high_value_data(high_value_df, duty_dict)

    # Generate summary
    print("📋 Generating summary...")
    Services.summary_table(low_values_data, high_values_data)

    # ===== NEW: Generate VAT Return Forms =====
    print("\n📝 Generating VAT Return Forms...")

    # Prepare data for forms
    lv_form_data = {
        'vat_per_country': lv_data_for_form[0],
        'return_vat_per_country': lv_data_for_form[1]
    }

    hv_form_data = {
        'vat_to_return_from_nl': high_values_data[0],
        'vat_per_country': hv_data_for_form[0],
        'return_vat_per_country': hv_data_for_form[2],
        'duty_returned_by_country': hv_data_for_form[1]
    }

    # Generate and save all forms
    VATReturnForms.save_all_forms(lv_form_data, hv_form_data, return_period="Q3 2024")

    print("\n✅ Analysis complete!")
    print("📁 Check the 'data' folder for analysis reports.")
    print("📁 Check the 'vat_returns' folder for ready-to-file forms.")


if __name__ == "__main__":
    main()