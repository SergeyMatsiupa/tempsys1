import pika
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)  # Устанавливаем уровень DEBUG для максимальной детализации
logger = logging.getLogger(__name__)      # Создаем логгер

try:
    print("Создание очереди RabbitMQ")
    parameters = pika.ConnectionParameters('localhost')  # Параметры подключения к localhost:5672
    connection = pika.BlockingConnection(parameters)     # Устанавливаем блокирующее соединение
    channel = connection.channel()                       # Создаем канал
    channel.queue_declare(queue='test')                  # Объявляем очередь 'test'
    channel.queue_bind(queue='test', exchange='amq.direct', routing_key='test')  # Привязываем очередь
    print("Очередь создана и привязана")
except Exception as e:
    logger.error(f"Ошибка: {e}")  # Логируем ошибку с полным описанием
finally:
    if 'connection' in locals() and connection.is_open:  # Проверяем, существует ли соединение и открыто ли оно
        connection.close()                               # Закрываем соединение
        print("Соединение закрыто")