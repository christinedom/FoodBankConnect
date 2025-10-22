import { useNavigate } from "react-router-dom";
import "../styles/CardStyles.css";

const ProgramCard = ({ id, name, program_type, freq, host }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/programs/${encodeURIComponent(name)}`, {
      state: { id, name },
    });
  };

  return (
    <div className="card-glass d-flex flex-column h-100 p-3">
      <p><strong>Name:</strong> {name}</p>
      <p><strong>Host:</strong> {host}</p>
      <p><strong>Frequency:</strong> {freq}</p>
      <p><strong>Service Type:</strong> {program_type}</p>
      <p><strong>Eligibility:</strong> Open</p>
      <button className="cta-button mt-auto" onClick={handleClick}>
        See Details
      </button>
    </div>
  );
};

export default ProgramCard;
