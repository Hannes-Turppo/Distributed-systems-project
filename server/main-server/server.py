import xmlrpc.client
import socket
import threading
import json
from redis import Redis
import json
import time



# Redis cache handling
class RedisCache:
  def __init__(self, host='localhost', port=6379, db=0, forward_callback=None):
    try:
      # init redis components
      self.redis = Redis(host=host, port=port, db=db, decode_responses=True)
      self._stop_event = threading.Event()

      # populate with data from storage
      self.populate_cache()

    except Exception as e:
      print(f"Error initializing redis connection: {e}")


# pull old content from database to cache
  def populate_cache(self):
    old_data = storage_proxy.get_data()
    print(old_data)
    keys = old_data.keys()
    for topic in keys:
      self.redis.set(topic.name, topic.messages)
    return


# set_topic to redis cache for fast acces for new joiners and store into permanent storage.
  def set_topic(self, storage, topicName, content):
    try:
      self.redis.set(topicName, content)
      storage_proxy.set_data(topics)
      return True
    except Exception as e:
      print(f"Error while setting topic: {e}")
      return False


# when client connects to topic, get old messages from redis
  def get_topic(self, topicName):
    try:
      topic = self.redis.get(topicName)
      if not topic:
        return False
      else:
        return topic
    except Exception as e:
      print(f"Error while getting topic from Redis: {e}")
      return False
  

class Topic:
  def __init__(self, name):
    self.name = name
    self.messages = [] # List of messages in given topic
    self.members = [] # List of socket connections in the chatroom

  def add_message(self, username, message):
    try:
      timestamp = time.time()
      self.messages.append({
        "from": username,
        "message": message,
        "timestamp": timestamp
      })
      return True
    except Exception as e:
      print(f"Error while adding message to topic: {e}")
      return False

  def get_messages(self):
    return self.messages

  def add_member(self, username):
    if username not in self.members:
      self.members.append(username)
    return True



# Handle commands from stdin.
def commands(server):
  global running # Use global variable
  while running:
    try:
      command = input().strip()
      if command == "/h":
         print("Available commands:")
         print("- /h        List available commands")
         print("- /exit     Shut down the server\n")
      elif command == "/exit":
        print("Shutting down the server.")
        running = False
        server.close()
      else:
         print("Unknown command. Try again or type \"/h\" for help")
    except EOFError:
      break
    except Exception as error:
      print(f"Command error: {error}")


# handle RPC calls to NewsServer
def handle_news(keyword):
  # code goes here
  return


# function to handle incoming client requests
# server accepts following actions:
# "list_topics"
# "create_topic"
# "join_topic"
# "send_topic_message"
# "leave_topic"
def handle_client_request(userName, conn, cache, message):
  try:
    command = json.loads(message)
    action = command.get("action")


    # Topic functionality
    if action == "list_topics":
      groups = list(cache.keys()) # Get all current channels from Redis and return them to client
      conn.sendall(json.dumps({"topics": groups}).encode())


    # create a new topic
    if action == "create_Topic":
      name = command.get("Topic_name")

      if name in topics:
        conn.sendall(b"Error: Topic already exists.")
      else:
        topics[name] = Topic(name)
        topics[name].add_member(userName)
        conn.sendall(json.dumps({"status": "created", "Topic_name": name}).encode())
        print(f"Topic '{name}' created by {userName}")


    # Join existing topic
    if action == "join_Topic":
      name = command.get("Topic_name")
      Topic = topics.get(name)
      if not Topic:
        conn.sendall(json.dumps({"status": "error", "message": "Topic not found"}).encode())
        return
      
      # Add user to Topic members
      Topic.add_member(userName)

      # Send Topic history
      response = json.dumps({
        "status": "joined",
        "Topic_name": name,
        "messages": Topic.get_messages(),
        "members": Topic.members
      })
      conn.sendall(response.encode())
      print(f"{userName} joined Topic '{name}'")


    # Send a message to existing topic
    if action == "send_Topic_message":
      Topic_name = command.get("Topic_name")
      msg = command.get("message")
      
      Topic = topics.get(Topic_name)
      if not Topic:
        conn.sendall(b"Error: Topic not found.")
        return
      
      # Add message to Topic history
      Topic.add_message(userName, msg)
      cache.set_topic(Topic_name, Topic)

      # Broadcast to all Topic members
      message_data = json.dumps({
        "type": "Topic_message",
        "Topic_name": Topic_name,
        "from": userName,
        "message": msg
      })
      
      with locking:
        for member in Topic.members:
          if member in clients and member != userName:
            try:
              clients[member].sendall(message_data.encode())
            except Exception as e:
              print(f"Failed to send message to {member}: {e}")


    # Exit a topic's subscriber list
    if action == "leave_Topic":
      Topic_name = command.get("Topic_name")
      Topic = topics.get(Topic_name)
      if Topic and userName in Topic.members:
        Topic.members.remove(userName)
        print(f"{userName} left Topic '{Topic_name}'")
      conn.sendall(b"Left Topic")


    # Use news microservice to search news by keyword
    if action == "search_news":
      keyword = command.get("keyword")
      handle_news(keyword)


  except Exception as error:
    conn.sendall(b"Internal server error.")
    print(f"Error {error} from command {action}")
  return



# main handler for client connections
def handle_client(conn, addr):
  global running
  userName = None

  try:
    data = conn.recv(1024)
    if not data:
      return
    userName = data.decode().strip()

    # connect user to socket
    with locking:
      if userName not in clients:
        clients[userName] = conn
        conn.send(b"OK")
        print(f'User {userName} connected @ {addr[0]}, {addr[1]}')
      else:
        conn.sendall(b"Username already in use.")
        return  # Added: Don't continue if username is taken

    while running:
      # connection functionality
      data = conn.recv(1024)
      if not data:
        with locking:  # Added lock
          if userName in clients:
            del clients[userName]
        print(f"User {userName} disconnected.")
        break

      msg = data.decode().strip()
      handle_client_request(userName, conn, msg)

  except (ConnectionResetError, BrokenPipeError) as error:
    print(f"Connection error from {addr}: {error}")
  finally:  # connection cleanup on closure
    with locking:
      if userName and userName in clients:
        del clients[userName]
    print(f"Cleaned up connection for {userName}")


# define socket. creates a listening socket and handles incoming connections
def define_socket(hostname, ip, PORT):
  global running

  with socket.create_server(("", PORT), family=socket.AF_INET6, backlog=5, reuse_port=True, dualstack_ipv6=True) as server:
    print(f"Server listening on {hostname} @ {ip}:{PORT}")
    print("Use \"/exit\" to shut down server")

    #start command handler
    command_handler = threading.Thread(target=commands, args=(server,), daemon=True)
    command_handler.start()

    while running:
      try:
        server.settimeout(1)  #timeout checks if server is running
        conn, addr = server.accept()

        # start new thread for each new connection
        client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        client_thread.start()

      except socket.timeout:
        continue # Check if timed out
      except OSError:
        if not running:
          break
        raise
      except Exception as error:
        print(f"Server error: {error}")
        continue


# Server state
running = True
locking = threading.Lock()
clients = {}  # Dict: k: username, v: socket connection
topics = {}   # Dict: k: topicname, v: list of messages
cache = RedisCache()
storage_proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")



# main server 
def server():
  # host options
  hostname = socket.gethostname()
  ip=socket.gethostbyname(hostname)
  PORT = 12347

  define_socket(hostname, ip, PORT)




if __name__=="__main__":  
  server()
