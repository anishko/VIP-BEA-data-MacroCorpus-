# BEA coverage check

Run on 2026-11-09. For each dataset: the full dictionary, then every series in a sample of its tables. `Checked` says how we know a table is complete: either we compared it with the dictionary's list, or BEA returns the whole table in one call.

| Dataset | Status | Dictionary params listed | Tables in dataset | Sampled | Requests ok | Series | Observations | MB |
|---|---|---|---|---|---|---|---|---|
| MNE | issues | 12/12 | 57 | 5 | 3/17 | 707 | 9582 | 5.3 |

**707 series** downloaded in total.

## Sampled tables

| Dataset | Table | Series | Requests ok | Checked | Missing |
|---|---|---|---|---|---|
| MNE | 16 | 0 | 0/7 | whole table in one call | - |
| MNE | 22 | 235 | 1/1 | whole table in one call | - |
| MNE | 53 | 234 | 1/1 | whole table in one call | - |
| MNE | 51 | 0 | 0/7 | whole table in one call | - |
| MNE | 6 | 238 | 1/1 | whole table in one call | - |

## Issues

- **error** MNE / 16: No data with any of the request shapes tried (DirectionOfInvestment=outward, Classification=Country; DirectionOfInvestment=inward, Classification=Country; DirectionOfInvestment=inward, Classification=CountryofUBObyType; DirectionOfInvestment=outward, Classification=Country, OwnershipLevel=0, NonbankAffiliatesOnly=0; DirectionOfInvestment=inward, Classification=Country, OwnershipLevel=0, NonbankAffiliatesOnly=0; DirectionOfInvestment=parent, Classification=Industry, OwnershipLevel=1, NonbankAffiliatesOnly=0; DirectionOfInvestment=state, Classification=StatebyCountryofUBO, OwnershipLevel=0, NonbankAffiliatesOnly=0).
- **error** MNE / 51: No data with any of the request shapes tried (DirectionOfInvestment=outward, Classification=Country; DirectionOfInvestment=inward, Classification=Country; DirectionOfInvestment=inward, Classification=CountryofUBObyType; DirectionOfInvestment=outward, Classification=Country, OwnershipLevel=0, NonbankAffiliatesOnly=0; DirectionOfInvestment=inward, Classification=Country, OwnershipLevel=0, NonbankAffiliatesOnly=0; DirectionOfInvestment=parent, Classification=Industry, OwnershipLevel=1, NonbankAffiliatesOnly=0; DirectionOfInvestment=state, Classification=StatebyCountryofUBO, OwnershipLevel=0, NonbankAffiliatesOnly=0).
- **info** MNE / 22: 1 of 235 series have no values at all (every value suppressed or not available).
- **info** MNE / 53: 10 of 234 series have no values at all (every value suppressed or not available).
- **info** MNE / 6: 13 of 238 series have no values at all (every value suppressed or not available).
