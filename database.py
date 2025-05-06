import asyncpg
import os

async def create_pool():
    """Create and return a connection pool for the PostgreSQL database."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    return await asyncpg.create_pool(database_url)

async def initialize_database(pool):
    """Initialize the PostgreSQL database."""
    async with pool.acquire() as conn:
        # Existing table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id BIGINT PRIMARY KEY,
                points INT DEFAULT 0
            );
        """)
        
        # New tryouts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tryouts (
                tryout_id SERIAL PRIMARY KEY,
                host_id BIGINT NOT NULL,
                cohost_id BIGINT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                participants JSONB NOT NULL DEFAULT '{}'::jsonb,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    print("✅ Database initialized successfully.")