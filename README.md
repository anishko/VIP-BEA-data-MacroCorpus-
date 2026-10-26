# VIP – BEA data (MacroCorpus)

Our part of MacroCorpus: pulling data from the BEA (Bureau of Economic Analysis) and turning it into one standard JSON format. All the code is in `macrocorpus-bea/`.

## How to run it

1. Get a free BEA API key here: https://apps.bea.gov/API/signup/ (they email it to you)
2. Set it up:
   ```bash
   cd macrocorpus-bea
   pip install -e .
   cp .env.example .env
   ```
   then open `.env` and paste your key in.
3. Download:
   ```bash
   python -m bea_corpus download
   ```
   Takes a few minutes. You'll see an `ok` line for every table it pulls.

## What it does

- Uses the BEA API key to call BEA's official API. No web scraping, it's just requests that return JSON.
- Goes through all 12 BEA datasets (NIPA, Regional, ITA, IIP, MNE, etc.), grabs the list of tables in each one, and downloads a sample (a few hundred series per dataset) to make sure the code works on every dataset.
- Converts everything into the same JSON format: one series per line, with the info about the series (dataset, title, frequency, units) plus a list of dates and a list of values.

## Where stuff ends up

- `data/standardized/<Dataset>.jsonl` – the clean JSON (this is the main output)
- `data/raw/` – the original BEA responses, in case we need to re-convert
- `reports/download_summary.md` – how big each dataset is and how many series we got

`data/` isn't on GitHub since it's big, except for one sample: `macrocorpus-bea/data/standardized/NIPA.jsonl` (434 series), so you can see the format without running anything.

If we change the JSON format, run `python -m bea_corpus standardize`. It redoes the JSON from the saved raw files without downloading again.

## Important facts

- **The sample is ~120 MB. All of BEA would be roughly 3 GB** (estimated from the sample, see `reports/download_summary.md`). Regional would probably be even bigger than that estimate since it has every state/county/metro.
- Biggest datasets: NIPA (~1 GB), MNE (~660 MB), NIUnderlyingDetail and InputOutput (~400 MB each).
- BEA limits you to 100 requests a minute, so the code waits a little between calls. Re-runs are fast because responses are saved.
- The API only gives the latest revised numbers, not what was originally published.
- Your API key stays in `.env`, which doesn't get pushed to GitHub.
