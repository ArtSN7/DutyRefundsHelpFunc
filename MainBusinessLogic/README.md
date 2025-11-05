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

## 🔧 Configuration

Edit `config.py` to customize:
- VAT rates by country
- Commission rates
- Consignment threshold (default: €150)

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
5. **Three separate submissions**:
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
