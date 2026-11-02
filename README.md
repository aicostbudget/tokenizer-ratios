# Tokenizer ratios: how many characters is a token?

[![code: MIT](https://img.shields.io/badge/code-MIT-blue)](LICENSE-CODE)
[![data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-blue)](LICENSE-DATA)

Everyone says one token is about four characters. We wanted to know how far off that is, so we ran 951 text
samples through OpenAI's `o200k_base` tokenizer (tiktoken 0.14.0) and counted.

Short version: it depends a lot on what the text is. Plain English fits about 5 characters in a token, so
dividing by 4 overcounts it. JSON and CSV fit about 2, so the same rule misses roughly half their tokens.
Chinese and Japanese come out at about 1.4.

| Content | Samples | Characters per token | Characters ÷ 4 gives you | Words per token |
|---|---:|---:|---:|---:|
| English blog writing | 416 | 4.98 | 1.24× the real count | 0.81 |
| English technical docs | 354 | 4.38 | 1.09× | 0.66 |
| Python source | 53 | 4.19 | 1.05× | |
| Russian | 4 | 3.88 | 0.97× | |
| JSON | 20 | 2.11 | 0.53× | |
| CSV | 40 | 2.10 | 0.52× | |
| English with emoji | 15 | 2.08 | 0.52× | 0.30 |
| Korean | 4 | 1.77 | 0.44× | |
| API keys, UUIDs, hashes | 30 | 1.55 | 0.39× | |
| Chinese | 11 | 1.37 | 0.34× | |
| Japanese | 4 | 1.34 | 0.34× | |

Full numbers, including the per-sample range, are in
[results/chars-per-token-o200k_base.json](results/chars-per-token-o200k_base.json). The write-up with a cost
example is on the AICostBudget blog:
[How Many Characters Is a Token? We Measured 10 Kinds of Text](https://aicostbudget.com/en/blog/how-many-characters-is-a-token).

## Rules of thumb that hold up better than ÷ 4

- Plain English (emails, articles, chat): characters ÷ 5
- Technical English and source code: characters ÷ 4.2
- JSON, CSV, logs and anything number-heavy: characters ÷ 2
- API keys, hashes, base64, UUIDs: characters ÷ 1.5
- Chinese or Japanese: characters × 0.73
- 1,000 English words: about 1,240 tokens for everyday prose, about 1,530 for technical writing

## Estimating without a tokenizer

If you need a number in the browser or anywhere you can't load a tokenizer, count a few things separately
and weight them. `scripts/fit_estimator.py` fits the weights with non-negative least squares, giving every
category the same total weight:

```
tokens ≈ 0.91 × Latin words
       + 0.33 × words of 1-3 letters
       + 0.62 × words starting with a capital
       + 1.41 × camelCase boundaries
       + 0.22 × letters past the 10th in one word
       + 0.66 × digits
       + 0.56 × ASCII punctuation
       + 1.53 × emoji and other symbols
       + 1.24 × runs of 2+ spaces or tabs
       + 0.73 × CJK characters
       + 0.28 × other non-Latin letters (Cyrillic, Greek...)
```

Estimate divided by the real count, after rounding each sample up:

| blog | docs | code | CSV | JSON | Chinese | IDs | emoji | Japanese | Korean | Russian |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.016 | 1.012 | 0.999 | 1.003 | 0.998 | 1.007 | 1.003 | 1.013 | 0.992 | 1.061 | 1.010 |

These are in-sample. Fitting on even rows and scoring odd rows gives similar numbers for the big categories
(see [results/estimator-weights-o200k_base.json](results/estimator-weights-o200k_base.json)), but the odd
rows come from the same sources, so this says the fit is not overfitted to individual samples, not that it
works on every kind of text. The same weights run the free
[AICostBudget Token Calculator](https://aicostbudget.com/en/token-calculator).

## What's in the data

`data/samples.jsonl` has one sample per line: `id`, `category`, `source` and `text`. Token counts are not
stored; the scripts recount them, so you can rerun everything with another tiktoken encoding.

| source | categories | where it came from |
|---|---|---|
| aicostbudget-blog | blog | paragraphs over 200 characters from AICostBudget blog posts, without price placeholders |
| python-stdlib-docstring | docs | docstrings longer than 400 characters from 19 CPython 3.11 modules, first 2,500 characters |
| python-stdlib-source | code | 2,500-character slices of CPython 3.11 standard-library files |
| synthetic | csv, json, emoji | generated order and metrics tables, short emoji messages |
| random | ids | base64, hex, UUIDs and `sk-` strings made from random bytes. They are not API keys. |
| hand-written | zh, ja, ko, ru | paragraphs and sentences about AI costs and billing, written for this test |

## Reproduce

```
git clone https://github.com/aicostbudget/tokenizer-ratios
cd tokenizer-ratios
pip install -r requirements.txt
python scripts/measure.py                          # results/chars-per-token-o200k_base.json
python scripts/fit_estimator.py                    # results/estimator-weights-o200k_base.json
python scripts/measure.py --encoding cl100k_base   # same samples, the older GPT-4 tokenizer
```

## Limits

- Only OpenAI tokenizers. Claude, Gemini, Llama, DeepSeek and others use their own, and the same text can
  come out at a different count. Use the provider's own token counting before you lock a budget.
- The CSV and JSON files are generated tables, not real exports. Real data with more text or more numbers
  will land somewhere in the per-sample range (CSV 1.6 to 3.9 characters per token).
- Chinese has 11 paragraphs; Japanese, Korean and Russian have four sentences each. Treat those rows as
  directional.
- The technical docs are Python docstrings, which have more code names than most product documentation.

If you run this on another tokenizer or add a content type, a pull request with the results file is welcome.

## License

Code (`scripts/`) is MIT. Data and results are CC BY 4.0, except the Python standard-library excerpts, which
stay under the PSF License. See [LICENSE-CODE](LICENSE-CODE) and [LICENSE-DATA](LICENSE-DATA).
