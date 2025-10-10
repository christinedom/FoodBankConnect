const Header = ({HeaderText}) => {
	return (
		<header className="py-5 text-center bg-light border-bottom">
			<div className="container-fluid">
				<h1 className="display-5 fw-bold">{HeaderText}</h1>
			</div>
		</header>
	);
};
export default Header;
