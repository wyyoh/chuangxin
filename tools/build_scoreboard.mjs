#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

function parseArgs(argv) {
  const args = { csv: [], out: null };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--csv") {
      args.csv.push(argv[++i]);
    } else if (arg === "--out") {
      args.out = argv[++i];
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  if (!args.csv.length) throw new Error("at least one --csv is required");
  if (!args.out) throw new Error("--out is required");
  return args;
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (quoted) {
      if (ch === '"' && next === '"') {
        cell += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        cell += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(cell);
      cell = "";
    } else if (ch === "\n") {
      row.push(cell.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += ch;
    }
  }
  if (cell.length || row.length) {
    row.push(cell.replace(/\r$/, ""));
    rows.push(row);
  }
  const header = rows.shift() ?? [];
  return rows.filter((r) => r.length && r.some((v) => v !== "")).map((r) => {
    const obj = {};
    header.forEach((h, idx) => {
      obj[h] = r[idx] ?? "";
    });
    return obj;
  });
}

function numberOrBlank(value) {
  if (value === undefined || value === null || value === "") return "";
  const num = Number(value);
  return Number.isFinite(num) ? num : value;
}

function sheetNameFromCsv(csvArg) {
  const [name, file] = csvArg.includes("=") ? csvArg.split(/=(.*)/s) : ["", csvArg];
  const raw = name || path.basename(file, path.extname(file)).replace(/_metrics$/i, "");
  return raw.replace(/[\\/*[\]:?]/g, "_").slice(0, 31) || "metrics";
}

function csvPath(csvArg) {
  return csvArg.includes("=") ? csvArg.split(/=(.*)/s)[1] : csvArg;
}

async function addTableSheet(workbook, sheetName, rows) {
  const sheet = workbook.worksheets.add(sheetName);
  const columns = [
    "case",
    "requested_pipeline",
    "selected_pipeline",
    "status",
    "fallback_reason",
    "selected_nodes",
    "selected_levels",
    "original_nodes",
    "original_levels",
    "opt_runtime_sec",
    "cec_runtime_sec",
    "peak_mem_mb",
    "output_path",
  ];
  const values = [
    columns,
    ...rows.map((row) => columns.map((col) => numberOrBlank(row[col]))),
  ];
  sheet.getRange(`A1:M${values.length}`).values = values;
  sheet.getRange(`A1:E${values.length}`).format.columnWidthPx = 150;
  sheet.getRange(`F1:L${values.length}`).format.columnWidthPx = 112;
  sheet.getRange(`M1:M${values.length}`).format.columnWidthPx = 360;
  return { sheet, columns, values };
}

function summarize(name, rows) {
  const selectedNodes = rows.map((r) => Number(r.selected_nodes)).filter(Number.isFinite);
  const selectedLevels = rows.map((r) => Number(r.selected_levels)).filter(Number.isFinite);
  const originalNodes = rows.map((r) => Number(r.original_nodes)).filter(Number.isFinite);
  const cecFailures = rows.filter((r) => String(r.cec_pass).toLowerCase() !== "true").length;
  const fallbacks = rows.filter((r) => String(r.status).startsWith("fallback")).length;
  const totalNodes = selectedNodes.reduce((a, b) => a + b, 0);
  const totalOriginal = originalNodes.reduce((a, b) => a + b, 0);
  const maxLevel = selectedLevels.length ? Math.max(...selectedLevels) : "";
  const totalRuntime = rows.reduce((sum, r) => sum + (Number(r.opt_runtime_sec) || 0) + (Number(r.cec_runtime_sec) || 0), 0);
  const maxMem = Math.max(0, ...rows.map((r) => Number(r.peak_mem_mb)).filter(Number.isFinite));
  return [
    name,
    rows.length,
    totalNodes,
    totalOriginal,
    totalOriginal ? totalOriginal - totalNodes : "",
    maxLevel,
    fallbacks,
    cecFailures,
    totalRuntime,
    maxMem,
  ];
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const workbook = Workbook.create();
  const summaryRows = [];

  for (const csvArg of args.csv) {
    const file = csvPath(csvArg);
    const name = sheetNameFromCsv(csvArg);
    const text = await fs.readFile(file, "utf8");
    const rows = parseCsv(text);
    await addTableSheet(workbook, name, rows);
    summaryRows.push(summarize(name, rows));
  }

  const summary = workbook.worksheets.add("Summary");
  const summaryValues = [
    [
      "dataset",
      "cases",
      "selected_nodes_sum",
      "original_nodes_sum",
      "node_delta_vs_original",
      "max_selected_level",
      "fallback_count",
      "cec_failure_count",
      "runtime_sec_sum",
      "peak_mem_mb_max",
    ],
    ...summaryRows,
  ];
  summary.getRange(`A1:J${summaryValues.length}`).values = summaryValues;
  summary.getRange(`A1:A${summaryValues.length}`).format.columnWidthPx = 120;
  summary.getRange(`B1:H${summaryValues.length}`).format.columnWidthPx = 150;
  summary.getRange(`I1:J${summaryValues.length}`).format.columnWidthPx = 150;

  const outputPath = path.resolve(args.out);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
  console.log(outputPath);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
