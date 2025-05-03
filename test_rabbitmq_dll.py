import ctypes
from ctypes import POINTER, Structure, c_uint16, c_char_p, c_int, c_void_p
import os

os.environ['AMQP_DEBUG'] = '1'  # Enable AMQP debugging
DLL_PATH = r"C:\wamp64\bin\php\php8.2.27\rabbitmq.4.dll"

# Load DLL
try:
    rabbitmq_dll = ctypes.CDLL(DLL_PATH)
    print(f"Successfully loaded DLL from {DLL_PATH}")
except OSError as e:
    print(f"Failed to load DLL: {e}")
    exit(1)

# Define types (unchanged)
class amqp_connection_state_t(Structure):
    pass

class amqp_rpc_reply_t(Structure):
    _fields_ = [("reply_type", c_int), ("reply", c_void_p), ("library_error", c_int)]

amqp_channel_t = c_uint16
AMQP_SASL_METHOD_PLAIN = 0
AMQP_RESPONSE_NORMAL = 0
AMQP_STATUS_OK = 0

# Function prototypes (unchanged)
rabbitmq_dll.amqp_new_connection.restype = POINTER(amqp_connection_state_t)
rabbitmq_dll.amqp_tcp_socket_new.argtypes = [POINTER(amqp_connection_state_t)]
rabbitmq_dll.amqp_tcp_socket_new.restype = c_void_p
rabbitmq_dll.amqp_socket_open.argtypes = [c_void_p, c_char_p, c_int]
rabbitmq_dll.amqp_socket_open.restype = c_int
rabbitmq_dll.amqp_login.argtypes = [POINTER(amqp_connection_state_t), c_char_p, c_int, c_int, c_int, c_int, c_char_p, c_char_p]
rabbitmq_dll.amqp_login.restype = amqp_rpc_reply_t
rabbitmq_dll.amqp_destroy_connection.argtypes = [POINTER(amqp_connection_state_t)]
rabbitmq_dll.amqp_error_string2.restype = c_char_p

# Check library version
try:
    rabbitmq_dll.amqp_version.restype = c_char_p
    version = rabbitmq_dll.amqp_version()
    print(f"rabbitmq-c library version: {version.decode() if version else 'Unknown'}")
except AttributeError:
    print("amqp_version function not found in DLL")

# Step 1: Create connection
conn = rabbitmq_dll.amqp_new_connection()
if not conn:
    print("Failed to create connection")
    exit(1)
print("Connection created successfully:", conn)

# Step 2: Create socket
socket = rabbitmq_dll.amqp_tcp_socket_new(conn)
if not socket:
    print("Failed to create socket")
    rabbitmq_dll.amqp_destroy_connection(conn)
    exit(1)
print("Socket created successfully:", socket)

# Step 3: Open socket
host = b"127.0.0.1"
port = 5672
print(f"Attempting to open socket at {host.decode()}:{port}")
status = rabbitmq_dll.amqp_socket_open(socket, host, port)
if status != AMQP_STATUS_OK:
    error_msg = rabbitmq_dll.amqp_error_string2()
    print(f"Failed to open socket: status {status}, error: {error_msg.decode() if error_msg else 'Unknown error'}")
    rabbitmq_dll.amqp_destroy_connection(conn)
    exit(1)
print("Socket opened successfully")

# Step 4: Login
username = b"testuser"
password = b"testpass"
vhost = b"/"
channel_max = 0
frame_max = 131072
heartbeat = 60
print(f"Login parameters: vhost='{vhost.decode()}', channel_max={channel_max}, frame_max={frame_max}, heartbeat={heartbeat}, username='{username.decode()}'")
print("Attempting login...")
reply = rabbitmq_dll.amqp_login(conn, vhost, channel_max, frame_max, heartbeat, AMQP_SASL_METHOD_PLAIN, username, password)
print(f"Login result: reply_type={reply.reply_type}, library_error={reply.library_error}")
if reply.reply_type != AMQP_RESPONSE_NORMAL:
    error_msg = rabbitmq_dll.amqp_error_string2()
    print(f"Login failed: reply_type {reply.reply_type}, library_error {reply.library_error}, details: {error_msg.decode() if error_msg else 'No additional info'}")
    print("Connection state after login attempt:", conn)
    rabbitmq_dll.amqp_destroy_connection(conn)
    exit(1)
print("Login successful")

# Cleanup
rabbitmq_dll.amqp_destroy_connection(conn)
print("Connection closed, test completed")