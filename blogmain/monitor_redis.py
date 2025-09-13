# monitor_redis.py
from django_redis import get_redis_connection
import time

def monitor_redis():
    conn = get_redis_connection("default")
    info = conn.info()
    
    print(f"Connected clients: {info['connected_clients']}")
    print(f"Used memory: {info['used_memory_human']}")
    print(f"Commands processed: {info['total_commands_processed']}")
    print(f"Keyspace hits: {info.get('keyspace_hits', 0)}")
    print(f"Keyspace misses: {info.get('keyspace_misses', 0)}")

if __name__ == "__main__":
    monitor_redis()