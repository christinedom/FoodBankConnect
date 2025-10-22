import { useNavigate } from "react-router-dom";
import Button from "react-bootstrap/Button";
import "../styles/Programs.css";

const ProgramCard = ({ id, name, program_type, freq, host }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/programs/${encodeURIComponent(name)}`, {
      state: { id },
    });
  };

  return (
    <div className="program-card d-flex flex-column h-100 shadow-sm p-3">
      <h5 className="card-title">{name}</h5>
      <p><strong>Host:</strong> {host}</p>
      <p><strong>Frequency:</strong> {freq}</p>
      <p><strong>Service Type:</strong> {program_type}</p>
      <p><strong>Eligibility:</strong> Open</p>
      <Button className="btn btn-primary mt-auto w-100" onClick={handleClick}>
        See Details
      </Button>
    </div>
  );
};

export default ProgramCard;
