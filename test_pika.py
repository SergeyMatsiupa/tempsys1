import pika

# Параметры подключения
credentials = pika.PlainCredentials('testuser', 'testpass')
parameters = pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials)

# Установка соединения
try:
    connection = pika.BlockingConnection(parameters)
    print("Подключение успешно установлено")
    connection.close()
    print("Соединение закрыто")
except Exception as e:
    print(f"Ошибка подключения: {e}")