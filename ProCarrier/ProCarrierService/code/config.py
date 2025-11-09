class Config:
    """Configuration constants for VAT and duty calculations."""

    # ==================== VAT RATES ====================
    DATA_DIR = './'

    VAT_RATES = {
        'DE': 0.19, 'PT': 0.23, 'ES': 0.21, 'IE': 0.23,
        'SE': 0.25, 'NL': 0.21, 'DK': 0.25, 'FI': 0.255,
        'IT': 0.22, 'AT': 0.20, 'BE': 0.21, 'EE': 0.22
    }
    
    # ==================== COMMISSION RATES ====================

    # Dictionary for easy lookup
    COMMISSION_RATES = {
        'DE': 0.2, 'PT': 0.2, 'ES': 0.2, 'IE': 0.3,
        'SE': 0.2, 'NL': 0.2, 'DK': 0.2, 'FI': 0.2,
        'IT': 0.2, 'AT': 0.2, 'BE': 0.2, 'EE': 0.2
    }


    
    # ==================== DUTY EXCLUSIONS ====================
    # Countries where duty cannot be reclaimed on returns
    DUTY_EXCLUDED_COUNTRIES = ['IE']  # Ireland does not allow duty returns
    
    # ==================== THRESHOLDS ====================
    CONSIGNMENT_THRESHOLD = 150  # EUR - Low value vs High value threshold

    # ==================== FILE PATHS ====================
    # Input files
    DEFAULT_DUTY_EXCEL_PATH = "Duties Import Jan 99.xlsx"
    
    # Return period
    DEFAULT_RETURN_PERIOD = "Q3 2024"


    # ==================== COLUMN DEFINITIONS ====================
    low_value_columns = [
        'MRN', 'Line Item Quantity Imported', 'Line Item Quantity Returned',
        'Line Item Unit Price', 'Consignment Value', 'VAT Rate', 'Consignee Country'
    ]

    high_value_columns = [
        'MRN', 'HS CODE', 'Line Item Quantity Imported', 'Line Item Quantity Returned',
        'Line Item Unit Price', 'Consignment Value', 'VAT Rate', 'Consignee Country'
    ]
    
    # ==================== HELPER METHODS ====================
    @staticmethod
    def get_commission_rate(country: str) -> float:
        """Get commission rate for VAT refunds by country."""
        return Config.COMMISSION_RATES[country]
    
    @staticmethod
    def get_pc_rate(country: str) -> float:
        """Get PC (Pro Carrier) rate for VAT refunds by country."""
        return 1 - Config.COMMISSION_RATES[country]
    
    @staticmethod
    def get_duty_revenue_rate(country: str) -> float:
        """Get duty revenue rate by country."""
        return Config.COMMISSION_RATES[country]