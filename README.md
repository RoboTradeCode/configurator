# Configurator
## Версия 1.0.1
Предназначен для предоставления гейтам и ядру конфигураций и информации о торгуемых рынках

Актуальный хост: `3.68.58.96`

Пример URL для подключения: http://3.68.58.96:8000/binance/1

### Общее описание Configurator

Программное обеспечение которое предназначено для обеспечения гейтов и ядер следующими данными:

 - информация о торгуемых ценных бумагах
 - рабочие конфигурации

<a name="обобщенный-алгоритм"/>

### Обобщенный алгоритм 

Configurator реализует API, которые использует Агент для получения информации о торгуемых бумагах и конфигурации для работы гейта и шлюза.

Алгоритм работы можно представить так:

1. Агент совершает запрос к API конфигуратора
2. Конфигуратор получает данные из биржи, из конфигов, генерирует торговые маршруты
3. Конфигуратор отправляет JSON  с данными или с ошибкой.

### Деплой на сервере

[Описание процесса деплоя (ссылка на Wiki)](https://github.com/RoboTradeCode/configurator/wiki/%D0%94%D0%B5%D0%BF%D0%BB%D0%BE%D0%B9-%D0%BD%D0%B0-%D1%81%D0%B5%D1%80%D0%B2%D0%B5%D1%80%D0%B5).
