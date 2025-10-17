import { useLocation, Link } from "react-router-dom";
import Navbar from "./Navbar";
import Header from "./Header";
import Footer from "./Footer";
import Breadcrumb from "./Breadcrumb";
import styles from "../styles/Sponsors.module.css";

const SponsorInstancePage = () => {
	const location = useLocation();
	const {
		sponsor_img,
		sponsor_alt,
		name,
		about,
		contribution,
		contribution_amt,
		contribution_unit,
		affiliation,
		sponsor_link,
		past_inv,
		map_link,
	} = location.state || {};
	const decoded_link = decodeURIComponent(map_link)
	return (
		<div id="wrapper">
			<Navbar />
			<Header headerText={"Sponsors & Donors - " + name} />
			<Breadcrumb model_type="sponsors" current_page={name} />

			{/* <!--Main container--> */}
			<main className="container my-5">
				<div className={`${styles["sponsor-img-container"]} text-center mb-4`}>
					<img src={sponsor_img} alt={sponsor_alt} />
				</div>
				<section className={`mb-4 ${styles.about}`}>
					<h2>About</h2>
					<p>{about}</p>
				</section>
				<section className="mb-4">
					<h2>Details</h2>
					<ul style={{ listStyle: "none" }}>
						<li>
							<p>
								<strong>Contribution Type:</strong> {contribution}
							</p>
						</li>
						<li>
							<p>
								<strong>Contribution Amount:</strong> {contribution_amt}
							</p>
						</li>
						<li>
							<p>
								<strong>Contribution Unit:</strong> {contribution_unit}
							</p>
						</li>
						<li>
							<p>
								<strong>Affiliation: </strong> {affiliation}
							</p>
						</li>
						<li>
							{/*Figure out how to link to other instance pages
							 *May want to send in an array of past involvements and
							 *loop through array creating various link components to
							 *other instance pages
							 *Perhaps list of tuples [(model type : instance of model)]
							 *e.g. (Sponsor : Trader Joe's)
							 */}
							<p>
								<strong>Past Involvement: </strong>
								{
									past_inv
									// past_inv.map((inv) =>(
									// 	<Link>{inv}</Link>
									// ))
								}
							</p>
						</li>
						<li style={{ marginTop: "25px" }}>
							<strong>Website: </strong>
							<a href={sponsor_link} target="_blank" rel="noreferrer">
								{sponsor_link}
							</a>
						</li>
					</ul>
				</section>
				<section className={`${styles["map-container"]} mt-3`}>
					<iframe
						style={{ width: "80%", height: "450px" }}
						src={decoded_link}
						allowFullScreen=""
						loading="lazy"
						referrerPolicy="no-referrer-when-downgrade"></iframe>
				</section>
			</main>

			<Footer />
		</div>
	);
};
export default SponsorInstancePage;
