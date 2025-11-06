# VAT Analysis Tool with Automated Return Forms

Complete VAT analysis tool for e-commerce with automated generation of Dutch VAT Return, OSS Return, and Duty Return forms.

## 📁 Project Structure

```
vat_analysis/
├── config.py                  # Configuration & VAT rates
├── data_layer.py             # Data loading & cleaning
├── duty_processor.py         # Duty calculations
├── low_value_processor.py    # IOSS processing (≤€150)
├── high_value_processor.py   # OSS processing (>€150)
├── services.py               # Shared services
├── vat_return_forms.py       # ✨ NEW: VAT forms generator
├── main.py                   # Main entry point
└── README.md                 # This file
```

## 🎯 What It Does

### Analysis:
1. **Low Value (IOSS)**: Processes parcels ≤€150
2. **High Value (OSS)**: Processes parcels >€150
3. **Duty Calculations**: Calculates import duties and refunds
4. **Returns Processing**: Handles customer returns and credits

### Forms Generated:
1. **DUTCH_VAT_RETURN_Q3_2024.xlsx**
   - IOSS sales and returns
   - NL high value parcels
   - Import VAT reclaim (with minus sign effect)
   - Box numbers (Box 1, Box 5, etc.)

2. **OSS_VAT_RETURN_Q3_2024.xlsx**
   - Sales to other EU countries
   - Returns as credits
   - Net VAT per country

3. **DUTY_RETURN_CLAIM_Q3_2024.xlsx**
   - Separate customs claim
   - Duty refunds by country
   - **⚠️ Ireland (IE) excluded** - duty cannot be reclaimed

4. **DR_REVENUE_DETAILED_Q3_2024.xlsx** ✨ NEW
   - OSS VAT payment due
   - Dutch VAT net position (to claim from broker)
   - Duty revenue to Pro Carrier (80% general, **IE excluded**)

5. **PC_DUTY_REVENUE_Q3_2024.xlsx** ⭐⭐ **NEW**
   - Pro Carrier revenue breakdown
   - Low value and high value parcels
   - Duty revenue (80% general, 70% Ireland)
   - **⚠️ Ireland (IE) excluded** - duty cannot be reclaimed

6. **COMPREHENSIVE_FINANCIAL_BREAKDOWN_Q3_2024.xlsx** ⭐⭐⭐ **NEW**
   - Complete financial overview with all key metrics
   - IOSS VAT to Pay for Imports
   - IOSS VAT for Returns (Credit)
   - Net IOSS VAT
   - Broker Import VAT Paid (21% on HV parcels)
   - VAT to Reclaim from Broker (parcels to other EU)
   - NL HV Returns VAT (parcels stayed in NL)
   - OSS VAT to Pay (other EU countries)
   - OSS VAT Returned (returns from other EU)
   - Net OSS VAT
   - Total Duty Returned (all countries, IE excluded)
   - Total VAT Returned (IOSS + NL + OSS)
   - DR Fee (commission on VAT returns)
   - PC Portion from VAT Returns
   - PC Duty Revenue (100%)
   - PC Total Revenue
   - Summary of total refunds to process (VAT + Duty), DR revenue (commission), and PC revenue (remainder + duty)

## 📋 Input Data Fields

Your CSV must have these columns:
- Parcel ID
- CARRIER
- Line Item ID
- SKU
- COO (Country of Origin)
- HS CODE
- Line Item Name
- Line Item Quantity Imported
- Line Item Quantity Returned
- Line Item Unit Price
- Line Item Currency
- MRN (Movement Reference Number)
- Entry Date
- Declarant EORI
- Consignee Name
- Consignee Address
- Consignee City
- Consignee Postcode
- Consignee Country
- Courier Name
- Courier Tracking #
- EU Export Date
- Export MRN

## 🚀 Installation

```bash
# Install required packages
pip install pandas openpyxl
```

## 💻 Usage

```python
# Just run main.py
python main.py
```

## 📂 Output Files

### Analysis Reports (data/ folder):
- lv_consignments_data.xlsx
- lv_vat_per_country_summary.xlsx
- lv_returned_vat_per_country_summary.xlsx
- hv_consignments_data.xlsx
- hv_vat_per_country_summary.xlsx
- hv_vat_difference_summary.xlsx
- hv_returned_vat_per_country_summary.xlsx
- hv_duty_and_vat_returned_values_summary.xlsx

### VAT Return Forms (vat_returns/ folder):
- DUTCH_VAT_RETURN_Q3_2024.xlsx
- OSS_VAT_RETURN_Q3_2024.xlsx
- DUTY_RETURN_CLAIM_Q3_2024.xlsx
- DR_REVENUE_DETAILED_Q3_2024.xlsx ⭐ **NEW**
- PC_DUTY_REVENUE_Q3_2024.xlsx ⭐⭐ **NEW**
- COMPREHENSIVE_FINANCIAL_BREAKDOWN_Q3_2024.xlsx ⭐⭐⭐ **NEW**
- FINANCIAL_SUMMARY.xlsx ⭐

## 🔧 Configuration

All configuration is centralized in `config.py`:

### VAT Rates
- Configurable per country
- NL VAT rate: 21%

### Commission Rates
- Default: 20% (most countries)
- Ireland (IE): 30%

### Duty Revenue Rates
- Default: 80% (company gets 80% of refunded duty)
- Ireland (IE): 70% (company gets 70% of refunded duty)

