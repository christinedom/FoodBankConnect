import React from "react";
import { Link } from "react-router-dom";
import styles from "../styles/NewHome.module.css";

const imgs = [
	"central-texas-food-bank.jpg",
	"new-food-pantry.jpg",
	"cooking-case.png",
	"drive-thru.jpg",
	"food-bank-delivery.jpg",
	"hope-food-pantry.jpg",
	"volunteer.jpg",
	"trader-joes.png",
	"d_lair.png",
];

const NewHome = () => {
	return (
		<div className={`homepage ${styles.carouselWrapper}`}>
			<div className="homepage">
				<div
					id="homecarousel"
					className="carousel slide carousel-fade"
					data-bs-ride="carousel"
					data-bs-pause="false">
					<div className="carousel-inner">
						{imgs.map((image, index) => (
							<div
								key={index}
								className={`carousel-item ${index === 0 ? "active" : ""} ${
									styles.carouselItem
								}`}
								data-bs-interval="3000">
								<img
									src={`images/${image}`}
									alt=""
									className={`d-block ${styles.carouselImage}`}
								/>
							</div>
						))}
					</div>
				</div>
			</div>

			<div className={`${styles.overlayContainer}`}>
				<div id="overlay" className={styles.wrapper}>
					<img className={styles.icon} src="favicon.svg" alt="Food Bank Icon" />
					<p className={styles.info}>
						<strong>We are foodbankconnect.me</strong>
						<br />
						We are a hub for food banks, donors, and volunteers to find ways to
						use <br />
						their skills and resources to provide food for those suffering from
						hunger.
						<br />
						We think no family should be barred from accessing food due to
						poverty.
						<br />
						Our site allows those in need of assistance to search for services
						from
						<br />
						which they can directly benefit. Explore our site and find out about
						our
						<br />
						mission to end hunger!
					</p>
					<table id="nav-buttons">
						<tbody>
							<tr id="select-tr">
								<td>
									<Link to="/foodbanks" className={styles["food-banks-btn"]}>
										<strong>View Food Banks</strong>
									</Link>
								</td>
								<td>
									<Link to="/sponsors" className={styles["sponsors-btn"]}>
										<strong>View Sponsors</strong>
									</Link>
								</td>
								<td>
									<Link to="/programs" className={styles["programs-btn"]}>
										<strong>View Programs</strong>
									</Link>
								</td>
								<td>
									<Link to="/about" className={styles["about-btn"]}>
										<strong>About the Site</strong>
									</Link>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
};

export default NewHome;
