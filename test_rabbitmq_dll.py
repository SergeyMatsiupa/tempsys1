import ctypes
from ctypes import POINTER, Structure, c_uint16, c_char_p, c_int, c_void_p

# Путь к DLL
DLL_PATH = r"C:\wamp64\bin\php\php8.2.27\rabbitmq.4.dll"

# Загрузка DLL
try:
    rabbitmq_dll = ctypes.CDLL(DLL_PATH)
    print(f"Успешно загружена DLL из {DLL_PATH}")
except OSError as e:
    print(f"Не удалось загрузить DLL: {e}")
    exit(1)

# Определение типов
class amqp_connection_state_t(Structure):
    pass  # Заглушка для состояния соединения

class amqp_rpc_reply_t(Structure):
    _fields_ = [
        ("reply_type", c_int),
        ("reply", c_void_p),
        ("library_error", c_int),
    ]

amqp_channel_t = c_uint16  # Тип канала

# Константы
AMQP_SASL_METHOD_PLAIN = 0
AMQP_RESPONSE_NORMAL = 0
AMQP_STATUS_OK = 0

# Настройка прототипов функций
rabbitmq_dll.amqp_new_connection.restype = POINTER(amqp_connection_state_t)
rabbitmq_dll.amqp_tcp_socket_new.argtypes = [POINTER(amqp_connection_state_t)]
rabbitmq_dll.amqp_tcp_socket_new.restype = c_void_p
rabbitmq_dll.amqp_socket_open.argtypes = [c_void_p, c_char_p, c_int]
rabbitmq_dll.amqp_socket_open.restype = c_int
rabbitmq_dll.amqp_login.argtypes = [POINTER(amqp_connection_state_t), c_char_p, c_int, c_int, c_int, c_int, c_char_p, c_char_p]
rabbitmq_dll.amqp_login.restype = amqp_rpc_reply_t
rabbitmq_dll.amqp_destroy_connection.argtypes = [POINTER(amqp_connection_state_t)]
rabbitmq_dll.amqp_destroy_connection.restype = None
rabbitmq_dll.amqp_error_string2.restype = c_char_p
rabbitmq_dll.amqp_error_string2.argtypes = []

# Добавляем проверку версии библиотеки (если доступна)
try:
    rabbitmq_dll.amqp_version.restype = c_char_p
    version = rabbitmq_dll.amqp_version()
    print(f"Версия библиотеки rabbitmq-c: {version.decode() if version else 'Неизвестно'}")
except AttributeError:
    print("Функция amqp_version не найдена в DLL")

# Шаг 1: Создание соединения
conn = rabbitmq_dll.amqp_new_connection()
if not conn:
    print("Не удалось создать соединение")
    exit(1)
print("Соединение создано успешно: %s" % conn)

# Шаг 2: Создание сокета
socket = rabbitmq_dll.amqp_tcp_socket_new(conn)
if not socket:
    print("Не удалось создать сокет")
    rabbitmq_dll.amqp_destroy_connection(conn)
    exit(1)
print("Сокет создан успешно: %s" % socket)

# Шаг 3: Открытие сокета
host = b"127.0.0.1"
port = 5672
print(f"Попытка открыть сокет на {host.decode()}:{port}")
status = rabbitmq_dll.amqp_socket_open(socket, host, port)
if status != AMQP_STATUS_OK:
    error_msg = rabbitmq_dll.amqp_error_string2()
    print(f"Не удалось открыть сокет: статус {status}, ошибка: {error_msg.decode() if error_msg else 'Неизвестная ошибка'}")
    rabbitmq_dll.amqp_destroy_connection(conn)
    exit(1)
print("Сокет открыт успешно")

# Шаг 4: Логин с testuser
username = b"testuser"
password = b"testpass"
vhost = b"/"
channel_max = 0
frame_max = 131072  # Стандартное значение для RabbitMQ
heartbeat = 60      # Включен для поддержания соединения
print(f"Параметры логина: vhost='{vhost.decode()}', channel_max={channel_max}, frame_max={frame_max}, heartbeat={heartbeat}, username='{username.decode()}'")
reply = rabbitmq_dll.amqp_login(conn, vhost, channel_max, frame_max, heartbeat, AMQP_SASL_METHOD_PLAIN, username, password)
print(f"Результат логина: reply_type={reply.reply_type}, library_error={reply.library_error}")
if reply.reply_type != AMQP_RESPONSE_NORMAL:
    error_msg = rabbitmq_dll.amqp_error_string2()
    print(f"Логин не удался: reply_type {reply.reply_type}, library_error {reply.library_error}, подробности: {error_msg.decode() if error_msg else 'Нет дополнительной информации'}")
    rabbitmq_dll.amqp_destroy_connection(conn)
    exit(1)
print("Логин выполнен успешно")

# Очистка ресурсов
rabbitmq_dll.amqp_destroy_connection(conn)
print("Соединение закрыто, тест завершен")