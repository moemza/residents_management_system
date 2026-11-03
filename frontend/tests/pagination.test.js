import test from "node:test";
import assert from "node:assert/strict";

import { PAGE_SIZE, clampPage, formatPageRange } from "../src/api/pagination.js";

test("formatPageRange reports the visible slice", () => {
  assert.equal(formatPageRange(0, 20, 45), "Showing 1–20 of 45");
  assert.equal(formatPageRange(2, 20, 45), "Showing 41–45 of 45");
  assert.equal(formatPageRange(1, 20, 20), "Showing 1–20 of 20");
});

test("formatPageRange handles empty and invalid totals", () => {
  assert.equal(formatPageRange(0, 20, 0), "No results");
  assert.equal(formatPageRange(0, 20, -1), "No results");
  assert.equal(formatPageRange(0, 20, Number.NaN), "No results");
});

test("clampPage keeps a valid page unchanged", () => {
  assert.equal(clampPage(0, PAGE_SIZE, 45), 0);
  assert.equal(clampPage(2, PAGE_SIZE, 45), 2);
});

test("clampPage bounds pages to the available range", () => {
  assert.equal(clampPage(9, 20, 45), 2);
  assert.equal(clampPage(-4, 20, 45), 0);
  assert.equal(clampPage(9, 20, 0), 0);
});
