import pika
credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
channel = connection.channel()
channel.queue_declare(queue='test_queue')
channel.basic_publish(exchange='', routing_key='test_queue', body='Hello, RabbitMQ!')
print("Сообщение отправлено")
connection.close()