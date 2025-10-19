import { useNavigate } from "react-router-dom";
import Button from "react-bootstrap/Button";
import "../styles/Programs.css";

const ProgramCard = ({
  name,
  type,
  elig,
  freq,
  cost,
  host,
  img,
  about,
  sign_up_link,
  map_link,
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/programs/${name}`, {
      state: {
        name,
        type,
        elig,
        freq,
        cost,
        img,
        about,
        sign_up_link,
      },
    });
  };

  return (
    <div className="program-card d-flex flex-column h-100 shadow-sm">
      <img src={img} className="card-img-top" alt={name} />
      <div className="program-card-body d-flex flex-column flex-grow-1 p-3">
        <h5 className="card-title">{name}</h5>
        <p><strong>Type:</strong> {type}</p>
        <p><strong>Eligibility:</strong> {elig}</p>
        <p><strong>Frequency:</strong> {freq}</p>
        <p><strong>Cost:</strong> {cost}</p>
        <p><strong>Host:</strong> {host}</p>
        <Button className="btn btn-primary mt-auto w-100" onClick={handleClick}>
          See Details
        </Button>
      </div>
    </div>
  );
};

export default ProgramCard;