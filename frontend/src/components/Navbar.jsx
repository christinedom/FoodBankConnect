import fav from "../assets/react.svg";
import { Link, NavLink } from "react-router-dom";

const Navbar = () => {
	return (
		<nav className="navbar navbar-expand-lg navbar-dark bg-primary">
			<div className="container-fluid">
				<Link className="navbar-brand" to="/">
					<img id="icon" src={fav} alt="My SVG" height="50em" width="50em" />{" "}
					FoodBankConnect
				</Link>
				<div className="collapse navbar-collapse">
					<ul className="navbar-nav ms-auto">
						<li className="nav-item">
							<NavLink className="nav-link" to="/about">
								About
							</NavLink>
						</li>
						<li className="nav-item">
							<NavLink className="nav-link" to="/foodbanks">
								Food Banks
							</NavLink>
						</li>
						<li className="nav-item">
							<NavLink className="nav-link" to="/programs">
								Programs
							</NavLink>
						</li>
						<li className="nav-item">
							<NavLink className="nav-link" to="/sponsors">
								Sponsors
							</NavLink>
						</li>
					</ul>
				</div>
			</div>
		</nav>
	);
};
export default Navbar;
