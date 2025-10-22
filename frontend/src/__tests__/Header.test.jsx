import { render, screen } from '@testing-library/react';
import Header from "../components/Header"

test(`Making sure component renders`, () => {
	render(<Header headerText="This should have rendered"/>)

	const header_component = screen.getByText(`This should have rendered`)

	expect(header_component).toBeInTheDocument()
});

test(`Testing sub header text`, () => {
	render(<Header headerText="This should never be empty/null" subText="This should render alongside main header"/>)

	const main_header = screen.getByText(`This should never be empty/null`)
	const sub_text = screen.getByText(`This should render alongside main header`)

	expect(main_header).toBeInTheDocument()
	expect(sub_text).toBeInTheDocument()
});