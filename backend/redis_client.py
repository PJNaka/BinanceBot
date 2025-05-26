# backend/redis_client.py
import json
import redis.asyncio as aioredis # Using redis.asyncio as aioredis
from typing import Any, Dict, Optional

# Import configuration variables (will be loaded from config.py in a real app)
# from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, AGENT_CONTEXT_TTL_SECONDS
# For standalone testing or if config.py isn't fully wired yet:
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None 
AGENT_CONTEXT_TTL_SECONDS = 3600


# Global variable to hold the Redis connection pool
redis_pool: Optional[aioredis.ConnectionPool] = None

async def init_redis_pool():
    """Initializes the Redis connection pool."""
    global redis_pool
    if redis_pool is not None:
        # print("Redis pool already initialized.")
        return

    # Construct Redis URL, handling optional password
    if REDIS_PASSWORD:
        redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    else:
        redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    try:
        # print(f"Initializing Redis pool with URL: {redis_url.replace(REDIS_PASSWORD, '********') if REDIS_PASSWORD else redis_url}")
        redis_pool = aioredis.ConnectionPool.from_url(redis_url, max_connections=20, decode_responses=False) # decode_responses=False because we handle JSON
        # Test connection
        async with get_redis_connection() as r:
            await r.ping()
        print("Successfully connected to Redis and initialized connection pool.")
    except Exception as e:
        print(f"Error initializing Redis pool: {e}")
        redis_pool = None # Ensure pool is None if initialization fails

async def get_redis_connection() -> aioredis.Redis:
    """
    Provides an asynchronous Redis connection from the pool.
    Usage: async with get_redis_connection() as r: ...
    """
    if redis_pool is None:
        # This can happen if init_redis_pool failed or was not called.
        # Depending on strictness, could raise an error or try to init again.
        print("Redis pool not initialized. Attempting to initialize now.")
        await init_redis_pool() # Try to initialize if not already
        if redis_pool is None: # If still None after attempt
             raise ConnectionError("Redis connection pool is not available.")

    # The pool itself manages connections, so we create a Redis client instance with it.
    # redis.asyncio.Redis.from_pool is suitable for creating a client from an established pool.
    # However, the more direct way is to use aioredis.Redis(connection_pool=redis_pool)
    return aioredis.Redis(connection_pool=redis_pool)


async def close_redis_pool():
    """Closes the Redis connection pool."""
    global redis_pool
    if redis_pool:
        try:
            await redis_pool.disconnect()
            print("Redis connection pool closed.")
        except Exception as e:
            print(f"Error closing Redis pool: {e}")
        finally:
            redis_pool = None


def _generate_context_key(user_id: Any, session_id: Any) -> str:
    """Generates a consistent Redis key for agent context."""
    return f"agent_context:user_{str(user_id)}:session_{str(session_id)}"


async def save_agent_context(
    user_id: Any, 
    session_id: Any, 
    context_data: Dict[str, Any], 
    ttl: Optional[int] = None
) -> bool:
    """
    Saves agent context data to Redis as a JSON string with a TTL.
    Args:
        user_id: User identifier.
        session_id: Session identifier.
        context_data: The context data dictionary to save.
        ttl: Time-to-live in seconds. Defaults to AGENT_CONTEXT_TTL_SECONDS from config.
    Returns:
        True if successful, False otherwise.
    """
    if ttl is None:
        ttl = AGENT_CONTEXT_TTL_SECONDS
        
    key = _generate_context_key(user_id, session_id)
    try:
        json_data = json.dumps(context_data)
        async with get_redis_connection() as r:
            await r.set(key, json_data, ex=ttl)
        # print(f"Saved context for key {key} with TTL {ttl}s.")
        return True
    except json.JSONEncodeError as e:
        print(f"Error encoding context data to JSON for key {key}: {e}")
        return False
    except Exception as e:
        print(f"Error saving agent context to Redis for key {key}: {e}")
        return False


async def load_agent_context(user_id: Any, session_id: Any) -> Optional[Dict[str, Any]]:
    """
    Loads agent context data from Redis.
    Args:
        user_id: User identifier.
        session_id: Session identifier.
    Returns:
        The context data dictionary if found, otherwise None.
    """
    key = _generate_context_key(user_id, session_id)
    try:
        async with get_redis_connection() as r:
            json_data = await r.get(key)
        
        if json_data:
            # print(f"Loaded context for key {key}.")
            return json.loads(json_data) # json_data will be bytes if decode_responses=False on pool
        else:
            # print(f"No context found for key {key}.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error decoding context data from JSON for key {key}: {e}")
        return None
    except Exception as e:
        print(f"Error loading agent context from Redis for key {key}: {e}")
        return None


async def delete_agent_context(user_id: Any, session_id: Any) -> bool:
    """
    Deletes agent context data from Redis.
    Args:
        user_id: User identifier.
        session_id: Session identifier.
    Returns:
        True if deletion was successful (or key did not exist), False on error.
    """
    key = _generate_context_key(user_id, session_id)
    try:
        async with get_redis_connection() as r:
            await r.delete(key)
        # print(f"Deleted context for key {key}.")
        return True
    except Exception as e:
        print(f"Error deleting agent context from Redis for key {key}: {e}")
        return False

# Example Usage (for testing, can be run with `python -m backend.redis_client`)
async def main_test():
    print("Starting Redis client test...")
    # Initialize pool (normally done at app startup)
    await init_redis_pool()
    
    if redis_pool is None:
        print("Failed to initialize pool, cannot run tests.")
        return

    test_user_id = "test_user_123"
    test_session_id = "test_session_abc"
    test_context_data = {"message_history": ["Hello", "How are you?"], "current_phase": "REFLECT"}

    # Test save
    print(f"\nAttempting to save context for user {test_user_id}, session {test_session_id}...")
    save_success = await save_agent_context(test_user_id, test_session_id, test_context_data, ttl=60)
    print(f"Save successful: {save_success}")

    # Test load
    if save_success:
        print(f"\nAttempting to load context for user {test_user_id}, session {test_session_id}...")
        loaded_context = await load_agent_context(test_user_id, test_session_id)
        print(f"Load successful: {loaded_context is not None}")
        if loaded_context:
            print(f"Loaded data: {loaded_context}")
            assert loaded_context == test_context_data

    # Test load non-existent
    print(f"\nAttempting to load non-existent context...")
    non_existent_context = await load_agent_context("non_existent_user", "non_existent_session")
    print(f"Load non-existent successful (should be None): {non_existent_context is None}")
    assert non_existent_context is None

    # Test delete
    if save_success:
        print(f"\nAttempting to delete context for user {test_user_id}, session {test_session_id}...")
        delete_success = await delete_agent_context(test_user_id, test_session_id)
        print(f"Delete successful: {delete_success}")
        
        # Try loading again to confirm deletion
        print(f"Attempting to load deleted context...")
        deleted_context = await load_agent_context(test_user_id, test_session_id)
        print(f"Load deleted context successful (should be None): {deleted_context is None}")
        assert deleted_context is None

    # Close pool (normally done at app shutdown)
    await close_redis_pool()
    print("\nRedis client test finished.")

if __name__ == "__main__":
    # This allows running `python -m backend.redis_client` to test the functions.
    # Ensure you have a Redis server running locally for this test.
    asyncio.run(main_test())
