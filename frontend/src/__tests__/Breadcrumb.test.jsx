import { render, screen } from '@testing-library/react';
import Breadcrumb from '../components/Breadcrumb'; 

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => (
    <a href={to} {...props}>
      {children}
    </a>
  )
}));

describe('Breadcrumb Component', () => {
  const defaultProps = {
    model_type: 'foodbanks',
    current_page: 'Test Food Bank'
  };

  test('renders without crashing', () => {
    render(<Breadcrumb {...defaultProps} />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  test('has correct accessibility attributes', () => {
    render(<Breadcrumb {...defaultProps} />);
    
    const nav = screen.getByRole('navigation');
    expect(nav).toHaveAttribute('aria-label', 'breadcrumb');
    
    const activeItem = screen.getByText('Test Food Bank').closest('li');
    expect(activeItem).toHaveAttribute('aria-current', 'page');
  });

  test('renders all breadcrumb items', () => {
    render(<Breadcrumb {...defaultProps} />);
    
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Food Banks')).toBeInTheDocument();
    expect(screen.getByText('Test Food Bank')).toBeInTheDocument();
  });

  test('renders correct CSS classes', () => {
    const { container } = render(<Breadcrumb {...defaultProps} />);
    
    const breadcrumb = container.querySelector('.breadcrumb');
    expect(breadcrumb).toBeInTheDocument();
    
    const breadcrumbItems = container.querySelectorAll('.breadcrumb-item');
    expect(breadcrumbItems).toHaveLength(3);
    
    // Check active item has correct class
    const activeItem = screen.getByText('Test Food Bank').closest('li');
    expect(activeItem).toHaveClass('breadcrumb-item', 'active');
  });

  describe('model_type variations', () => {
    test('displays "Food Banks" for model_type "foodbanks"', () => {
      render(<Breadcrumb model_type="foodbanks" current_page="Test Page" />);
      
      expect(screen.getByText('Food Banks')).toBeInTheDocument();
      const foodBanksLink = screen.getByText('Food Banks').closest('a');
      expect(foodBanksLink).toHaveAttribute('href', '/foodbanks');
    });

    test('displays "Programs" for model_type "programs"', () => {
      render(<Breadcrumb model_type="programs" current_page="Test Program" />);
      
      expect(screen.getByText('Programs')).toBeInTheDocument();
      const programsLink = screen.getByText('Programs').closest('a');
      expect(programsLink).toHaveAttribute('href', '/programs');
    });

    test('displays "Sponsors & Donors" for other model_types', () => {
      render(<Breadcrumb model_type="sponsors" current_page="Test Sponsor" />);
      
      expect(screen.getByText('Sponsors & Donors')).toBeInTheDocument();
      const sponsorsLink = screen.getByText('Sponsors & Donors').closest('a');
      expect(sponsorsLink).toHaveAttribute('href', '/sponsors');
    });

    test('displays "Sponsors & Donors" for unknown model_type', () => {
      render(<Breadcrumb model_type="unknown" current_page="Test Page" />);
      
      expect(screen.getByText('Sponsors & Donors')).toBeInTheDocument();
    });
  });

  test('home link points to correct path', () => {
    render(<Breadcrumb {...defaultProps} />);
    
    const homeLink = screen.getByText('Home').closest('a');
    expect(homeLink).toHaveAttribute('href', '/');
  });

  test('model link points to correct path based on model_type', () => {
    const { rerender } = render(<Breadcrumb model_type="foodbanks" current_page="Test" />);
    
    let modelLink = screen.getByText('Food Banks').closest('a');
    expect(modelLink).toHaveAttribute('href', '/foodbanks');

    rerender(<Breadcrumb model_type="programs" current_page="Test" />);
    modelLink = screen.getByText('Programs').closest('a');
    expect(modelLink).toHaveAttribute('href', '/programs');

    rerender(<Breadcrumb model_type="sponsors" current_page="Test" />);
    modelLink = screen.getByText('Sponsors & Donors').closest('a');
    expect(modelLink).toHaveAttribute('href', '/sponsors');
  });

  test('current page is displayed correctly and is not a link', () => {
    render(<Breadcrumb model_type="foodbanks" current_page="Specific Food Bank Name" />);
    
    const currentPage = screen.getByText('Specific Food Bank Name');
    expect(currentPage).toBeInTheDocument();
    
    // Current page should not be a link (it's just text in the active list item)
    const currentPageLink = currentPage.closest('a');
    expect(currentPageLink).toBeNull();
  });

  test('container structure is correct', () => {
    const { container } = render(<Breadcrumb {...defaultProps} />);
    
    const mainContainer = container.querySelector('.container');
    expect(mainContainer).toBeInTheDocument();
    
    const breadcrumbList = container.querySelector('ol.breadcrumb');
    expect(breadcrumbList).toBeInTheDocument();
    
    const listItems = breadcrumbList.querySelectorAll('li');
    expect(listItems).toHaveLength(3);
  });

  test('applies correct styling classes', () => {
    const { container } = render(<Breadcrumb {...defaultProps} />);
    
    const nav = container.querySelector('nav');
    expect(nav).toHaveClass('bg-light', 'py-2');
    
    const breadcrumb = container.querySelector('.breadcrumb');
    expect(breadcrumb).toHaveClass('mb-0');
  });

  describe('edge cases', () => {
    test('handles empty current_page', () => {
      render(<Breadcrumb model_type="foodbanks" current_page="" />);
      
      const currentPageItem = screen.getByRole('navigation').querySelector('.breadcrumb-item.active');
      expect(currentPageItem).toBeInTheDocument();
      expect(currentPageItem).toHaveTextContent('');
    });

    test('handles very long current_page text', () => {
      const longText = 'A'.repeat(100);
      render(<Breadcrumb model_type="programs" current_page={longText} />);
      
      expect(screen.getByText(longText)).toBeInTheDocument();
    });
  });
});