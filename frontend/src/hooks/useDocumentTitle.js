import { useEffect } from "react";

const BASE_TITLE = "Residents Management System";

/**
 * Keep the browser tab title in sync with the current page.
 *
 * Route components call this hook directly, so no central route/title map has
 * to be maintained.
 */
export function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} — ${BASE_TITLE}` : BASE_TITLE;
  }, [title]);
}
