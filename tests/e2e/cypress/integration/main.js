describe('First Test', () => {
  it('Check conda-store home page', () => {
    cy.visit('/');

    cy.visit('/login/')

    cy.get('#login > a')
      .should('contain', 'Sign in with JupyterHub')
      .click();
  })
})
