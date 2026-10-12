# BEA overview

The Bureau of Economic Analysis (BEA, U.S. Dept. of Commerce) produces the U.S. national accounts: GDP and everything that adds up to it. For MacroCorpus it's our U.S. source for **output (GDP)** and **inflation (PCE price index)**. It covers the U.S. only, at annual, quarterly, and monthly frequencies. Quarterly GDP goes back to 1947.

## What it measures

- **GDP**: total output, plus consumer spending, investment, government, exports and imports
- **Personal income and saving**
- **Prices**: the PCE price index, the Fed's preferred inflation measure
- **Industries**: value added by industry, and input-output tables
- **Regions**: GDP, income, and employment by state, county, and metro
- **International**: U.S. trade and money flows with each country, and foreign assets and liabilities
- **Multinational companies** and **fixed assets**

## The 12 API datasets

There's also a 13th, `APIDatasetMetaData`, which holds no data. Each dataset contains many tables; BEA has thousands of series in total.

| Dataset | Contents | Frequency | Use for us |
|---|---|---|---|
| NIPA | Headline national accounts | A/Q/M | High |
| Regional | States, counties, metros | A; Q for states (GDP 2005+, income 1948+) | High |
| NIUnderlyingDetail | Finer NIPA detail | A/Q/M | Medium |
| GDPbyIndustry | Industry value added | A 1997+, Q 2005+ | Medium |
| UnderlyingGDPbyIndustry | Finer industry detail | A 1997+ | Low |
| ITA | Balance of payments by country | A, Q (SA and NSA) | Medium |
| IIP | International investment position | A, Q (NSA) | Low |
| IntlServTrade | Services trade by country | A | Low |
| IntlServSTA | Services through foreign affiliates | A | Low |
| MNE | Multinational enterprises | A | Low |
| FixedAssets | Capital stock and depreciation | A | Low |
| InputOutput | Industry-to-industry purchases | A | Low |

Key NIPA tables:

- **T10101**: real GDP % change, quarterly
- **T10106**: real GDP in chained dollars
- **T20600**: personal income, monthly
- **T20804**: PCE prices, monthly

## What BEA doesn't have

| Variable | Source |
|---|---|
| CPI, unemployment | BLS |
| Interest rates, industrial production | Federal Reserve |
| Other countries | OECD, IMF, Eurostat, national statistics offices |

FRED re-hosts most BEA series.

## Why it's useful for MacroCorpus

- **Cross-country anchor.** U.S. GDP follows international national-accounts standards, so it can be lined up with other countries' GDP.
- **Regional comparison.** It gives 50 states under one method.
- **Frequency comparison.** The same concepts come at several frequencies.
- **Built-in test cases for the properties we study:**
  - *Seasonality:* ITA has SA and NSA versions of the same series.
  - *Breaks:* industry data has the SIC→NAICS break around 1997–2001.
  - *Missingness:* Alaska and Hawaii have no data before 1950.
  - *Short series:* quarterly state GDP is only about 80 quarters long.

## API essentials

- **Endpoint:** `https://apps.bea.gov/api/data`, with a free 36-character key. Results come back as JSON or XML.
- **Methods:**
  - `GetDataSetList`
  - `GetParameterList`
  - `GetParameterValues`
  - `GetParameterValuesFiltered`
  - `GetData`
- **Limits per minute:** 100 requests, 100 MB, 30 errors. Exceeding them returns HTTP 429 and a timeout of about 60 s.
- **Output fields:**
  - `TimePeriod`: `2024`, `2024Q3`, or `2024M7`
  - `DataValue`: has commas, which need stripping
  - `UNIT_MULT`: a power of 10
  - `CL_UNIT`: the unit
  - `NoteRef`: links to footnotes
- **Official Python package:** `beaapi`. This repo uses its own small client instead, for caching and control.

## Gotchas for forecasting

1. **Revisions.** Quarterly GDP goes through advance, second, and third estimates, then annual updates (September) and comprehensive updates (about every 5 years). The API returns only the latest values.
2. **Revision size.** The average absolute revision from the advance estimate to the latest is about 1.2–1.3 percentage points of annualized growth. Treat that as a noise floor for forecast errors.
3. **SAAR.** Quarterly NIPA values are seasonally adjusted annual rates.
4. **Base years.** Chained-dollar levels are re-based at comprehensive updates, so prefer growth rates.

## Sources

- [BEA data](https://www.bea.gov/data)
- [BEA API User Guide](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf)
- [API signup](https://apps.bea.gov/API/signup/)
- [beaapi](https://pypi.org/project/beaapi/)
- [GDP revisions](https://www.bea.gov/sites/default/files/2024-10/relia.pdf)
- [Release schedule](https://www.bea.gov/news/schedule)
