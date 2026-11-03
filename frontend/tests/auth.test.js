import test from "node:test";
import assert from "node:assert/strict";

import { clearCsrfToken, getCsrfToken, setCsrfToken } from "../src/auth.js";

test("CSRF token exists only in memory and can be cleared", () => {
  clearCsrfToken();
  assert.equal(getCsrfToken(), "");

  setCsrfToken("synthetic-csrf-token");
  assert.equal(getCsrfToken(), "synthetic-csrf-token");

  clearCsrfToken();
  assert.equal(getCsrfToken(), "");
});
