# 📊 ФИНАЛЬНОЕ РУКОВОДСТВО: IOSS & OSS
## С правильной VAT формулой: VAT = (Parcel + Duty) × Rate
### Q3 2025, все товары в одном квартале

---

# 🎯 ОСНОВНЫЕ ПРИНЦИПЫ

## Правило #1: Формула VAT - ПРАВИЛЬНАЯ

```
VAT = (Parcel Price + Duty) × VAT Rate

Duty ВКЛЮЧАЕТСЯ в базу для VAT!
```

### ПРИМЕРЫ:

**HV-NL-100 (NL import, €400 parcel):**
```
Parcel: €400
Duty (3.7%): €400 × 3.7% = €14.80
VAT base: €400 + €14.80 = €414.80

Import VAT (21%): €414.80 × 21% = €87.11
Import Duty: €14.80

Atlantic платит: €87.11 VAT + €14.80 Duty = €101.91
```

**HV-IE-200 (IE import, €500 parcel):**
```
Parcel: €500
Duty (3.7%): €500 × 3.7% = €18.50
VAT base: €500 + €18.50 = €518.50

Import VAT (23%): €518.50 × 23% = €119.26
Import Duty: €18.50

Irish broker платит: €119.26 VAT + €18.50 Duty = €137.76
```

---

## Правило #2: IOSS - БЕЗ разделения!

```
IOSS ≤€150:
├─ Импорт: ВСЕГДА 0% VAT
├─ Pro Carrier: Собирает VAT у покупателя
├─ Вы: Передаете VAT в налоговую
└─ БЕЗ разделения на типы!
```

---

## Правило #3: IE товары - ТОЛЬКО в Ireland!

```
ВСЕ MRN 25IE... остаются в Ireland:
├─ Доставляются: В Ireland
├─ Продаются: В Ireland
└─ Это: DOMESTIC (никогда не cross-border)

Нет:
├─ ❌ IE→Germany
├─ ❌ IE→France
└─ ❌ IE→Other EU

ТОЛЬКО:
└─ ✅ IE→Ireland
```

---

# 📦 ЧАСТЬ 1: LOW VALUE (≤€150) - IOSS

## Процесс простой и ОДИНАКОВЫЙ!

### Шаг 1: Импорт под IOSS

```
Товар ≤€150 с IOSS номером:
├─ Таможня: VAT = 0%
├─ Брокер платит: €0 
└─ Товар: Входит БЕЗ VAT
```

### Шаг 2: Pro Carrier собирает VAT

```
Pro Carrier продает:
├─ Parcel €100
├─ VAT (25%): +€25
└─ Покупатель платит: €125

Pro Carrier собирает VAT по ставке страны доставки!
```

### Шаг 3: Вы группируете по странам

```
Germany (19%):
├─ Посылка 1: €100 × 19% = €19
├─ Посылка 2: €80 × 19% = €15.20
└─ ИТОГО: €34.20

Ireland (23%):
├─ Посылка 1: €120 × 23% = €27.60
└─ ИТОГО: €27.60

Возвраты (отнимаем):
├─ Germany -€60 × 19% = -€11.40
└─ Ireland -€100 × 23% = -€23
```

### Шаг 4: Dutch VAT Return (Monthly)

**Form fields:**

**Box 1a: IOSS Sales**
```
Germany (19%):
├─ Description: "IOSS distance sales to Germany"
├─ Taxable Amount: €180 (€100+€80)
├─ VAT Rate: 19%
└─ VAT Amount: €34.20

Ireland (23%):
├─ Description: "IOSS distance sales to Ireland"
├─ Taxable Amount: €120
├─ VAT Rate: 23%
└─ VAT Amount: €27.60

[Все страны]
```

**Box 1c: Returns**
```
Germany (negative):
├─ Description: "IOSS returns from Germany"
├─ VAT Amount: -€11.40

Ireland (negative):
├─ Description: "IOSS returns from Ireland"
├─ VAT Amount: -€23
```

**Box 5: €0** (IOSS не имеет input VAT) - смотреть шаг по Broker's import VAT payment

---

### Шаг 5: Комиссия от IOSS returns

```
Ireland returns: 30% commission
Other returns: 20% commission

Пример:
Germany returns (€11.40) × 20% = €2.28
Ireland returns (€23) × 30% = €6.90
```

---

# 📦 ЧАСТЬ 2: HIGH VALUE (>€150)

## Группы товаров

### Группа A-NL: NL Cross-Border Sales

**Определение:**
- Import: NL (MRN 25NL...)
- Customer: Other EU country
- Status: Delivered

**Пример:**
```
NL→Germany €400
NL→France €300
```

**Что происходит:**
```
Import в NL:
├─ VAT base: €400 + €14.80 = €414.80
├─ VAT: €414.80 × 21% = €87.11
└─ Duty: €14.80
  Total: €101.91

Sale в Germany:
├─ VAT: €400 × 19% = €76 - учитываем только vat без duty
├─ Reason: Distance sale, German customer
└─ Method: OSS payment
```

