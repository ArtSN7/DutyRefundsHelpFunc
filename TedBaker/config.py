"""Configuration constants for VAT and duty calculations."""


class Config:
    """Configuration constants for VAT and duty calculations."""

    VAT_RATES = {
        'DE': 0.19, 'PT': 0.23, 'ES': 0.21, 'IE': 0.23,
        'SE': 0.25, 'NL': 0.21, 'DK': 0.25, 'FI': 0.255,
        'IT': 0.22, 'AT': 0.20, 'BE': 0.21, 'EE': 0.22
    }

    NL_VAT_RATE = 0.21
    DEFAULT_COMMISSION_RATE = 0.2
    IE_COMMISSION_RATE = 0.3
    CONSIGNMENT_THRESHOLD = 150

    # Output directory for CSV reports
    OUTPUT_DIR = "./reports/"

    low_value_columns = ['MRN', 'Line Item Quantity Imported', 'Line Item Quantity Returned', 'Line Item Unit Price',
                         'Consignment Value', 'VAT Rate', 'Consignee Country']

    high_value_columns = ['MRN', 'HS CODE', 'Line Item Quantity Imported', 'Line Item Quantity Returned',
                          'Line Item Unit Price', 'Consignment Value', 'VAT Rate', 'Consignee Country']

