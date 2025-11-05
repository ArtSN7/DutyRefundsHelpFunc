"""Main application entry point - VAT Analysis Tool."""

import pandas as pd
from pathlib import Path
from data_layer import DataLayer
from low_value_processor import LowValueProcessor
from high_value_processor import HighValueProcessor
from duty_processor import DutyProcessor
from services import Services
from vat_return_forms import VATReturnForms
from config import Config
import warnings

warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


def main():
    """
    Main application workflow.
    
    Process Flow:
    1. Load and process duty rates
    2. Load and separate consignment data
    3. Process low value (IOSS) consignments
    4. Process high value (OSS) consignments
    5. Generate analysis summary
    6. Generate VAT return forms
    7. Generate enhanced DR revenue table
    """
    
    # ==================== CONFIGURATION ====================
    print("=" * 80)
    print("📊 VAT ANALYSIS TOOL")
    print("=" * 80)
    print(f"Return Period: {Config.DEFAULT_RETURN_PERIOD}")
    print(f"Data Source: {Config.DEFAULT_CSV_PATH}")
    print("=" * 80)
    
    # ==================== STEP 1: PROCESS DUTY DATA ====================
    print("\n📦 Step 1/7: Processing duty rates...")
    duty_data = pd.read_excel(Config.DEFAULT_DUTY_EXCEL_PATH)
    duty_dict = DutyProcessor.process_duty_data(duty_data)
    print(f"   ✅ Loaded {len(duty_dict)} duty rates")

    # ==================== STEP 2: LOAD CONSIGNMENT DATA ====================
    print("\n📂 Step 2/7: Loading consignment data...")
    low_value_df, high_value_df = DataLayer.load_data(Config.DEFAULT_CSV_PATH)
    print(f"   ✅ Low value (IOSS ≤€{Config.CONSIGNMENT_THRESHOLD}): {len(low_value_df)} consignments")
    print(f"   ✅ High value (OSS >€{Config.CONSIGNMENT_THRESHOLD}): {len(high_value_df)} consignments")

    # ==================== STEP 3: PROCESS LOW VALUE (IOSS) ====================
    print("\n💶 Step 3/7: Processing low value consignments (IOSS)...")
    low_values_data, lv_data_for_form = LowValueProcessor.process_low_value_data(low_value_df)
    
    # Extract LV metrics
    lv_dr_revenue = low_values_data[0]
    lv_pc_return = low_values_data[1]
    lv_total_vat_from_returns = low_values_data[2]
    lv_total_import_vat = low_values_data[3]
    
    print(f"   ✅ IOSS VAT to pay: €{lv_total_import_vat:,.2f}")
    print(f"   ✅ DR Revenue (LV): €{lv_dr_revenue:,.2f}")
    print(f"   ✅ PC to return: €{lv_pc_return:,.2f}")

    # ==================== STEP 4: PROCESS HIGH VALUE (OSS) ====================
    print("\n💷 Step 4/7: Processing high value consignments (OSS)...")
    high_values_data, hv_data_for_form = HighValueProcessor.process_high_value_data(
        high_value_df, duty_dict
    )
    
    # Extract HV metrics
    hv_vat_to_return = high_values_data[0]
    hv_dr_revenue = high_values_data[1]
    hv_vat_difference_txt = high_values_data[2]
    hv_vat_to_pay_total = high_values_data[3]
    
    print(f"   ✅ Import VAT to reclaim: €{hv_vat_to_return:,.2f}")
    print(f"   ✅ OSS VAT due: €{hv_vat_to_pay_total:,.2f}")
    print(f"   ✅ DR Revenue (HV): €{hv_dr_revenue:,.2f}")

    # ==================== STEP 5: GENERATE SUMMARY ====================
    print("\n📋 Step 5/7: Generating analysis summary...")
    Services.summary_table(low_values_data, high_values_data)
    total_dr_revenue = lv_dr_revenue + hv_dr_revenue
    print(f"   ✅ Total DR Revenue: €{total_dr_revenue:,.2f}")
    print(f"   ✅ Summary saved to {Config.DATA_DIR}")

    # ==================== STEP 6: PREPARE FORM DATA ====================
    print("\n📝 Step 6/7: Preparing VAT return forms...")
    
    # Prepare LV form data
    lv_form_data = {
        'vat_per_country': lv_data_for_form[0],
        'return_vat_per_country': lv_data_for_form[1]
    }
    
    # Prepare HV form data (merge duty and VAT refunds)
    hv_combined_refunds = HighValueProcessor.duty_vat_hv_merge(
        hv_data_for_form[2],  # return_vat_per_country
        hv_data_for_form[1]   # duty_returned_by_country
    )
    
    hv_form_data = {
        'vat_to_return_from_nl': hv_vat_to_return,
        'vat_per_country': hv_data_for_form[0],
        'return_vat_per_country': hv_data_for_form[2],
        'duty_returned_by_country': hv_data_for_form[1],
        'combined_refunds': hv_combined_refunds
    }

    # ==================== STEP 7: GENERATE VAT FORMS ====================
    print("\n🎯 Step 7/7: Generating VAT return forms...")
    
    # Create vat_returns directory
    forms_dir = Path(Config.VAT_RETURNS_DIR)
    forms_dir.mkdir(exist_ok=True)
    
    # Generate standard VAT forms
    VATReturnForms.save_all_forms(
        lv_form_data, 
        hv_form_data, 
        Config.DEFAULT_RETURN_PERIOD
    )
    
    # Generate enhanced DR Revenue table
    print("\n💰 Generating Enhanced DR Revenue Table...")

    
    _, lv_dr_revenue_table = LowValueProcessor.calculate_dr_revenue_from_lw_returns(
        lv_data_for_form[1]
    )
    
    _, hv_dr_revenue_table = HighValueProcessor.calculate_dr_revenue_from_hw_returns(
        hv_combined_refunds
    )
    
    Services.create_enhanced_dr_revenue_table(
        lv_dr_revenue_table,
        hv_dr_revenue_table,
        lv_data_for_form[1],  # lv_return_vat_per_country
        hv_combined_refunds,
        Config.DEFAULT_RETURN_PERIOD
    )


    # ==================== COMPLETION ====================
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()