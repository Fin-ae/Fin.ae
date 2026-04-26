// Cypress e2e test script
describe('Finae App End-to-End', () => {
  beforeEach(() => {
    cy.visit('http://localhost:3000');
  });

  it('displays the main header and hero section', () => {
    cy.contains('Finae').should('be.visible');
    cy.contains('Find the best financial products').should('be.visible');
  });

  it('can browse news section and click pagination', () => {
    cy.get('[data-testid="news-section"]').scrollIntoView();
    cy.contains('Financial News & Insights').should('be.visible');
    
    // Click page 2
    cy.contains('button', '2').click();
    
    // Wait for fetch to complete
    cy.wait(1000); 
    cy.get('[data-testid="news-grid"]').children().should('have.length.at.least', 1);
  });
});
