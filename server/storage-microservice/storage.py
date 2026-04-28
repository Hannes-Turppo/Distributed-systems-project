#!/usr/bin/python
import psycopg2
from config import config
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
from threading import Lock
import json


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

        return cursor
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

def set_data(cur, data):
  for line in data:
    pass
  return

def get_data(cur):
  data = cur.execute('SELECT * FROM topics')
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
  cursor = connect()
  # define server
  server = ThreadingXMLRPCServer(("localhost", 8000))

  # server functions
  server.register_function(get_data(cursor), "get_data")
  server.register_function(set_data(cursor), "set_data")

  # serve
  print("Listening on port 8000...")
  server.serve_forever()
  disconnect(db, cursor)
