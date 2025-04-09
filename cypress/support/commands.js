// Пользовательские команды для тестирования
Cypress.Commands.add('login', (username = 'admin', password = 'admin') => {
  cy.visit('/login')
  cy.get('input[name="username"]').type(username)
  cy.get('input[name="password"]').type(password)
  cy.get('button[type="submit"]').click()
  cy.url().should('include', '/')
})

// Команда для проверки наличия элемента на странице
Cypress.Commands.add('elementExists', (selector) => {
  cy.get(selector).should('exist')
})

Cypress.Commands.add('checkRoomAvailability', (roomId, checkIn, checkOut) => {
  cy.request({
    url: `/api/rooms/${roomId}/availability?check_in=${checkIn}&check_out=${checkOut}`,
    failOnStatusCode: false
  })
}) 