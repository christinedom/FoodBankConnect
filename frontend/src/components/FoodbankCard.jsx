import { useNavigate } from "react-router-dom";

const FoodBankCard = ({ id, name, city, zipcode, urgency }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/foodbanks/${encodeURIComponent(name)}`, {
      state: { id, name, city, zipcode, urgency },
    });
  };

  return (
    <div
      className="card h-100 shadow-sm"
      style={{ cursor: "pointer" }}
      onClick={handleClick}
    >
      <div className="card-body">
        <p><strong>Name:</strong> {name}</p>
        <p><strong>City:</strong> {city || "N/A"}</p>
        <p><strong>ZIP Code:</strong> {zipcode || "N/A"}</p>
        <p><strong>Urgency:</strong> {urgency || "N/A"}</p>
        <p><strong>Eligibility:</strong> Everybody</p>
      </div>
    </div>
  );
};

export default FoodBankCard;