### File Paths
- Input CSV path
- Duty Excel path
- Return period
- Output directories

### Thresholds
- Consignment threshold: €150 (IOSS vs OSS)

## 📊 Enhanced Revenue Tables

### DR Revenue Table (DR_REVENUE_DETAILED)
Shows what Duty Refunds gets from VAT returns (commission):
- **By Country Breakdown**:
  - LV VAT Refund: VAT refunds from low value returns
  - LV DR Revenue: Company revenue from LV refunds (20%/30% commission)
  - HV VAT Refund: VAT refunds from high value returns
  - HV Duty Refund: Duty refunds from high value returns (IE excluded)
  - HV DR Revenue: Company revenue from HV refunds (20%/30% commission)
  - Total VAT Refund: Combined LV + HV VAT refunds
  - Total DR Revenue: Combined LV + HV revenue (commission only)
  - Commission Rate: Applied rate (20% or 30%)
  - Notes: Special notes (e.g., "No duty reclaim" for IE)

### PC Duty Revenue Table (PC_DUTY_REVENUE) ⭐⭐ NEW
Shows what Pro Carrier gets from duty refunds (100%):
- **By Country Breakdown**:
  - HV Duty Refund: Duty refunds from high value returns (IE excluded)
  - PC Revenue from Duty: Pro Carrier gets 100% of duty refunds
  - Rate: 100% (full duty refund goes to PC)
  - Notes: Special notes (e.g., "No duty reclaim" for IE)

### Comprehensive Financial Breakdown ⭐⭐⭐ NEW
Complete financial overview with all key metrics:

**IOSS Section (Low Value ≤€150)**:
1. IOSS VAT to Pay for Imports
2. IOSS VAT for Returns (Credit)
3. Net IOSS VAT

**Broker Import VAT Section**:
4. Broker Import VAT Paid (21% on HV parcels)
5. VAT to Reclaim from Broker (parcels to other EU)
6. NL HV Returns VAT (parcels stayed in NL)

**OSS Section (High Value >€150)**:
7. OSS VAT to Pay (other EU countries)
8. OSS VAT Returned (returns from other EU)
9. Net OSS VAT

**Duty Section**:
10. Total Duty Returned (all countries, IE excluded)

**Revenue Split**:
11. Total VAT Returned (IOSS + NL + OSS)
12. DR Fee (commission on VAT returns)
13. PC Portion from VAT Returns
14. PC Duty Revenue (100%)
15. PC Total Revenue

**Summary**:
- Total Refunds to Process (VAT + Duty)
- DR Revenue (commission)
- PC Revenue (remainder + duty)

**Important Notes**:
- **VAT Refunds**: Go to customers, with DR taking 20-30% commission
- **Duty Refunds**: Go 100% to Pro Carrier (no commission)
- **IE Exclusion**: No duty can be reclaimed from Ireland

**Revenue Split**:
- DR gets: 20-30% commission on VAT refunds
- PC gets: 100% of duty refunds
- Customers get: 70-80% of VAT refunds (remainder after DR commission)

## 📊 Dutch VAT Return Breakdown

### Box 1 (Output VAT):
- IOSS sales (all countries)
- NL high value sales
- Minus returns

### Box 5 (Input VAT - DEDUCTION):
- Import VAT reclaim (parcels to other EU)
- **This creates MINUS effect** → Refund

### Net Result:
- If negative = **REFUND DUE**
- Automatic bank transfer (2-3 months)

## ✅ Key Features

- ✨ **Automated VAT forms** ready to file
- 📝 **Box numbers** for Dutch returns
- 🔄 **Returns handled** as negative amounts
- 💰 **Duty separate** from VAT
- 🎯 **OSS excludes NL** (as required)
- ⚡ **Import VAT reclaim** with minus sign

## 📖 How Forms Work

### Dutch VAT Return:
```
Output VAT (Box 1):
  + IOSS net
  + NL high value net
  = Total output VAT

Input VAT (Box 5):
  + Import VAT reclaim (MINUS EFFECT)
  = Total input VAT

NET = Output - Input
(Negative = Refund due to you)
```

### OSS Return:
```
Per country:
  Sales VAT
  - Returns VAT
  = Net VAT per country

Total OSS payment = Sum of all net amounts
```

### Duty Return:
```
Separate claim to Dutch Customs:
  - Duty by country
  - 90-day deadline
  - Export proof required
```

## ⚠️ Important Notes

1. **Import VAT reclaim** = Input VAT = MINUS sign effect
2. **OSS excludes NL** (NL goes in Dutch VAT Return)
3. **Duty is separate** from VAT returns
4. **Returns** = Negative amounts in forms
5. **Ireland (IE) duty exclusion**: Duty cannot be reclaimed from Ireland, so:
   - IE returns only include VAT refunds (30% commission)
   - No duty refunds for IE parcels
   - IE excluded from duty return claim form
6. **Three separate submissions**:
   - Dutch VAT Return (monthly/quarterly)
   - OSS Return (quarterly only)
   - Duty Return (to customs, not tax office)

## 🆘 Support

For questions about:
- **VAT regulations**: Contact Belastingdienst
- **Code issues**: Check the comments in each file
- **Forms**: Use the generated Excel files as templates

## 📝 License

Internal use only.

---

**Last Updated**: November 2025
**Version**: 2.0 (with automated forms)
