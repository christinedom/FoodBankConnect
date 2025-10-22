import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import Navbar from "./Navbar";
import Header from "./Header";
import Footer from "./Footer";
import Breadcrumb from "./Breadcrumb";

const BASE_URL = "https://api.foodbankconnect.me/v1/programs";
const FOODBANKS_URL = "https://api.foodbankconnect.me/v1/foodbanks?size=50&start=1";

const ProgramsInstancePage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = location.state || {};
  const [program, setProgram] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProgram = async () => {
      if (!id) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(`${BASE_URL}/${id}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setProgram(data);
      } catch (err) {
        console.error("Error fetching program:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchProgram();
  }, [id]);

  // Navigate to the foodbank page by host name
  const handleHostClick = async (hostName) => {
    try {
      const res = await fetch(FOODBANKS_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const target = (data.items || []).find(fb => fb.name === hostName);
      if (target) {
        navigate(`/foodbanks/${encodeURIComponent(target.name)}`, { state: { id: target.id } });
      } else {
        alert(`Foodbank not found: ${hostName}`);
      }
    } catch (err) {
      console.error("Error fetching foodbanks:", err);
    }
  };

  if (loading) return <div className="container my-5">Loading program details...</div>;
  if (!program) return <div className="container my-5">Program not found.</div>;

  return (
    <div className="wrapper">
      <Navbar />
      <Header headerText={program.name} />
      <Breadcrumb model_type="programs" current_page={program.name} />

      <main className="container my-5">
        <div className="row">
          <div className="col-lg-6 mb-4">
            {program.image ? (
              <img src={program.image} className="img-fluid rounded shadow" alt={program.name} />
            ) : (
              <div className="text-muted">No image available</div>
            )}
          </div>

          <div className="col-lg-6">
            <h3 className="fw-bold">Program Details</h3>
            <ul className="list-group mb-3">
              <li className="list-group-item"><strong>ID:</strong> {program.id}</li>
              <li className="list-group-item"><strong>Type:</strong> {program.program_type}</li>
              <li className="list-group-item"><strong>Frequency:</strong> {program.frequency}</li>
              <li className="list-group-item"><strong>Eligibility:</strong> {program.eligibility || "Everybody"}</li>
              <li className="list-group-item"><strong>Cost:</strong> {program.cost}</li>
              <li className="list-group-item">
                <strong>Host:</strong>{" "}
                {program.host ? (
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      handleHostClick(program.host);
                    }}
                  >
                    {program.host}
                  </a>
                ) : "N/A"}
              </li>
              <li className="list-group-item"><strong>Details Page:</strong> {program.details_page}</li>
              <li className="list-group-item"><strong>Sign Up / Learn More:</strong> {program.sign_up_link || "N/A"}</li>
              <li className="list-group-item"><strong>Links:</strong> {program.links || "N/A"}</li>
              <li className="list-group-item"><strong>Created At:</strong> {program.created_at}</li>
              <li className="list-group-item"><strong>Fetched At:</strong> {program.fetched_at || "N/A"}</li>
            </ul>
          </div>
        </div>

        <section className="mt-5">
          <h3>About the Program</h3>
          <p>{program.about || "No description available."}</p>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default ProgramsInstancePage;
