import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Residents Management System</h1>
      <div className="d-flex flex-column align-items-center gap-3">
        <Link to="/add-resident" className="btn btn-primary btn-lg">Add Resident</Link>
        <Link to="/search?type=name" className="btn btn-secondary btn-lg">Search by Name</Link>
        <Link to="/search?type=village" className="btn btn-secondary btn-lg">Search by Village</Link>
        <Link to="/search?type=qualification" className="btn btn-success btn-lg">Search by Qualification</Link>
        <Link to="/search?type=skill" className="btn btn-info btn-lg">Search by Skill</Link>
      </div>
      <p className="text-center mt-4">Manage your community's residents, villages, and qualifications with ease.</p>
    </div>
  );
}
