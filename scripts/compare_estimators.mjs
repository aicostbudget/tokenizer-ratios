// Compare three ways to guess a token count against the real o200k_base count, per content type:
// characters ÷ 4, tokenx (https://github.com/johannschopplich/tokenx) and estimate-tokens.js from this repo.
// Prints estimate ÷ real (1.000 = exact) and writes results/estimator-comparison-o200k_base.json.
// Usage: npm install && npm run compare
import { readFileSync, writeFileSync } from "node:fs";
import { getEncoding } from "js-tiktoken";
import { estimateTokenCount } from "tokenx";
import { estimateTokens } from "../estimate-tokens.js";

const root = new URL("../", import.meta.url);
const encoding = getEncoding("o200k_base");
const samples = readFileSync(new URL("data/samples.jsonl", root), "utf8").trim().split("\n").map((line) => JSON.parse(line));

const methods = {
  "chars/4": (text) => Math.ceil(text.length / 4),
  tokenx: (text) => estimateTokenCount(text),
  "estimate-tokens.js": (text) => estimateTokens(text),
};

const totals = {};
for (const sample of samples) {
  const row = (totals[sample.category] ??= { samples: 0, tokens: 0, ...Object.fromEntries(Object.keys(methods).map((name) => [name, 0])) });
  row.samples += 1;
  row.tokens += encoding.encode(sample.text).length;
  for (const [name, estimate] of Object.entries(methods)) row[name] += estimate(sample.text);
}

const ratios = Object.fromEntries(Object.entries(totals).map(([category, row]) => [category, {
  samples: row.samples,
  tokens: row.tokens,
  ...Object.fromEntries(Object.keys(methods).map((name) => [name, Number((row[name] / row.tokens).toFixed(3))])),
}]));

console.log(["category", "samples", ...Object.keys(methods)].join("\t"));
for (const [category, row] of Object.entries(ratios)) console.log([category, row.samples, ...Object.keys(methods).map((name) => row[name].toFixed(3))].join("\t"));

const version = (name) => JSON.parse(readFileSync(new URL(`node_modules/${name}/package.json`, root), "utf8")).version;
const versions = { "js-tiktoken": version("js-tiktoken"), tokenx: version("tokenx") };
writeFileSync(new URL("results/estimator-comparison-o200k_base.json", root),
  JSON.stringify({ encoding: "o200k_base", versions, estimateOverActual: ratios }, null, 2) + "\n");
