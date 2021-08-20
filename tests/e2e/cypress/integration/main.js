describe('First Test', () => {
  it('Check conda-store home page', () => {
    cy.visit('/conda-store/');

    cy.visit('/conda-store/login/')

    cy.get('#login > a')
      .should('contain', 'Sign in with JupyterHub')
      .click();

    cy.get('#username_input')
      .type('conda-store-test');

    cy.get('#password_input')
      .type('test');

    cy.get('form').submit();
  })
})
