import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import Header from "../components/Header";
import Footer from "../components/Footer";
import FoodbankCard from "../components/FoodbankCard";
import "../styles/Foodbanks.css"; // Add this line if you don't already have it

const BASE_URL = "https://api.foodbankconnect.me/v1/foodbanks";

const Foodbanks = () => {
  const [foodbanks, setFoodbanks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFoodBanks = async () => {
      try {
        const response = await fetch(`${BASE_URL}?size=10&start=1`);
        if (!response.ok) throw new Error("Failed to fetch food banks");
        const data = await response.json();
        setFoodbanks(data.items || []);
      } catch (err) {
        console.error("Error fetching food banks:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchFoodBanks();
  }, []);

  if (loading) return <div className="container my-5">Loading food banks...</div>;

  return (
    <div className="foodbanks-page">
      <Navbar />
      <Header headerText="Food Banks" />

      <main className="container my-5">
        {error && (
          <div className="text-danger mb-3">
            Failed to load data. Showing partial content. Error: {error}
          </div>
        )}

        <div className="text-muted mb-3">
          Showing {foodbanks.length} Food Bank{foodbanks.length !== 1 && "s"} in Total
        </div>

        <div className="card-grid">
          {foodbanks.map((bank) => (
            <FoodbankCard
              key={bank.id}
              id={bank.id}
              name={bank.name}
              city={bank.city}
              zipcode={bank.zipcode}
              urgency={bank.urgency}
            />
          ))}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Foodbanks;