**Действия:**
- ✅ Box 5b: Reclaim €87.11 (NL import VAT) - там где IOSS заполняется
- ✅ OSS: Pay €76 (Germany sales tax)
- ✅ Commission: €87.11 - €76 = €11.11 profit

---

### Группа B-NL: NL Domestic

**Определение:**
- Import: NL (MRN 25NL...)
- Customer: NL
- Status: Delivered

**Пример:**
```
NL→NL €200
NL→NL €450
```

**Что происходит:**
```
Import в NL:
├─ VAT base: €200 + €7.40 = €207.40
├─ VAT: €207.40 × 21% = €43.55
└─ Total: €43.55 + €7.40 = €50.95

Sale в NL:
├─ VAT: 21% (ставка NL)
├─ Customer: NL
└─ Result: VAT уже правильный!
```

**Действия:**
- ❌ Box 5b: NO (VAT already correct 21%)
- ❌ OSS: NO (domestic, not distance sale)
- ✓ NOTHING! VAT финален и уже заплачен брокером

---

### Группа B-IE: IE Domestic

**Определение:**
- Import: IE (MRN 25IE...)
- Customer: IE
- Status: Delivered

**ВАЖНО: ЕДИНСТВЕННЫЙ ВАРИАНТ ДЛЯ IE!**

```
IE товары ТОЛЬКО идут в Ireland:
├─ IE→Ireland ВСЕГДА
├─ IE→Germany: НЕ СУЩЕСТВУЕТ
```

**Пример:**
```
IE→Ireland €300
IE→Ireland €600
```

**Что происходит:**
```
Import в IE:
├─ VAT base: €300 + €11.10 = €311.10
├─ VAT: €311.10 × 23% = €71.55
└─ Total: €71.55 + €11.10 = €82.65

Sale в Ireland:
├─ VAT: 23% (ставка Ireland)
├─ Customer: Ireland
└─ Result: VAT уже правильный!
```

**Действия:**
- ❌ Box 5b: NO (not NL import!)
- ❌ OSS: NO (domestic, not distance sale)
- ✓ NOTHING! VAT финален и уже заплачен брокером

---

### Группа C-NL-X: NL Cross-Border Return

**Определение:**
- Import: NL (MRN 25NL...)
- Original: Was cross-border (A-NL)
- Status: Returned

**Пример:**
```
NL→Germany €400 (returned)
NL→France €300 (returned)
```

**Что происходит:**
```
При возврате сделка отменяется:
├─ Было: Box 5b + OSS платежи
├─ Теперь: Возвращаем оба
└─ Плюс: RGR для import charges
```

**Действия:**
- ❌ Box 5b: NO (already used when sold)
- ✅ OSS: Correction -€76 (Germany)
- ✅ NL RGR: Reclaim €87.11 VAT + €14.80 Duty ( по тому что было заплачено при импорте в NL )

---

### Группа C-NL-D: NL Domestic Return

**Определение:**
- Import: NL (MRN 25NL...)
- Original: Was domestic (B-NL)
- Status: Returned

**Пример:**
```
NL→NL €200 (returned)
```

