# BEA coverage check

Run on 2026-11-01. For each dataset: the full dictionary, then every series in a sample of its tables. `Checked` says how we know a table is complete: either we compared it with the dictionary's list, or BEA returns the whole table in one call.

| Dataset | Status | Dictionary params listed | Tables in dataset | Sampled | Requests ok | Series | Observations | MB |
|---|---|---|---|---|---|---|---|---|
| NIPA | ok | 5/5 | 249 | 5 | 5/5 | 256 | 31861 | 8.2 |
| NIUnderlyingDetail | ok | 4/4 | 58 | 5 | 5/5 | 1482 | 488366 | 124.3 |
| FixedAssets | ok | 2/2 | 109 | 5 | 5/5 | 253 | 19361 | 4.8 |
| GDPbyIndustry | issues | 4/4 | 39 | 5 | 5/5 | 898 | 48372 | 8.6 |
| UnderlyingGDPbyIndustry | issues | 4/4 | 27 | 5 | 5/5 | 1175 | 33693 | 5.7 |
| InputOutput | ok | 2/2 | 10 | 2 | 2/2 | 5889 | 170315 | 41.7 |
| ITA | ok | 4/4 | 889 | 5 | 5/5 | 155 | 9503 | 3.6 |
| IIP | ok | 4/4 | 399 | 5 | 5/5 | 46 | 956 | 0.4 |
| IntlServTrade | ok | 5/5 | 117 | 5 | 5/5 | 847 | 15542 | 8.8 |
| IntlServSTA | ok | 5/5 | 8 | 5 | 5/5 | 110 | 1899 | 1.1 |
| MNE | ok | 12/12 | 58 | 5 | 5/5 | 862 | 17831 | 9.5 |
| Regional | ok | 4/4 | 105 | 3 | 107/107 | 5760 | 165720 | 28.1 |

**17733 series** downloaded in total.

## Sampled tables

