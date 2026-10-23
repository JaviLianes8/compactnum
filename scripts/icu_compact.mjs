// Format numbers with ICU's compact notation, as Node.js ships it, for the oracle tests.
// Reads a JSON list of [value, precision, display] from stdin, where value is a decimal
// string (formatted exactly), precision the maximum fraction digits and display "short"
// or "long". Writes {versions, results} as JSON to stdout.
let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const formatters = new Map();
  const results = JSON.parse(input).map(([value, precision, display]) => {
    const key = `${precision}/${display}`;
    if (!formatters.has(key)) {
      formatters.set(key, new Intl.NumberFormat("en", {
        notation: "compact",
        compactDisplay: display,
        maximumFractionDigits: precision,
        roundingMode: "halfExpand",
      }));
    }
    return formatters.get(key).format(value);
  });
  const versions = { node: process.versions.node, icu: process.versions.icu, cldr: process.versions.cldr };
  process.stdout.write(JSON.stringify({ versions, results }));
});
