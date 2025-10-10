// Programs.jsx
import React, { useState } from "react";
import { Link } from "react-router-dom";

const programsList = [
  {
    name: "Drive-Thru Food Pantry",
    type: "Distribution",
    eligibility: "Open",
    frequency: "Weekly",
    cost: "Free",
    host: "Church",
    image: "/images/drive-thru.jpg",
    detailsPage: "drive-thru-food-pantry",
  },
  {
    name: "Culinary Training Program",
    type: "Class",
    eligibility: "High School GED",
    frequency: "Yearly",
    cost: "Free",
    host: "Food Bank",
    image: "/images/cooking-case.png",
    detailsPage: "culinary-training",
  },
  {
    name: "Nutrition Education Program",
    type: "Service",
    eligibility: "Referral-based",
    frequency: "Ongoing Sessions",
    cost: "Free",
    host: "Food Bank",
    image: "/images/nutrition-education.png",
    detailsPage: "nutrition-class",
  },
];

const Programs = () => {
  const [filter, setFilter] = useState("all");

  const filteredPrograms =
    filter === "all"
      ? programsList
      : programsList.filter((p) => p.type === filter);

  const handleFilterClick = (type) => {
    setFilter(type);
  };

  return (
    <div className="programs-page">
      {/* Navbar */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
        <div className="container">
          <Link className="navbar-brand" to="/">
            <img src="/favicon.svg" alt="Icon" height="50" width="50" /> FoodBankConnect
          </Link>
          <div className="collapse navbar-collapse">
            <ul className="navbar-nav ms-auto">
              <li className="nav-item">
                <Link className="nav-link" to="/about">About</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/foodbanks">Food Banks</Link>
              </li>
              <li className="nav-item">
                <span className="nav-link active">Programs</span>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/sponsors">Sponsors</Link>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      {/* Header */}
      <header className="py-5 text-center bg-white">
        <div className="container">
          <h1 className="display-5 fw-bold">Programs & Volunteer Opportunities</h1>
          <p className="lead text-muted">
            Explore how you can participate or benefit from local food programs.
          </p>
        </div>
      </header>

      {/* Filter Buttons */}
      <div className="container text-center mb-4">
        <div className="btn-group">
          {["all", "Distribution", "Volunteer", "Class", "Service"].map((type) => (
            <button
              key={type}
              className={`btn btn-outline-primary ${filter === type ? "active" : ""}`}
              onClick={() => handleFilterClick(type)}
            >
              {type === "all" ? "All" : type}
            </button>
          ))}
        </div>
      </div>

      {/* Program Cards */}
      <main className="container">
        <div className="mb-4 text-muted">
          Showing {filteredPrograms.length} Programs in Total
        </div>
        <div className="row g-4">
          {filteredPrograms.map((program, idx) => (
            <div key={idx} className="col-md-6 col-lg-3">
              <div className="card h-100 shadow-sm">
                <img
                  src={program.image}
                  className="card-img-top"
                  alt={program.name}
                />
                <div className="card-body">
                  <h5 className="card-title">{program.name}</h5>
                  <p><strong>Type:</strong> {program.type}</p>
                  <p><strong>Eligibility:</strong> {program.eligibility}</p>
                  <p><strong>Frequency:</strong> {program.frequency}</p>
                  <p><strong>Cost:</strong> {program.cost}</p>
                  <p><strong>Host:</strong> {program.host}</p>
                  <Link
                    to={`/${program.detailsPage}`}
                    className="btn btn-primary w-100"
                  >
                    See Details
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-4 mt-5 bg-primary text-white">
        &copy; 2025 FoodBankConnect
      </footer>
    </div>
  );
};

export default Programs;
