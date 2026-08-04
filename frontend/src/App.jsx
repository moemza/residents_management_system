import { Routes, Route, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Home from "./pages/Home";
import AddResident from "./pages/AddResident";
import EditResident from "./pages/EditResident";
import ViewResident from "./pages/ViewResident";
import SearchResident from "./pages/SearchResident";
import Toast from "./components/Toast";
import { useToast } from "./hooks/useToast";

export default function App() {
  const location = useLocation();
  const { toast, showToast, clearToast } = useToast();

  useEffect(() => {
    if (location.state?.success) {
      showToast(location.state.success, "success");
      window.history.replaceState({}, "");
    }
  }, [location, showToast]);

  return (
    <>
      {toast && <Toast message={toast.message} type={toast.type} onClose={clearToast} />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/add-resident" element={<AddResident />} />
        <Route path="/edit-resident/:id" element={<EditResident />} />
        <Route path="/view-resident/:id" element={<ViewResident />} />
        <Route path="/search" element={<SearchResident />} />
      </Routes>
    </>
  );
}
