import { useNavigate } from "react-router-dom";
import styles from "./SponsorCard.module.css";
import '../styles/CardStyles.css';

const SponsorCard = ({
	id,
	name,
	affiliation,
	city,
	state,
}) => {
	const navigate = useNavigate();

	const handleClick = () => {
		navigate(`/sponsors/${id}`, {
			state: { id },
		});
	};

	return (
		<div
			className={`card-glass ${styles["sponsor-card"]}`}
			onClick={handleClick}
			style={{ cursor: "pointer" }}
		>
			<div className={styles["card-body"]}>
				<p className={styles["text"]}>
					<strong>Name:</strong> {name}
					<br />
					<strong>Contribution:</strong> Donations / Grants
					<br />
					<strong>Affiliation:</strong> {affiliation}
					<br />
					<strong>City:</strong> {city}
					<br />
					<strong>State:</strong> {state}
				</p>
				<button className="cta-button">See Details</button>
			</div>
		</div>
	);
};

export default SponsorCard;