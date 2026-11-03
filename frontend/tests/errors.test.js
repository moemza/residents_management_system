import test from "node:test";
import assert from "node:assert/strict";

import { getApiErrorMessage } from "../src/api/errors.js";

test("string detail is returned unchanged", () => {
  const error = { response: { data: { detail: "Resident not found" } } };
  assert.equal(getApiErrorMessage(error, "fallback"), "Resident not found");
});

test("validation array detail is flattened into field messages", () => {
  const error = {
    response: {
      data: {
        detail: [
          { loc: ["body", "email"], msg: "value is not a valid email address" },
          { loc: ["body", "first_name"], msg: "Field required" },
        ],
      },
    },
  };
  assert.equal(
    getApiErrorMessage(error, "fallback"),
    "email: value is not a valid email address; first_name: Field required"
  );
});

test("unknown error shapes use the fallback", () => {
  assert.equal(getApiErrorMessage({}, "fallback"), "fallback");
  assert.equal(getApiErrorMessage(null, "fallback"), "fallback");
});

test("empty string detail uses the fallback", () => {
  const error = { response: { data: { detail: "   " } } };
  assert.equal(getApiErrorMessage(error, "fallback"), "fallback");
});
