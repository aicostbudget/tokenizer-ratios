// Estimate an OpenAI o200k_base token count (GPT-4o, GPT-4.1, o-series and newer) without a tokenizer.
// Weights fitted on the 951 samples in https://github.com/aicostbudget/tokenizer-ratios (MIT).
// Within about 2% on English prose, technical docs, code, CSV, JSON and Chinese; other tokenizers differ.
const W = { cjk: 0.73, otherLetter: 0.28, word: 0.91, longWordLetter: 0.22, shortWord: 0.33, capitalized: 0.62,
  camel: 1.41, digit: 0.66, punct: 0.56, symbol: 1.53, spaceRun: 1.24 };
const CJK = /[぀-ヿ㐀-鿿가-힯豈-﫿　-〿＀-￯]/gu;
const LATIN = /[A-Za-zÀ-ɏ]+/gu;
const count = (text, pattern) => (text.match(pattern) ?? []).length;

export function estimateTokens(text) {
  if (!text) return 0;
  const rest = text.replace(CJK, "");
  const words = rest.match(LATIN) ?? [];
  const estimate = count(text, CJK) * W.cjk
    + count(rest.replace(LATIN, ""), /\p{L}|\p{M}/gu) * W.otherLetter
    + words.length * W.word
    + words.reduce((sum, word) => sum + Math.max(0, word.length - 10), 0) * W.longWordLetter
    + words.filter((word) => word.length <= 3).length * W.shortWord
    + words.filter((word) => /^\p{Lu}/u.test(word)).length * W.capitalized
    + count(rest, /[a-z][A-Z]/g) * W.camel
    + count(rest, /\p{Nd}/gu) * W.digit
    + count(rest, /[!-/:-@[-`{-~]/g) * W.punct
    + count(rest, /[^\s\p{L}\p{M}\p{Nd}!-/:-@[-`{-~]/gu) * W.symbol
    + count(rest, /[ \t]{2,}/g) * W.spaceRun;
  return Math.max(1, Math.ceil(estimate));
}
