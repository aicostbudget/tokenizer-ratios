# How many characters is a token? Stop dividing by 4

[![code: MIT](https://img.shields.io/badge/code-MIT-blue)](LICENSE-CODE)
[![data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-blue)](LICENSE-DATA)

"One token is about four characters" is the rule everyone uses. We ran 951 text samples through OpenAI's
`o200k_base` tokenizer (GPT-4o, GPT-4.1 and newer; tiktoken 0.14.0) and counted. The rule is fine for code,
off by a quarter on plain English, and **misses half the tokens in JSON and CSV**. If you size context windows
or price API calls with it, the JSON-heavy calls are the ones that blow your budget.

The good news: you don't need a tokenizer to do much better. [`estimate-tokens.js`](estimate-tokens.js) is a
26-line function with no dependencies. Copy it into your project and it lands within about 2% of the real count
on English, docs, code, CSV, JSON and Chinese.

## Three estimators against the real count

Estimate divided by the real `o200k_base` count, summed per content type. 1.000 is exact; 0.50 means you
counted half the tokens you will pay for.

| Content | Samples | characters ÷ 4 | [tokenx](https://github.com/johannschopplich/tokenx) 2.2.0 | estimate-tokens.js |
|---|---:|---:|---:|---:|
| English blog writing | 416 | 1.250 | 1.048 | 1.016 |
| English technical docs | 354 | 1.097 | 1.031 | 1.012 |
| Python source | 53 | 1.047 | 1.027 | 0.999 |
| CSV | 40 | **0.524** | 1.000 | 1.003 |
| JSON | 20 | **0.527** | 0.903 | 0.998 |
| Chinese | 11 | **0.346** | 1.184 | 1.007 |
| API keys, UUIDs, hashes | 30 | **0.388** | **0.378** | 1.003 |
| English with emoji | 15 | 0.618 | **0.434** | 1.013 |
| Japanese | 4 | 0.352 | 1.096 | 0.992 |
| Korean | 4 | 0.449 | 1.092 | 1.061 |
| Russian | 4 | 0.980 | 0.922 | 1.010 |

Rerun it yourself with `npm install && npm run compare`
([scripts/compare_estimators.mjs](scripts/compare_estimators.mjs), results in
[results/estimator-comparison-o200k_base.json](results/estimator-comparison-o200k_base.json)).

How to read this fairly:

- tokenx is a good library. It is tiny and close on English and code. It undercounts random IDs and emoji by
  more than half and JSON by about 10%, so it is the wrong pick if your prompts carry API payloads or logs.
- The `estimate-tokens.js` column is in-sample: its weights were fitted on these same samples. Fitting on the
  even rows and scoring only the odd rows gives blog 1.008, docs 1.017, code 1.001, CSV 0.999, JSON 0.985,
  Chinese 1.015 and IDs 0.970. Japanese, Korean and Russian have four sentences each, and there the held-out
  error is 6% to 12%.
- All three are estimates. For billing, use the provider's own token count.

## Use it

```js
import { estimateTokens } from "./estimate-tokens.js";

estimateTokens('{"order_id": 48213, "total": 129.95, "currency": "USD"}'); // 22. The real o200k_base count is 22; characters ÷ 4 says 14.
```

It runs in Node, Deno, Bun and the browser. It needs Unicode property escapes in regular expressions, which every
current runtime has. The weights are in the first lines of the file; refit them for another tokenizer with
`python scripts/fit_estimator.py --encoding <name>`.

## Characters per token, by content type

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

(This table divides total characters by total tokens without rounding each sample, so the ÷ 4 column differs
from the comparison above in the second decimal.) Full numbers, including the per-sample range, are in
[results/chars-per-token-o200k_base.json](results/chars-per-token-o200k_base.json). The write-up with a cost
example is on the AICostBudget blog:
[How Many Characters Is a Token? We Measured 10 Kinds of Text](https://aicostbudget.com/en/blog/how-many-characters-is-a-token).

## Rules of thumb that hold up better than ÷ 4

- Plain English (emails, articles, chat): characters ÷ 5
- Technical English and source code: characters ÷ 4.2
- JSON, CSV, logs and anything number-heavy: characters ÷ 2
- API keys, hashes, base64, UUIDs: characters ÷ 1.5
- Chinese or Japanese: characters × 0.73
- How many tokens is 1,000 words? About 1,240 for everyday English prose, about 1,530 for technical writing

## How the estimator works

It counts a few things separately and weights them. `scripts/fit_estimator.py` fits the weights with
non-negative least squares, giving every category the same total weight:

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

The held-out check splits rows from the same sources, so it shows the fit is not overfitted to individual
samples, not that it works on every kind of text. The same weights run the free
[AICostBudget Token Calculator](https://aicostbudget.com/en/token-calculator), where you can paste text and see
the estimate and its API cost per model.

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
npm install && npm run compare                     # results/estimator-comparison-o200k_base.json
```

## Limits

- Only OpenAI tokenizers. Claude, Gemini, Llama, DeepSeek and others use their own, and the same text can
  come out at a different count. Use the provider's own token counting before you lock a budget.
- The CSV and JSON files are generated tables, not real exports. Real data with more text or more numbers
  will land somewhere in the per-sample range (CSV 1.6 to 3.9 characters per token).
- Chinese has 11 paragraphs; Japanese, Korean and Russian have four sentences each. Treat those rows as
  directional.
- The technical docs are Python docstrings, which have more code names than most product documentation.

If you run this on another tokenizer, add a content type or have a better estimator, a pull request with the results
file is welcome. If the data saved you a budget surprise, a star helps other people find it.

## Cite

GitHub shows a "Cite this repository" button from [CITATION.cff](CITATION.cff).

## License

Code (`scripts/` and `estimate-tokens.js`) is MIT. Data and results are CC BY 4.0, except the Python standard-library excerpts, which
stay under the PSF License. See [LICENSE-CODE](LICENSE-CODE) and [LICENSE-DATA](LICENSE-DATA).
