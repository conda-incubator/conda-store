describe('First Test', () => {
  it('Check conda-store home page', () => {
    // display home page without login
    cy.visit('/conda-store/');

    // visit login page
    cy.visit('/conda-store/login/');

    // click on sign in with jupyterhub
    // login through jupyterhub oauth server
    cy.get('#login')
      .should('contain', 'Please sign in');

    cy.get('#username')
      .should('be.visible')
      .type('username@example.com')

    cy.get('#password')
      .should('be.visible')
      .type('password')

    cy.get('form').submit()
    cy.url().should('include', 'user')

    // visit home page again
    cy.get('a.navbar-brand').click()

    // visit environment
    cy.get('h5.card-title > a').contains('filesystem/python-flask-env').click()

    // visit build
    cy.get('li.list-group-item > a').contains('Build').click()
  })
})
