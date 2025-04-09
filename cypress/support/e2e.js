// Импортируем команды Cypress
import './commands'

// Обработка необработанных исключений
Cypress.on('uncaught:exception', (err, runnable) => {
  // Возвращаем false, чтобы предотвратить сбой теста
  return false
}) 