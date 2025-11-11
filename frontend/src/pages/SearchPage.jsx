import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Header from "../components/Header";
import Footer from "../components/Footer";
import styles from "../styles/SearchPage.module.css";

const BASE_URL = "https://api.foodbankconnect.me/v1/search";

const SearchPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const urlQuery = searchParams.get("q") || "";
  const [query, setQuery] = useState(urlQuery);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const performSearch = useCallback(async (searchQuery) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BASE_URL}?q=${encodeURIComponent(searchQuery)}`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setResults(data.items || []);
    } catch (err) {
      console.error("Search error:", err);
      setError("Failed to search. Please try again.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Search when URL query parameter changes
  useEffect(() => {
    if (urlQuery) {
      setQuery(urlQuery);
      performSearch(urlQuery);
    }
  }, [urlQuery, performSearch]);

  const handleSearch = async (e) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed) {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`);
      // The useEffect will trigger the search
    }
  };

  // Highlight matching text
  const highlight = (text, term) => {
    if (!term) return text;
    const regex = new RegExp(`(${term})`, "gi");
    return text.replace(regex, "<mark>$1</mark>");
  };

  return (
    <div id="wrapper">
      <Navbar />
      <Header headerText="Search" />
      
      <main className="container my-5">
        <div className={styles.container}>
          <form onSubmit={handleSearch} className={styles.searchBar}>
            <input
              type="text"
              placeholder="Search for food banks, sponsors, or programs..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit" disabled={loading}>
              {loading ? "Searching..." : "Search"}
            </button>
          </form>

          {error && <div className="alert alert-danger mt-3">{error}</div>}

          <div className={styles.results}>
            {loading && <p>Searching...</p>}
            {!loading && results.length === 0 && query && <p>No results found.</p>}
            {!loading && results.map((r, i) => {
              const modelPath = r.model.toLowerCase();
              const routePath = `/${modelPath}/${encodeURIComponent(r.name)}`;
              // Capitalize first letter for display
              const modelDisplay = r.model.charAt(0).toUpperCase() + r.model.slice(1);
              return (
                <div key={i} className={styles.resultCard}>
                  <p className={styles.modelTag}>{modelDisplay}</p>
                  <Link 
                    to={routePath}
                    state={{ id: r.id, name: r.name }}
                    dangerouslySetInnerHTML={{
                      __html: `<strong>${r.name}</strong>`,
                    }}
                  />
                  <p
                    dangerouslySetInnerHTML={{
                      __html: highlight(r.snippet, query),
                    }}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default SearchPage;
