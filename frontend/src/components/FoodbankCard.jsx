import { useNavigate } from "react-router-dom";
import '../styles/CardStyles.css';

const FoodbankCard = ({ id, name, city, zipcode, urgency }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/foodbanks/${encodeURIComponent(name)}`, {
      state: { id, name, city, zipcode, urgency },
    });
  };

  return (
    <div
      className="card-glass h-100"
      style={{ cursor: "pointer" }}
      onClick={handleClick}
    >
      <div className="card-body">
        <p><strong>Name:</strong> {name}</p>
        <p><strong>City:</strong> {city || "N/A"}</p>
        <p><strong>ZIP Code:</strong> {zipcode || "N/A"}</p>
        <p><strong>Urgency:</strong> {urgency || "N/A"}</p>
        <p><strong>Eligibility:</strong> Everybody</p>
        <button className="cta-button">See Details</button>
      </div>
    </div>
  );
};

export default FoodbankCard;
