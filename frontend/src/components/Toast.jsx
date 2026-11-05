import { useEffect } from "react";

export default function Toast({ message, type = "success", onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const isError = type !== "success";
  const background = isError ? "alert-danger" : "alert-success";

  return (
    <div
      className={`alert ${background} alert-dismissible position-fixed top-0 end-0 m-3`}
      style={{ zIndex: 9999, minWidth: 280, maxWidth: "calc(100vw - 2rem)" }}
      role={isError ? "alert" : "status"}
      aria-live={isError ? "assertive" : "polite"}
      aria-atomic="true"
    >
      {message}
      <button
        type="button"
        className="btn-close"
        aria-label="Close notification"
        onClick={onClose}
      />
    </div>
  );
}
