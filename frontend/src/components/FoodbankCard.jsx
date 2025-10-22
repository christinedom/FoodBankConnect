import { useNavigate } from "react-router-dom";

const FoodBankCard = ({ id, name, city, zip }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/foodbanks/${encodeURIComponent(name)}`, {
      state: { id, name, city, zip },
    });
  };

  return (
    <div
      className="card h-100 shadow-sm"
      style={{ cursor: "pointer" }}
      onClick={handleClick}
    >
      <div className="card-body">
        <h5 className="card-title">{name}</h5>
        <p className="card-text">
          <strong>City:</strong> {city || "N/A"} <br />
          <strong>ZIP Code:</strong> {zip || "N/A"}
        </p>
      </div>
    </div>
  );
};

export default FoodBankCard;