| Dataset | Table | Series | Requests ok | Checked | Missing |
|---|---|---|---|---|---|
| NIPA | T10101 | 50 | 1/1 | whole table in one call | - |
| NIPA | T20304 | 62 | 1/1 | whole table in one call | - |
| NIPA | T31506 | 43 | 1/1 | whole table in one call | - |
| NIPA | T50906 | 76 | 1/1 | whole table in one call | - |
| NIPA | T80400 | 25 | 1/1 | whole table in one call | - |
| NIUnderlyingDetail | U001A | 128 | 1/1 | whole table in one call | - |
| NIUnderlyingDetail | U20404 | 1200 | 1/1 | whole table in one call | - |
| NIUnderlyingDetail | U50205 | 56 | 1/1 | whole table in one call | - |
| NIUnderlyingDetail | U50705BM2 | 20 | 1/1 | whole table in one call | - |
| NIUnderlyingDetail | U90100 | 78 | 1/1 | whole table in one call | - |
| FixedAssets | FAAt101 | 24 | 1/1 | whole table in one call | - |
| FixedAssets | FAAt303E | 96 | 1/1 | whole table in one call | - |
| FixedAssets | FAAt309S | 96 | 1/1 | whole table in one call | - |
| FixedAssets | FAAt603 | 13 | 1/1 | whole table in one call | - |
| FixedAssets | FAAt903 | 24 | 1/1 | whole table in one call | - |
| GDPbyIndustry | 1 | 199 | 1/1 | every Industry in the dictionary | 1 of 101 |
| GDPbyIndustry | 14 | 199 | 1/1 | every Industry in the dictionary | 1 of 101 |
| GDPbyIndustry | 23 | 199 | 1/1 | every Industry in the dictionary | 1 of 101 |
| GDPbyIndustry | 34 | 100 | 1/1 | every Industry in the dictionary | 3 of 103 |
| GDPbyIndustry | 209 | 201 | 1/1 | every Industry in the dictionary | 1 of 102 |
| UnderlyingGDPbyIndustry | 210 | 191 | 1/1 | every Industry in the dictionary | 1 of 192 |
| UnderlyingGDPbyIndustry | 216 | 191 | 1/1 | every Industry in the dictionary | 1 of 192 |
| UnderlyingGDPbyIndustry | 227 | 191 | 1/1 | every Industry in the dictionary | 1 of 192 |
| UnderlyingGDPbyIndustry | 236 | 190 | 1/1 | every Industry in the dictionary | 1 of 191 |
| UnderlyingGDPbyIndustry | 242 | 412 | 1/1 | every Industry in the dictionary | 3 of 415 |
| InputOutput | 59 | 5402 | 1/1 | whole table in one call | - |
| InputOutput | 258 | 487 | 1/1 | whole table in one call | - |
| ITA | BalCapAcct | 73 | 1/1 | every AreaOrCountry in the dictionary | 0 of 36 |
| ITA | DiInvReinvestEarnWithoutCurrCostAdjLiabsWhlslTrd | 3 | 1/1 | every AreaOrCountry in the dictionary | 0 of 1 |
| ITA | ExpServConstAbroad | 3 | 1/1 | every AreaOrCountry in the dictionary | 0 of 1 |
| ITA | LoansAssets | 73 | 1/1 | every AreaOrCountry in the dictionary | 0 of 36 |
| ITA | TSI_ItaDiInvWithoutCurrCostAdjIncOutward | 3 | 1/1 | every AreaOrCountry in the dictionary | 0 of 1 |
| IIP | CurrAndDepAssets | 21 | 1/1 | whole table in one call | - |
| IIP | DebtAssetsExclReserveOthFinUsdLt | 1 | 1/1 | whole table in one call | - |
| IIP | DebtLiabsOthFinFc | 1 | 1/1 | whole table in one call | - |
| IIP | DiInvInwardCurrCost | 2 | 1/1 | whole table in one call | - |
| IIP | TreasBondsAndNotesLiabs | 21 | 1/1 | whole table in one call | - |
| IntlServTrade | AccountAuditBookkeep | 188 | 1/1 | every AreaOrCountry in the dictionary | 0 of 90 |
| IntlServTrade | Comp | 188 | 1/1 | every AreaOrCountry in the dictionary | 0 of 90 |
| IntlServTrade | InsPremiumsPaidDirIns | 95 | 1/1 | every AreaOrCountry in the dictionary | 0 of 90 |
| IntlServTrade | RDSaleRights | 188 | 1/1 | every AreaOrCountry in the dictionary | 0 of 90 |
| IntlServTrade | WasteTreatAndDePolAgAndMining | 188 | 1/1 | every AreaOrCountry in the dictionary | 0 of 90 |
| IntlServSTA | AllChannels | 2 | 1/1 | whole table in one call | - |
| IntlServSTA | Mousas | 104 | 1/1 | whole table in one call | - |
| IntlServSTA | SalesMousas | 1 | 1/1 | whole table in one call | - |
| IntlServSTA | Trade | 2 | 1/1 | whole table in one call | - |
| IntlServSTA | UsImportsFromMofas | 1 | 1/1 | whole table in one call | - |
| MNE | 30 | 236 | 1/1 | whole table in one call | - |
| MNE | 31 | 236 | 1/1 | whole table in one call | - |
| MNE | 27 | 236 | 1/1 | whole table in one call | - |
| MNE | 25 | 77 | 1/1 | whole table in one call | - |
| MNE | 33 | 77 | 1/1 | whole table in one call | - |
| Regional | CAGDP1 | 180 | 3/3 | every line in the dictionary | 0 of 3 |
| Regional | SAGDP9 | 5520 | 92/92 | every line in the dictionary | 0 of 92 |
| Regional | TASUMMARY2 | 60 | 12/12 | every line in the dictionary | 0 of 12 |

## Issues

- **warning** GDPbyIndustry / 1: 1 of 101 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO).
- **warning** GDPbyIndustry / 14: 1 of 101 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO).
- **warning** GDPbyIndustry / 23: 1 of 101 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO).
- **warning** GDPbyIndustry / 34: 3 of 103 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO, Percent change: (A,Q), Percentage points: (A,Q)).
- **warning** GDPbyIndustry / 209: 1 of 102 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO).
- **warning** UnderlyingGDPbyIndustry / 210: 1 of 192 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO).
- **warning** UnderlyingGDPbyIndustry / 216: 1 of 192 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO).
- **warning** UnderlyingGDPbyIndustry / 227: 1 of 192 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO).
- **warning** UnderlyingGDPbyIndustry / 236: 1 of 191 Industry values in the dictionary have no data, even when asked for on their own (e.g. 622HO).
- **warning** UnderlyingGDPbyIndustry / 242: 3 of 415 Industry values in the dictionary have no data, even when asked for on their own (e.g. 517110, 517210, 622HO).
- **info** IIP / CurrAndDepAssets: 3 of 21 series have no values at all (every value suppressed or not available).
- **info** IIP / TreasBondsAndNotesLiabs: 3 of 21 series have no values at all (every value suppressed or not available).
- **info** MNE / 31: 1 of 236 series have no values at all (every value suppressed or not available).
- **info** MNE / 27: 2 of 236 series have no values at all (every value suppressed or not available).
- **info** MNE / 25: 1 of 77 series have no values at all (every value suppressed or not available).
- **info** MNE / 33: 1 of 77 series have no values at all (every value suppressed or not available).
