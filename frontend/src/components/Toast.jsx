import { useEffect } from "react";

export default function Toast({ message, type = "success", onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);

  const bg = type === "success" ? "alert-success" : "alert-danger";

  return (
    <div
      className={`alert ${bg} alert-dismissible position-fixed top-0 end-0 m-3`}
      style={{ zIndex: 9999, minWidth: 280 }}
      role="alert"
    >
      {message}
      <button type="button" className="btn-close" onClick={onClose} />
    </div>
  );
}
