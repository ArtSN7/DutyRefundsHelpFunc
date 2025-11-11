from data_layer import DataLayer
from duty_processor import DutyProcessor
from config import Config
import pandas as pd
import warnings
from pathlib import Path
from lv_processes import LowValueProcessor
from hv_processes import HighValueProcessor

warnings.filterwarnings("ignore")


def generate_summary_table(data: dict):
    # Calculate VAT RETURN components
    ioss_sales, ioss_vat_to_return = data["IMPORT_IOSS"], data["RETURN_IOSS"]
    net_ioss = ioss_sales - ioss_vat_to_return
    lv_dr_fee = data["LV DR FEE"]

    # BROKER TRANSACTIONS IN NL
    value_broker_paid_during_import = data["VAT_PAID_DURING_IMPORT_TO_NL"]
    value_to_return_from_nl_for_import = data["VAT_TO_RETURN_FROM_NL_FOR_IMPORT"]

    # HV OSS VAT components
    hv_oss_import_vat = data["OSS_HV_VAT_DF"]["Total VAT to Pay"].sum()
    hv_oss_return_vat = data["OSS_HV_VAT_DF"]["Total VAT Refund"].sum()
    net_oss = hv_oss_import_vat - hv_oss_return_vat

    # HV VAT RETURNS
    nl_vat_returns = data["NL_REFUNDS"]["Total VAT Refund"].sum()
    nl_duty_returns = data["NL_REFUNDS"]["Total Duty Returned"].sum()
    ie_vat_returns = data["IE_REFUNDS"]["Total VAT Refund"].sum()

    # DUTY REFUNDS COMMISSION
    dr_fee = (
            ((nl_duty_returns + nl_vat_returns) * 0.2) + (ie_vat_returns * 0.3) + lv_dr_fee
    )

    # Pro Carrier PAYS YOU:
    # 1. Net IOSS VAT (you pay on their behalf)
    # 2. Net OSS VAT (you pay on their behalf)
    # 3. Your commission
    invoice_amount = net_ioss + net_oss + dr_fee  # Net IOSS  # Net OSS  # Commission

    # DR PAY BACK to Pro Carrier:
    # We also need to return reclaimed from broker's payment VAT for HV NL returns
    pc_return_amount = (
            nl_duty_returns
            + ie_vat_returns
            + nl_vat_returns
            + value_to_return_from_nl_for_import
    )

    rows = [
        ("TOTAL IOSS VAT", ioss_sales, "Total IOSS VAT for sales"),
        ("RETURNED IOSS VAT", ioss_vat_to_return, "IOSS VAT for returns"),
        ("NET IOSS VAT", net_ioss, "Net IOSS position"),
        (" ", " ", " "),
        (
            "AMOUNT BROKER PAID",
            value_broker_paid_during_import,
            "VAT paid by broker during import in NL for HV",
        ),
        (
            "AMOUNT THAT CAN BE CLAIMED BACK",
            value_to_return_from_nl_for_import,
            "Amount to reclaim from NL (HV) for values that didn't stay in NL",
        ),
        (" ", " ", " "),
        (
            "OSS import VAT paid",
            hv_oss_import_vat,
            "Total import VAT paid for HV consignments",
        ),
        (
            "OSS return VAT",
            hv_oss_return_vat,
            "Total VAT to return for HV consignments (non-NL)",
        ),
        ("NET OSS VAT", net_oss, "Net OSS VAT to pay"),
        (" ", " ", " "),
        (
            "Total VAT Refund From HV",
            ie_vat_returns + nl_vat_returns,
            "Total VAT refunded for returned HV parcels ",
        ),
        ("Total Duty Returned", nl_duty_returns, "Total refunded duty"),
        (
            "Total Refunds",
            nl_duty_returns + ie_vat_returns + nl_vat_returns,
            "Total VAT + Duty refunds",
        ),
        (" ", " ", " "),
        ("Duty Refunds Commission", dr_fee, "DR revenue from refunds"),
        (" ", " ", " "),
        (
            "Amount to invoice Pro Carrier:",
            invoice_amount,
            "Net IOSS + Net OSS + Commission",
        ),
        (
            "Amount to be paid to Pro Carrier:",
            pc_return_amount,
            "Refunds from customs + reclaimed broker's money",
        ),
    ]

    summary_df = pd.DataFrame(rows, columns=["Section", "Amount", "Description"])

    data_dir = Path(Config.DATA_DIR)
    data_dir.mkdir(exist_ok=True)
    summary_df.to_excel(data_dir / "INFORMATION.xlsx", index=False, engine="openpyxl")


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
    if data_type not in ["csv", "xlsx"]:
        raise ValueError(f"Invalid data_type: {data_type}. Must be 'csv' or 'xlsx'")

    output_dir = f"../{output_folder}/"

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    Config.DATA_DIR = output_dir

    # ==================== PROCESS DUTY DATA ====================
    duty_data = pd.read_excel(Config.DEFAULT_DUTY_EXCEL_PATH)
    duty_dict = DutyProcessor.process_duty_data(duty_data)

    # ==================== LOAD CONSIGNMENT DATA ====================
    if data_type == "csv":
        low_value_df, high_value_df = DataLayer.load_data(file_name)
    elif data_type == "xlsx":
        low_value_df, high_value_df = DataLayer.load_excel(file_name)

    # ==================== WORK WITH LV DATA ====================
    dr_lv_fee, import_ioss, returned_ioss = LowValueProcessor.process_low_value_data(
        low_value_df
    )

    # ==================== WORK WITH HV DATA ====================
    nl_values, ie_values = HighValueProcessor.process_high_value_data(
        high_value_df, duty_dict
    )

    (
        vat_that_was_paid_by_broker_in_nl,
        vat_to_return_from_nl,
        hv_vat_per_country,
        nl_combined_refunds,
    ) = nl_values
    ie_combined_refunds = ie_values[0]

    # ==================== WORK WITH FORM DATA ====================

    form = {
        # stats only
        "VAT_PAID_DURING_IMPORT_TO_NL": vat_that_was_paid_by_broker_in_nl,
        # VAT form
        "VAT_TO_RETURN_FROM_NL_FOR_IMPORT": vat_to_return_from_nl,
        "IMPORT_IOSS": import_ioss,
        "RETURN_IOSS": returned_ioss,
        "LV DR FEE": dr_lv_fee,
        # OSS VAT form
        "OSS_HV_VAT_DF": hv_vat_per_country,
        # Combined refunds
        "IE_REFUNDS": ie_combined_refunds,
        "NL_REFUNDS": nl_combined_refunds,
    }

    generate_summary_table(form)

    print(f"✅ DONE! Results saved to: {output_dir}")


def main():
    """Default execution with hardcoded values."""
    process_data(
        file_name="../OCT DATA.xlsx",
        data_type="xlsx",
        output_folder="./OCT_RESULTS",
    )


if __name__ == "__main__":
    main()
