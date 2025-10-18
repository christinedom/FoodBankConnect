import { useNavigate } from "react-router-dom";

const FoodBankCard = ({
  name,
  address,
  city,
  zip,
  capacity,
  days,
  hours,
  urgency,
  link,
  map,
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/foodbanks/${name}`, {
      state: {
        name,
        address,
        city,
        zip,
        capacity,
        days,
        hours,
        urgency,
        link,
        map,
      },
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
          <strong>Address:</strong> {address} <br />
          <strong>City:</strong> {city} <br />
          <b>ZIP Code:</b> {zip} <br />
          <b>Capacity:</b> {capacity} <br />
          <b>Hours:</b> {days}, {hours} <br />
          <b>Urgency:</b> {urgency}
        </p>
      </div>
    </div>
  );
};

export default FoodBankCard;
