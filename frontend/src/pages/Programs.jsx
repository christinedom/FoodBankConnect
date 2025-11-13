import "../styles/Programs.css";
import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import Header from "../components/Header";
import Footer from "../components/Footer";
import ProgramCard from "../components/ProgramsCard";

const BASE_URL = "https://dp3d297dp9.execute-api.us-east-2.amazonaws.com/v1/programs";
const ITEMS_PER_PAGE = 20;

const Programs = () => {
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  // Filters
  const [filters, setFilters] = useState({
    frequency: "",
    eligibility: "",
    cost: "",
    program_type: "",
    host: "", // new host filter
  });


  const [applyFilters, setApplyFilters] = useState(0);
  const [nextStart, setNextStart] = useState(null);
  const [prevStack, setPrevStack] = useState([]);
  const [allHosts, setAllHosts] = useState([]); // store unique hosts


  // Fetch programs from backend
  const fetchPrograms = async (startCursor = null) => {
    try {
      setLoading(true);


      const params = new URLSearchParams({
        size: ITEMS_PER_PAGE,
        ...(startCursor && { start: startCursor }),
        ...(filters.frequency && { frequency: filters.frequency }),
        ...(filters.eligibility && { eligibility: filters.eligibility }),
        ...(filters.cost && { cost: filters.cost }),
        ...(filters.program_type && { program_type: filters.program_type }),
        ...(filters.host && { host: filters.host }),
      });


      const fullURL = `${BASE_URL}?${params.toString()}`;
      console.log("Fetching URL:", fullURL);


      const response = await fetch(fullURL);
      if (!response.ok) throw new Error(`Failed to fetch programs: ${response.status}`);
      const data = await response.json();


      setPrograms(data.items || []);
      setNextStart(data.next_start || null);


      // extract unique hosts for dropdown if not already done
      if (allHosts.length === 0 && data.items) {
        const hosts = Array.from(new Set(data.items.map((p) => p.host))).sort();
        setAllHosts(hosts);
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
      setPrograms([]);
      setNextStart(null);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    fetchPrograms(null);
    setPrevStack([]);
  }, [applyFilters]);


  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };


  const handleApplyFilters = () => setApplyFilters((prev) => prev + 1);


  const loadNextPage = () => {
    if (nextStart) {
      setPrevStack((prev) => [...prev, nextStart]);
      fetchPrograms(nextStart);
    }
  };


  const loadPrevPage = () => {
    const newStack = [...prevStack];
    const prevCursor = newStack.pop() || null;
    setPrevStack(newStack);
    fetchPrograms(prevCursor);
  };

  if (loading) return <div className="text-center my-5">Loading programs...</div>;

  return (
    <div className="programs-page">
      <Navbar />
      <Header
        headerText="Programs & Volunteer Opportunities"
        subText="Explore how you can participate or benefit from local programs."
      />


      {error && (
        <div className="container my-5 text-warning">
          Failed to load live data: {error}
        </div>
      )}


      {/* FILTERS */}
      <div className="container mb-4">
        <div className="d-flex flex-wrap gap-3">
          <select name="frequency" value={filters.frequency} onChange={handleFilterChange} className="form-select w-auto">
            <option value="">All Frequencies</option>
            <option value="Weekly">Weekly</option>
            <option value="Monthly">Monthly</option>
            <option value="Yearly">Yearly</option>
          </select>


          <select name="eligibility" value={filters.eligibility} onChange={handleFilterChange} className="form-select w-auto">
            <option value="">All Eligibility</option>
            <option value="Everybody">Everybody</option>
            <option value="Families">Families</option>
            <option value="Seniors">Seniors</option>
          </select>


          <select name="cost" value={filters.cost} onChange={handleFilterChange} className="form-select w-auto">
            <option value="">All Costs</option>
            <option value="Free">Free</option>
            <option value="Paid">Paid</option>
          </select>


          <select name="program_type" value={filters.program_type} onChange={handleFilterChange} className="form-select w-auto">
            <option value="">All Program Types</option>
            <option value="Food Distribution">Food Distribution</option>
            <option value="Volunteer">Volunteer</option>
            <option value="Education">Education</option>
            <option value="Service">Service</option>
          </select>


          {/* HOST FILTER */}
          <select name="host" value={filters.host} onChange={handleFilterChange} className="form-select w-auto">
            <option value="">All Hosts</option>
            {allHosts.map((h) => (
              <option key={h} value={h}>{h}</option>
            ))}
          </select>


          <button className="btn btn-primary" onClick={handleApplyFilters}>
            Apply
          </button>
        </div>
      </div>

      {/* PROGRAM CARDS */}
      <main className="container my-5">
        <div className="card-grid">
          {programs.length > 0 ? (
            programs.map((p) => (
              <ProgramCard
                key={p.id}
                id={p.id}
                name={p.name}
                program_type={p.program_type}
                freq={p.frequency}
                host={p.host}
                eligibility={p.eligibility}
                cost={p.cost}
              />
            ))
          ) : (
            <p className="text-center mt-5">No programs found matching your criteria.</p>
          )}
        </div>

        {/* Pagination */}
        <div className="d-flex justify-content-center mt-4 gap-2">
          <button className="btn btn-secondary" onClick={loadPrevPage} disabled={prevStack.length === 0}>
            Previous
          </button>
          <button className="btn btn-secondary" onClick={loadNextPage} disabled={!nextStart}>
            Next
          </button>
        </div>
      </main>


      <Footer />
    </div>
  );
};

export default Programs;