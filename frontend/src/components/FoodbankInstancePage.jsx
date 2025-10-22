import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import Navbar from "./Navbar";
import Header from "./Header";
import Footer from "./Footer";
import Breadcrumb from "./Breadcrumb";

const BASE_URL = "https://api.foodbankconnect.me/v1/foodbanks";

const FoodbankInstancePage = () => {
  const location = useLocation();
  const { id, name } = location.state || {};

  const [foodbank, setFoodbank] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFoodbankDetails = async () => {
      if (!id) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${BASE_URL}/${id}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        setFoodbank(data);
      } catch (err) {
        console.error("Error fetching food bank:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchFoodbankDetails();
  }, [id]);

  // Display debug info if still loading
  if (loading) {
    return (
      <div className="container my-5">
        <h2>Loading Food Bank Details...</h2>
        <p>Reached instance page!</p>
        <p>ID: {id || "N/A"}</p>
        <p>Name: {name || "N/A"}</p>
      </div>
    );
  }

  if (!foodbank) {
    return (
      <div className="container my-5">
        <h2>Food bank not found or ID missing.</h2>
        <p>ID: {id || "N/A"}</p>
        <p>Name: {name || "N/A"}</p>
      </div>
    );
  }

  return (
    <div id="wrapper">
      <Navbar />
      <Header headerText={`Food Bank - ${foodbank.name || name}`} />
      <Breadcrumb model_type="foodbanks" current_page={foodbank.name || name} />

      <main className="container my-5">
        <section className="mb-4">
          <h2>Details</h2>
          <ul style={{ listStyle: "none", padding: 0 }}>
            <li><strong>ID:</strong> {foodbank.id || "N/A"}</li>
            <li><strong>Name:</strong> {foodbank.name || "N/A"}</li>
            <li><strong>About:</strong> {foodbank.about || "N/A"}</li>
            <li><strong>Website:</strong>{" "}
              {foodbank.website ? (
                <a href={foodbank.website} target="_blank" rel="noreferrer">{foodbank.website}</a>
              ) : "N/A"}
            </li>
            <li><strong>Phone:</strong> {foodbank.phone || "N/A"}</li>
            <li><strong>Image:</strong> {foodbank.image || "N/A"}</li>
            <li><strong>Address:</strong> {foodbank.address || "N/A"}</li>
            <li><strong>City:</strong> {foodbank.city || "N/A"}</li>
            <li><strong>State:</strong> {foodbank.state || "N/A"}</li>
            <li><strong>ZIP Code:</strong> {foodbank.zipcode || "N/A"}</li>
            <li><strong>Urgency:</strong> {foodbank.urgency || "N/A"}</li>
            <li><strong>Capacity:</strong> {foodbank.capacity || "N/A"}</li>
            <li><strong>Languages:</strong> {foodbank.languages?.join(", ") || "N/A"}</li>
            <li><strong>Services:</strong> {foodbank.services?.join(", ") || "N/A"}</li>
            <li><strong>Open Hours:</strong> {foodbank.open_hours || "N/A"}</li>
            <li><strong>Eligibility:</strong> {foodbank.eligibility || "N/A"}</li>
            <li><strong>Fetched At:</strong> {foodbank.fetched_at || "N/A"}</li>
            <li><strong>Created At:</strong> {foodbank.created_at || "N/A"}</li>
          </ul>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default FoodbankInstancePage;
