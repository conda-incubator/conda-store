function reloadPageUntilCompleted(maxAttempts=10, attempts=0) {
    if (attempts > maxAttempts) {
        throw new Error("Timed out waiting for report to be generated")
    }
    cy.get("#build-status").then($build => {
        if (!($build[0].innerHTML.includes('COMPLETED'))) {
            cy.wait(10000); // 10 seconds
            cy.reload()
            reloadPageUntilCompleted(maxAttempts, attempts+1)
        }
    })
}

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
    // should redirect to home page

    // visit environment
    cy.get('h5.card-title > a').contains('filesystem/python-flask-env').click()
    cy.url().should('include', 'environment')

    // visit build
    cy.get('li.list-group-item > a').contains('Build').click()
    cy.url().should('include', 'build')

    // wait for build to complete
    reloadPageUntilCompleted()

    // visit user page
    cy.visit('/conda-store/user/');
  })
})
