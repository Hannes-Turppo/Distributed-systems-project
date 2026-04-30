#!/usr/bin/python
import psycopg2
from config import config
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
from threading import Lock


class ThreadingXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
  daemon_threads = True
  allow_reuse_address = True

 
# connect to PostgreSQL and return connection
def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        
        # create a cursor
        cursor = conn.cursor()

    # execute a statement
        print('PostgreSQL database version:')
        cursor.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cursor.fetchone()
        print(db_version)

        return (conn, cursor)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None


def create_table(cur):
  cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
      id SERIAL PRIMARY KEY,
      timestamp TIMESTAMP DEFAULT NOW(),
      topic_name VARCHAR(255),
      username VARCHAR(255),
      message TEXT
    )
  """)
  return


# Write all new messages into DB so they can be fetched on server startup
def set_message(cur, conn, message):
  try:
    cur.execute(
        "INSERT INTO messages (timestamp, topic_name, username, message) VALUES (%s, %s, %s, %s)",
        (message.get("timestamp"), message.get("topic_name"), message.get("username"), message.get("message"))
    )
    conn.commit()
    return True
  except Exception as e:
    print(f"Error inserting message: {e}")
    return e


# get all messages from DB and return the to the main server as 
# dict of topics as keys and other data as values
def get_messages(cur):
  cur.execute('SELECT * FROM messages')
  data = cur.fetchall()
  return data

# Disconnect from PostgreSQL
def disconnect(conn, cursor):
  try:
    cursor.close()
    conn.close()
    print("Disconnected from DB")
  except Exception as e:
    print(f"Error while closing DB connection: {e}")


if __name__ == '__main__':
  # PostgreSQL connection
  connection = connect()
  if connection == None:
    print("failed to connect to DB. Exiting.")
    exit(1)

  (db, cursor) = connection
  create_table(cur=cursor)
  db.commit()

  # define server
  server = ThreadingXMLRPCServer(("localhost", 8080))

  # server functions
  server.register_function(lambda: get_messages(cursor), "get_messages")
  server.register_function(lambda message: set_message(cursor, db, message), "set_message") # gets message from main server.

  # serve
  print("Listening on port 8080...")
  server.serve_forever()
  disconnect(db, cursor)
