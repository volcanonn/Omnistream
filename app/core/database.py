import redis
from redis.exceptions import ConnectionError
from app.core.proto.media_info_pb2 import MediaInfoSummary

redis_client = None
MediaInfoSummaryContext = None

def connect_to_redis():
    """
    Initializes the redis client connection and assigns it to the global variable.
    This function is called once when the FastAPI application starts.
    """
    global redis_client, MediaInfoSummaryContext
    
    MediaInfoSummaryContext = MediaInfoSummary()
    print("Attempting to connect to DragonflyDB...")

    DB_HOST = "localhost"
    DB_PORT = 6379

    try:
        redis_client = redis.Redis(host=DB_HOST, port=DB_PORT, db=0, decode_responses=False)
        redis_client.ping()
        print(f"Successfully connected to DragonflyDB at {DB_HOST}:{DB_PORT}")
    except redis.exceptions.ConnectionError as e:
        print(f"FATAL: Could not connect to DragonflyDB. Please check the connection. Error: {e}")
        # In a real application, you might want to exit or handle this more gracefully
        redis_client = None # Ensure client is None if connection fails


def close_redis_connection():
    """
    Closes the redis client connection.
    This function is called once when the FastAPI application shuts down.
    """
    global redis_client
    if redis_client:
        redis_client.close()
        print("Redis connection closed.")