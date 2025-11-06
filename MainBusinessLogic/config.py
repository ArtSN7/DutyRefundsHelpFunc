class Config:
    """Configuration constants for VAT and duty calculations."""

    # ==================== VAT RATES ====================
    VAT_RATES = {
        'DE': 0.19, 'PT': 0.23, 'ES': 0.21, 'IE': 0.23,
        'SE': 0.25, 'NL': 0.21, 'DK': 0.25, 'FI': 0.255,
        'IT': 0.22, 'AT': 0.20, 'BE': 0.21, 'EE': 0.22
    }

    NL_VAT_RATE = 0.21
    
    # ==================== COMMISSION RATES ====================
    # Commission rate for DR revenue calculation
    DEFAULT_COMMISSION_RATE = 0.2  # 20% for most countries
    IE_COMMISSION_RATE = 0.3       # 30% for Ireland
    
    # Dictionary for easy lookup
    COMMISSION_RATES = {
        'IE': IE_COMMISSION_RATE
    }
    
    # PC (Pro Carrier) gets the remainder
    DEFAULT_PC_RATE = 0.8  # 80% for most countries (100% - 20%)
    IE_PC_RATE = 0.7       # 70% for Ireland (100% - 30%)
    
    # Duty revenue rates (what company gets from refunded duty)
    DUTY_REVENUE_RATE_DEFAULT = 0.8  # 80% for most countries
    DUTY_REVENUE_RATE_IE = 0.7        # 70% for Ireland
    
    # ==================== DUTY EXCLUSIONS ====================
    # Countries where duty cannot be reclaimed on returns
    DUTY_EXCLUDED_COUNTRIES = ['IE']  # Ireland does not allow duty returns
    
    # ==================== THRESHOLDS ====================
    CONSIGNMENT_THRESHOLD = 150  # EUR - Low value vs High value threshold

    # ==================== FILE PATHS ====================
    # Input files
    DEFAULT_CSV_PATH = "TED BAKER DUTY CLAIM BACK Jul-Sep v2.csv"
    DEFAULT_DUTY_EXCEL_PATH = "Duties Import Jan 99.xlsx"
    
    # Return period
    DEFAULT_RETURN_PERIOD = "Q3 2024"
    
    # Output directories
    DATA_DIR = "./data/"
    VAT_RETURNS_DIR = "./vat_returns/"

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
        return Config.IE_COMMISSION_RATE if country == 'IE' else Config.DEFAULT_COMMISSION_RATE
    
    @staticmethod
    def get_pc_rate(country: str) -> float:
        """Get PC (Pro Carrier) rate for VAT refunds by country."""
        return Config.IE_PC_RATE if country == 'IE' else Config.DEFAULT_PC_RATE
    
    @staticmethod
    def get_duty_revenue_rate(country: str) -> float:
        """Get duty revenue rate by country."""
        return Config.DUTY_REVENUE_RATE_IE if country == 'IE' else Config.DUTY_REVENUE_RATE_DEFAULT