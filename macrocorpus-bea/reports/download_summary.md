# BEA sample download: how heavy is each dataset?

Run on 2026-10-25. One GetData call per table; numbers are for the sample only.
`Est. full size` = average KB per call x number of tables in the dataset (rough; Regional is
much bigger in reality because every table also has many lines and geographies).

| Dataset | Tables in catalog | Calls OK / tried | Series | Rows | Raw MB | Avg s/call | Est. full size (MB) |
|---|---|---|---|---|---|---|---|
| NIPA | 249 | 5 / 5 | 434 | 81060 | 20.56 | 0.00 | 1024 |
| NIUnderlyingDetail | 58 | 3 / 3 | 384 | 90816 | 21.42 | 0.00 | 414 |
| FixedAssets | 109 | 5 / 5 | 343 | 32891 | 8.27 | 0.00 | 180 |
| GDPbyIndustry | 39 | 2 / 2 | 595 | 22898 | 4.03 | 0.00 | 79 |
| UnderlyingGDPbyIndustry | 27 | 2 / 2 | 382 | 11078 | 1.87 | 0.00 | 25 |
| InputOutput | 10 | 1 / 1 | 5402 | 156658 | 38.49 | 0.00 | 385 |
| ITA | 889 | 15 / 15 | 39 | 3546 | 1.31 | 0.00 | 78 |
| IIP | 399 | 15 / 15 | 76 | 1739 | 0.71 | 0.00 | 19 |
| IntlServTrade | 117 | 15 / 15 | 146 | 3886 | 1.63 | 0.00 | 13 |
| IntlServSTA | 8 | 2 / 2 | 1010 | 16769 | 7.86 | 0.00 | 31 |
| MNE | 58 | 1 / 1 | 1247 | 25582 | 11.42 | 0.00 | 662 |
| Regional | 105 | 9 / 9 | 354 | 13574 | 2.21 | 0.00 | 26 |
| **Total** | | | **10412** | **460497** | **119.79** | | **2936** |
