/**
 * Shared pagination helpers. Kept framework-free so they can be unit tested
 * with Node's built-in test runner.
 */

export const PAGE_SIZE = 20;

export function formatPageRange(page, pageSize, total) {
  if (!Number.isFinite(total) || total <= 0) return "No results";
  const size = Number.isFinite(pageSize) && pageSize > 0 ? pageSize : 1;
  const lastPage = Math.max(0, Math.ceil(total / size) - 1);
  const safePage = Math.min(Math.max(0, page), lastPage);
  const start = safePage * size + 1;
  const end = Math.min((safePage + 1) * size, total);
  return `Showing ${start}–${end} of ${total}`;
}

export function clampPage(page, pageSize, total) {
  if (!Number.isFinite(total) || total <= 0) return 0;
  const size = Number.isFinite(pageSize) && pageSize > 0 ? pageSize : 1;
  const lastPage = Math.max(0, Math.ceil(total / size) - 1);
  return Math.min(Math.max(0, page), lastPage);
}
