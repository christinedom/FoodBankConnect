import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import Header from "../components/Header";
import Footer from "../components/Footer";
import FoodbankCard from "../components/FoodbankCard";

const BASE_URL = "https://dp3d297dp9.execute-api.us-east-2.amazonaws.com/v1/foodbanks";

const ITEMS_PER_PAGE = 20;

const Foodbanks = () => {
  const [foodbanks, setFoodbanks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    city: "",
    state: "",
    zipcode: "",
    urgency: "",
    eligibility: "",
    languages: "",
  });
  const [nextStart, setNextStart] = useState(null);
  const [prevStack, setPrevStack] = useState([]); // store previous cursors for "Previous"


  // Apply button trigger
  const [applyFilters, setApplyFilters] = useState(0);


  const fetchFoodBanks = async (startCursor = null) => {
    try {
      setLoading(true);


      const params = new URLSearchParams({
        size: ITEMS_PER_PAGE,
        ...(startCursor && { start: startCursor }),
        ...(filters.city && { city: filters.city }),
        ...(filters.state && { state: filters.state }),
        ...(filters.zipcode && { zipcode: filters.zipcode }),
        ...(filters.urgency && { urgency: filters.urgency }),
        ...(filters.eligibility && { eligibility: filters.eligibility }),
        ...(filters.languages && { languages: filters.languages }),
      });


      const fullURL = `${BASE_URL}?${params.toString()}`;
      console.log("Fetching URL:", fullURL);


      const response = await fetch(fullURL);
      if (!response.ok) throw new Error("Failed to fetch food banks");
      const data = await response.json();


      setFoodbanks(data.items || []);
      setNextStart(data.next_start || null);
    } catch (error) {
      console.error("Error fetching food banks:", error);
      setFoodbanks([]);
      setNextStart(null);
    } finally {
      setLoading(false);
    }
  };

  // Fetch on filters applied
  useEffect(() => {
    fetchFoodBanks(null);
    setPrevStack([]);
  }, [applyFilters]);


  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value.trim() }));
  };


  const handleApplyFilters = () => setApplyFilters((prev) => prev + 1);


  const loadNextPage = () => {
    if (nextStart) {
      setPrevStack((prev) => [...prev, nextStart]); // push current cursor
      fetchFoodBanks(nextStart);
    }
  };


  const loadPrevPage = () => {
    const newStack = [...prevStack];
    const prevCursor = newStack.pop() || null;
    setPrevStack(newStack);
    fetchFoodBanks(prevCursor);
  };

  if (loading) return <div className="text-center my-5">Loading...</div>;

  return (
    <div id="wrapper">
      <Navbar />
      <Header headerText="Food Banks" />


      <main className="container my-5">
        {/* Filters */}
        <div className="d-flex flex-wrap gap-3 mb-4">
          <select name="city" value={filters.city} onChange={handleFilterChange}>
            <option value="">Cities</option>
            <option value="Commerce">Commerce</option>
            <option value="Louisville">Louisville</option>
            <option value="Newton">Newton</option>
            <option value="Houston">Houston</option>
            <option value="Mesa">Mesa</option>
            <option value="S Salt Lake">S Salt Lake</option>
            <option value="Mills River">Mills River</option>
            <option value="Greeley">Greeley</option>
            <option value="Woodland">Woodland</option>
            <option value="Stockton">Stockton</option>
            <option value="Fort Worth">Fort Worth</option>
            <option value="Seattle">Seattle</option>
            <option value="Puyallup">Puyallup</option>
            <option value="Chester">Chester</option>
            <option value="Carefree">Carefree</option>
            <option value="Lynnwood">Lynnwood</option>
            <option value="Sahuarita">Sahuarita</option>
            <option value="Auburn">Auburn</option>
            <option value="Edmonds">Edmonds</option>
            <option value="Covington">Covington</option>
          </select>


          <select name="state" value={filters.state} onChange={handleFilterChange}>
            <option value="">States</option>
            {["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>


          <input
            type="text"
            name="zipcode"
            placeholder="Zipcode"
            value={filters.zipcode}
            onChange={handleFilterChange}
          />


          <select name="urgency" value={filters.urgency} onChange={handleFilterChange}>
            <option value="">Urgency Levels</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>


          <select name="eligibility" value={filters.eligibility} onChange={handleFilterChange}>
            <option value="">Eligibility</option>
            <option value="Everybody">Everybody</option>
            <option value="Families">Families</option>
            <option value="Seniors">Seniors</option>
          </select>


          <select name="languages" value={filters.languages} onChange={handleFilterChange}>
            <option value="">Languages</option>
            <option value="English">English</option>
            <option value="Spanish">Spanish</option>
          </select>


          <button className="btn btn-primary" onClick={handleApplyFilters}>
            Apply
          </button>
        </div>


        {/* Foodbanks Grid */}
        <div className="row g-4">
          {foodbanks.length > 0 ? (
            foodbanks.map((bank) => (
              <div key={bank.id} className="col-md-4">
                <FoodbankCard
                  id={bank.id}
                  name={bank.name}
                  city={bank.city}
                  zipcode={bank.zipcode}
                  urgency={bank.urgency}
                  eligibility={bank.eligibility}
                />
              </div>
            ))
          ) : (
            <p className="text-center mt-5">No foodbanks found matching your criteria.</p>
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


export default Foodbanks;
