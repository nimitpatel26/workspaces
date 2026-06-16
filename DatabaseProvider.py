

from datetime import datetime, timezone
import os
import psycopg
from psycopg.rows import dict_row

"""
DB Operations:
* Check if short URL exists.
* Add in short URL.
* Get the long URL mapping.
* Return metadata.
* Delete record.
"""

class DatabaseProvider:

    def __init__(self):
        # 1. Fetch from environment variable, falling back to None if not set
        self.DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING")
        
        # 2. Add an explicit safety check to fail quickly if config is missing
        if not self.DB_CONNECTION_STRING:
            raise ValueError("Critical Configuration Error: DB_CONNECTION_STRING environment variable is not set.")

    def test_conn(self, dsn=None):
        dsn = self.DB_CONNECTION_STRING
        if not dsn:
            raise SystemExit("Set DATABASE_URL environment variable (e.g. postgres://user:pass@host:5432/dbname)")
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                print("OK, got:", cur.fetchone()[0])

    def create_urls_table(self):
        # SQL statement to create the table if it does not already exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS urls (
            user_id UUID NOT NULL,
            short_url TEXT NOT NULL UNIQUE,
            long_url TEXT NOT NULL,
            creation_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            expire_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            access_count INT DEFAULT 0
        );
        """
        
        try:
            # 2. Establish connection to the PostgreSQL database
            # Using a context manager automatically closes the connection when done
            with psycopg.connect(self.DB_CONNECTION_STRING) as conn:
                
                # 3. Open a cursor to perform database operations
                with conn.cursor() as cur:
                    
                    # Execute the SQL command
                    cur.execute(create_table_query)
                    
                    # Psycopg v3 enables autocommit by default for structural commands,
                    # but explicit connection management handles transaction blocks.
                    print("Table 'urls' created successfully!")
                    
        except Exception as e:
            print(f"An error occurred while creating the table: {e}")

    def drop_urls_table(self):
        # SQL command to permanently delete the table and all its rows
        drop_query = "DROP TABLE IF EXISTS urls;"
        
        try:
            # Establish connection to the PostgreSQL database
            with psycopg.connect(self.DB_CONNECTION_STRING) as conn:
                with conn.cursor() as cur:
                    
                    print("Attempting to drop table 'urls'...")
                    cur.execute(drop_query)
                    print("Table 'urls' has been permanently deleted.")
                    
        except Exception as e:
            print(f"An error occurred while dropping the table: {e}")

    def insert_sample_url(self, user_id, short_url, long_url, expire_time=None):
        # SQL parameterized query to prevent SQL injection vulnerabilities
        insert_query = """
        INSERT INTO urls (user_id, short_url, long_url, creation_time, expire_time, access_count)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        # Generate current UTC timestamp and set initial count
        current_time = datetime.now(timezone.utc)
        expire_time = expire_time if expire_time else datetime.max
        initial_count = 0
        
        try:
            # Establish connection to the PostgreSQL database
            with psycopg.connect(self.DB_CONNECTION_STRING) as conn:
                with conn.cursor() as cur:
                    
                    # Execute query passing parameters securely as a tuple
                    cur.execute(insert_query, (user_id, short_url, long_url, current_time, expire_time, initial_count))
                    
                    print(f"Successfully inserted sample short URL: {short_url}")
                    
        except Exception as e:
            print(f"An error occurred while inserting data: {e}")

    def get_all_urls(self):
        # SQL query to select all fields from the table
        select_query = "SELECT user_id, short_url, long_url, creation_time, expire_time, access_count FROM urls;"
        
        try:
            # Establish connection to the PostgreSQL database
            with psycopg.connect(self.DB_CONNECTION_STRING) as conn:
                with conn.cursor() as cur:
                    
                    # Execute the selection query
                    cur.execute(select_query)
                    
                    # Retrieve all rows from the executed cursor buffer
                    rows = cur.fetchall()
                    
                    print(f"--- Total Records Found: {len(rows)} ---\n")
                    
                    # Loop through and print each individual record
                    for row in rows:
                        print(f"User ID:      {row[0]}")
                        print(f"Short URL:    {row[1]}")
                        print(f"Long URL:     {row[2]}")
                        print(f"Created At:   {row[3]}")
                        print(f"Expire At:    {row[4]}")
                        print(f"Access Count: {row[5]}")
                        print("-" * 40)
                        
        except Exception as e:
            print(f"An error occurred while fetching data: {e}")

    def find_url_metadata(self, short_url: str) -> dict | None:
        # SQL query to strictly read data without updating anything
        query = """
        SELECT user_id, short_url, long_url, creation_time, expire_time, access_count 
        FROM urls 
        WHERE short_url = %s;
        """
        
        try:
            # Open connection and specify row_factory=dict_row to get a dictionary back
            with psycopg.connect(self.DB_CONNECTION_STRING, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    
                    # Execute securely using parameterization
                    cur.execute(query, (short_url,))
                    
                    # Fetch the returned row (returns None if no match is found)
                    metadata = cur.fetchone()
                    
                    return metadata
                        
        except Exception as e:
            print(f"Database error occurred: {e}")
            return None
        
    def increment_access_count(self, short_url: str) -> dict | None:
        # SQL query to increment the count and return the updated metadata
        query = """
        UPDATE urls 
        SET access_count = access_count + 1
        WHERE short_url = %s
        RETURNING short_url, long_url, access_count;
        """
        
        try:
            # Open connection and use dict_row to get a dictionary response
            with psycopg.connect(self.DB_CONNECTION_STRING, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    
                    # Execute securely using parameterization
                    cur.execute(query, (short_url,))
                    
                    # Fetch the updated row data
                    updated_row = cur.fetchone()
                    
                    return updated_row
                        
        except Exception as e:
            print(f"Database error occurred: {e}")
            return None


# db_provider = DatabaseProvider()
# create_urls_table()
# insert_sample_url("123e4567-e89b-12d3-a456-426614174000", "short1", "https://www.example.com/long-url-1")
# db_provider.get_all_urls()
# print(db_provider.find_url_metadata("short2"))
# drop_urls_table()