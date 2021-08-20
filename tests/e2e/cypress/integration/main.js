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

    // for some reason this does not
    // respect redirect_uri
    cy.get('form').submit();

    // visit login page
    cy.visit('/conda-store/login/')

    // click on sign in with jupyterhub
    // login through jupyterhub oauth server
    cy.get('#login > a')
      .should('contain', 'Sign in with JupyterHub')
      .click();

    // jupyterhub authorize access
    cy.get('form > input').click()
    cy.url().should('include', 'user')

    // visit home page again
    cy.get('a.navbar-brand').click()

    // visit environment
    cy.get('h5.card-title > a').contains('filesystem/python-numpy-env').click()

    // visit build
    cy.get('li.list-group-item > a').contains('Build').click()
  })
})
