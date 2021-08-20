describe('First Test', () => {
  it('Check conda-store home page', () => {
    // display home page without login
    cy.visit('/conda-store/');

    // visit login page
    cy.visit('/conda-store/login/')

    // click on sign in with jupyterhub
    // login through jupyterhub oauth server
    cy.get('#login > a')
      .should('contain', 'Sign in with JupyterHub')
      .click();

    // fill in username and password and submit
    cy.get('#username_input')
      .type('conda-store-test');

    cy.get('#password_input')
      .type('test');

    cy.get('form').submit();
  })
})
