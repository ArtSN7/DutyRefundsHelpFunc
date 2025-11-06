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
    # ==================== PROCESS DUTY DATA ====================
    print("\nStep 1/7: Processing duty rates...")
    duty_data = pd.read_excel(Config.DEFAULT_DUTY_EXCEL_PATH)
    duty_dict = DutyProcessor.process_duty_data(duty_data)

    # ==================== LOAD CONSIGNMENT DATA ====================
    print("\nStep 2/7: Loading consignment data...")
    low_value_df, high_value_df = DataLayer.load_data(Config.DEFAULT_CSV_PATH)


    # ==================== PROCESS LV and HV consignments ====================

    #return [vat_per_country, return_vat_per_country]
    vat_per_country, return_vat_per_country = LowValueProcessor.process_low_value_data(low_value_df)

    #return [Total Broker Paid, What we can return from NL, vat_per_country combined_refunds_df]
    vat_that_was_paid_by_broker_in_nl, vat_to_return_from_nl, hv_vat_per_country, combined_refunds = HighValueProcessor.process_high_value_data(high_value_df, duty_dict)

    # ==================== PROCESS LV and HV consignments ====================

    form = {
        # stats only
        'VAT Broker Paid During Import in NL for HV:': vat_that_was_paid_by_broker_in_nl,

        # VAT form
        'VAT to Return from NL for HV parcels that didnt stay in NL:': vat_to_return_from_nl, # to fill box 5b
        'VAT per Country DataFrame for LV:': vat_per_country, # based on this we calculate sales for IOSS VAT to fill the box 1a
        'Return VAT per Country DataFrame for LV:': return_vat_per_country, # based on this we calculate negative IOSS VAT to fill the box 1a credit

        # OSS VAT form
        'VAT per Country DataFrame for HV:': hv_vat_per_country, # based on this we calculate import OSS VAT to pay

        # for NL row we get total VAT refund to put it into VAT form as box 1a credit
        # for non-NL rows we get VAT refund to put it into OSS VAT form as box 1a credit

        # for every country I need separate table with Country, Total Refund (Duty + VAT), DR Revenue from that refund ( 20% for every country but 30% for IE )
        'Combined Refunds DataFrame for HV:': combined_refunds
    }



if __name__ == "__main__":
    main()