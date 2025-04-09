describe('Основные функции системы', () => {
  beforeEach(() => {
    // Очищаем куки перед каждым тестом
    cy.clearCookies()
  })

  it('Вход в систему', () => {
    // Проверяем процесс входа с учетными данными admin
    cy.visit('/login')
    cy.get('input[name="username"]').type('admin')
    cy.get('input[name="password"]').type('admin123')
    cy.get('button[type="submit"]').click()
    
    // После успешного входа должны быть перенаправлены на главную
    cy.url().should('include', '/')
    
    // Проверяем, что вход выполнен успешно
    cy.get('a.nav-link').contains('Выход').should('exist')
  })

  it('Просмотр главной страницы', () => {
    // Перейти на главную страницу
    cy.visit('/')
    
    // Проверяем, что главная страница загружена
    cy.get('h1').should('exist')
    
    // Проверяем наличие списка номеров или другого основного контента
    cy.get('.container').should('exist')
  })

  it('Регистрация нового пользователя', () => {
    // Уникальное имя пользователя с временной меткой
    const username = `test_user_${Date.now()}`
    const email = `${username}@example.com`
    
    // Переходим на страницу регистрации
    cy.visit('/register')
    
    // Заполняем форму регистрации
    cy.get('input[name="username"]').type(username)
    cy.get('input[name="email"]').type(email)
    cy.get('input[name="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    
    // После успешной регистрации должны быть перенаправлены на главную
    cy.url().should('include', '/')
  })

  it('Бронирование номера', () => {
    // Логинимся как администратор
    cy.visit('/login')
    cy.get('input[name="username"]').type('admin')
    cy.get('input[name="password"]').type('admin123')
    cy.get('button[type="submit"]').click()
    
    // Ждем успешного входа
    cy.url().should('include', '/')
    
    // Переходим на главную страницу
    cy.visit('/')
    
    // Находим первый номер в списке и кликаем по нему
    cy.get('.card a').first().click()
    
    // Проверяем, что мы перешли на страницу бронирования
    cy.url().should('include', '/book/')
    
    // Проверяем содержимое страницы
    cy.get('body').then($body => {
      console.log('Page HTML:', $body.html())
    })
    
    // Ждем загрузки flatpickr
    cy.get('#check_in').should('be.visible')
    cy.get('#check_out').should('be.visible')
    
    // Заполняем форму бронирования через flatpickr
    cy.get('#check_in').click()
    cy.get('.flatpickr-calendar').should('be.visible')
    cy.get('.flatpickr-day:not(.flatpickr-disabled)').first().click({ force: true })
    
    // Ждем, пока календарь закроется
    cy.get('.flatpickr-calendar').should('not.be.visible')
    
    cy.get('#check_out').click()
    cy.get('.flatpickr-calendar').should('be.visible')
    cy.get('.flatpickr-day:not(.flatpickr-disabled)').eq(2).click({ force: true })
    
    // Ждем, пока календарь закроется
    cy.get('.flatpickr-calendar').should('not.be.visible')

    // Проверяем наличие формы и её содержимое
    cy.get('form#bookingForm').should('exist').then($form => {
      console.log('Form found:', $form.length)
      console.log('Form HTML:', $form.html())
    })
    
    // Проверяем наличие кнопки отправки
    cy.get('form#bookingForm .btn-primary').should('exist').then($button => {
      console.log('Submit button found:', $button.length)
      console.log('Button HTML:', $button.html())
    })
    
    // Отправляем форму
    cy.get('form#bookingForm .btn-primary').should('be.visible').click()
  })
}) 