**Действия:**
- ❌ Box 5b: NO (wasn't used)
- ❌ OSS: NO (wasn't in OSS)
- ✅ NL RGR: Reclaim €43.55 VAT + €7.40 Duty

---

### Группа C-IE-D: IE Domestic Return

**Определение:**
- Import: IE (MRN 25IE...)
- Original: Was domestic (B-IE)
- Status: Returned

**Пример:**
```
IE→Ireland €300 (returned)
```

**Действия:**
- ❌ Box 5b: NO (never was there)
- ❌ OSS: NO (wasn't in OSS)
- ✅ IE RGR: Reclaim €71.55 VAT ONLY
- ❌ Duty: €11.10 - CANNOT reclaim in Ireland!
- ⚠️ Pro Carrier loss: €11.10 (duty)

---

## Box 5b: ТОЛЬКО Group A-NL!

### Что включаем:

```
ТОЛЬКО посылки:
├─ MRN: 25NL... (MUST!)
├─ Import location: Netherlands
├─ Customer: Other EU
├─ Status: Delivered (not returned)
└─ VAT amount: (Parcel + Duty) × 21%

Пример расчета:
├─ HV-NL-100: €400 → base €414.80 → VAT €87.11
├─ HV-NL-101: €300 → base €314.20 → VAT €65.98
└─ TOTAL Box 5b: €153.09
```

### Как заполнить Box 5b:

```
Description: "Import VAT for distance sales from Netherlands"

Taxable Amount: €700 (sum of A-NL parcels)
VAT Rate: 21%
VAT Amount: €153.09
```

### Что ИСКЛЮЧАЕМ:

```
❌ Group A-IE (IE imports, not NL!)
❌ Group B-NL (domestic, VAT correct)
❌ Group B-IE (IE imports, not NL)
❌ All returns (handle via RGR)
```

---

## OSS VAT Return: Quarterly

### Что включаем:

```
ТОЛЬКО Group A-NL (cross-border sales)

По странам:
├─ Germany: €400 → €76 (19%)
├─ France: €300 → €60 (20%)
└─ [Other EU countries...]

МИНУС returns:
├─ Germany returns: -€2,000 → -€380
└─ [Net per country...]
```

### ВАЖНО: IE НИКОГДА в OSS!

```
Почему:
├─ IE товары = ТОЛЬКО IE→Ireland
├─ IE→Ireland = Domestic
└─ Domestic ≠ Distance sale
└─ Distance sale = OSS only

Результат:
└─ Zero IE entries in OSS!
```

### Как заполнить:

```
MEMBER STATE: DE (Germany)
VAT Rate: 19%

SALES:
├─ Description: "Distance sales to Germany"
├─ Taxable Amount: €400
├─ VAT Amount: €76

RETURNS:
├─ Description: "Returns from Germany"
├─ Taxable Amount: -€2,000
├─ VAT Amount: -€380

NET:
├─ Taxable: €398,000 (example)
└─ VAT: €75,620
```

Repeat для каждой страны!

---

## RGR Forms: Per Return

### NL RGR (Groups C-NL-X, C-NL-D)


```
VAT PAID: €87.11
├─ Formula: (€400 + €14.80) × 21%
├─ Rate: 21% Netherlands
├─ Taxable base: Parcel + Duty included
└─ What to claim: Full €87.11

DUTY PAID: €14.80
├─ Formula: €400 × 3.7%
├─ Rate: 3.7%
└─ What to claim: Full €14.80

TOTAL CLAIM: €101.91 (both!)
```

**Your commission:**
```
Commission: (€87.11 + €14.80) × 20% = €20.38
Return to Pro Carrier: €101.91 - €20.38 = €81.53
```

---

### IE RGR (Group C-IE-D)

```
VAT PAID: €119.26 ✓
├─ Formula: (€500 + €18.50) × 23%
├─ Rate: 23% Ireland
├─ Taxable base: Parcel + Duty included
└─ What to claim: Full €119.26

DUTY PAID: €18.50 ✗
├─ Amount: €18.50
├─ Status: CANNOT RECLAIM in Ireland
├─ Ireland policy: No duty refunds
└─ What to claim: €0

TOTAL CLAIM: €119.26 (VAT only!)
```

**Your commission:**
```
Commission: €119.26 × 30% = €35.78
Return to Pro Carrier: €119.26 - €35.78 = €83.48
Pro Carrier loss (duty): -€18.50
```

**Important:** Submitted under DR company (NL company):
```
Your details on form:
├─ Company: Your NL company name
├─ VAT number: Your NL number
├─ EORI: Your NL EORI
└─ Country: Ireland (where import was)
```

---

# 📋 ИТОГОВАЯ ТАБЛИЦА

```
Category | Import | Dest  | Box 5b | OSS  | RGR  | VAT Formula          | Commission
---------|--------|-------|--------|------|------|----------------------|------------
A-NL     | NL     | EU≠NL | ✅     | ✅   | -    | (P+D)×21%            | N/A
B-NL     | NL     | NL    | ❌     | ❌   | -    | N/A                  | N/A
B-IE     | IE     | IE    | ❌     | ❌   | -    | N/A                  | N/A
C-NL-X   | NL     | EU≠NL | ❌     | ✅-  | ✅   | (P+D)×21%            | 20%(V+D)
C-NL-D   | NL     | NL    | ❌     | ❌   | ✅   | (P+D)×21%            | 20%(V+D)
C-IE-D   | IE     | IE    | ❌     | ❌   | ✅   | (P+D)×23%            | 30%(V)
IOSS     | Any    | Any   | -      | -    | -    | Collected by PC       | Per return
```

Legend:
- ✅ = Include
- ❌ = Exclude/Not applicable
- ✅- = Include as negative (correction)
- P = Parcel price
- D = Duty
- V = VAT
- PC = Pro Carrier
- (V+D) = Commission from VAT + Duty combined
- (V) = Commission from VAT only

---

# 🎯 КЛЮЧЕВЫЕ ФОРМУЛЫ

## Commission:

```
IOSS returns:
├─ Ireland: VAT × 30%
└─ Other: VAT × 20%

HV NL returns:
├─ (VAT + Duty) × 20%
└─ Example: (€87.11 + €14.80) × 20% = €20.38

HV IE returns:
├─ VAT × 30% (Duty excluded!)
└─ Example: €119.26 × 30% = €35.78
```

---


---

---

## По каждому возврату:

```
IF C-NL-X or C-NL-D:
├─ [ ] Prepare NL RGR
├─ [ ] VAT: (Parcel + Duty) × 21%
├─ [ ] Duty: Parcel × 3.7%
├─ [ ] Commission: (VAT+Duty) × 20%
└─ [ ] If C-NL-X: Also OSS correction

IF C-IE-D:
├─ [ ] Prepare IE RGR
├─ [ ] VAT: (Parcel + Duty) × 23%
├─ [ ] Duty: €0 (cannot reclaim!)
├─ [ ] Commission: VAT × 30%
└─ [ ] NO OSS correction
```

---
