import xmlrpc.client
import socket
import threading
import json
from datetime import datetime, timezone


class Topic:
  def __init__(self, name):
    self.name = name
    self.messages = [] # List of messages in given topic
    self.members = [] # List of socket connections in the chatroom

  def add_message(self, timestamp, username, message):
    try:
      self.messages.append({
        "username": username,
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
    else:
      return False




# Handle commands from stdin on the server.
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
         print("Unknown command. Try again or type \"/h\" for help\n")
    except EOFError:
      break
    except Exception as error:
      print(f"Command error: {error}")


# handle RPC calls to NewsServer
def handle_news(keyword):
  with xmlrpc.client.ServerProxy("http://localhost:8000/RPC2") as proxy:
    news = proxy.getNews(keyword)
  return news


# function to handle incoming client requests
# server accepts following actions:
# "list_topics"
# "create_topic"
# "join_topic"
# "send_topic_message"
# "leave_topic"
# "search_news"
def handle_client_request(username, conn, message):
  try:
    command = json.loads(message)
    action = command.get("action")


    # Topic functionality
    if action == "list_topics":
      groups = list(topics.keys()) # Get all current channels and return them to client
      conn.sendall(json.dumps({"topics": groups}).encode())


    # create a new topic
    if action == "create_topic":
      name = command.get("topic_name")

      if name in topics:
        conn.sendall(b"Error: Topic already exists.")
      else:
        topics[name] = Topic(name)
        topics[name].add_member(username)
        conn.sendall(json.dumps({"status": "created", "topic_name": name}).encode())
        print(f"Topic '{name}' created by {username}")


    # Join existing topic
    if action == "join_topic":
      name = command.get("topic_name")
      if name not in topics.keys():
        conn.sendall(json.dumps({"status": "error", "message": "Topic not found"}).encode())
        return
      topic = topics.get(name)
      
      # Add user to topic members
      topic.add_member(username)

      # Send topic history
      response = json.dumps({
        "status": "joined",
        "topic_name": name,
        "messages": topic.get_messages(),
        "members": topic.members
      })
      conn.sendall(response.encode())
      print(f"{username} joined topic '{name}'")


    # Send a message to existing topic
    if action == "send_topic_message":

      # form message data
      topic_name = command.get("topic_name")
      msg = command.get("message")
      timestamp = datetime.now(timezone.utc).isoformat()

      # find topic
      topic = topics.get(topic_name)
      if not topic:
        conn.sendall(b"Error: Topic not found.")
        return

      # Add message to server memory and persistent message history
      topic.add_message(timestamp, username, msg)
      res = storage_proxy.set_message({
        "timestamp": timestamp,
        "topic_name": topic_name,
        "username": username,
        "message": msg
      })
      if res is not True:
        print(f"Microservice error while saving message: {res}")

      # Broadcast to all topic members
      message_data = json.dumps({
        "type": "topic_message",
        "timestamp": timestamp,
        "topic_name": topic_name,
        "username": username,
        "message": msg
      })
      with locking:
        for member in topic.members:
          if member in clients and member != username:
            try:
              clients[member].sendall(message_data.encode())
            except Exception as e:
              print(f"Failed to send message to {member}: {e}")
          else:
            print(f"Error sending message to {member}: client not found.")


    # Exit a topic's subscriber list
    if action == "leave_topic":
      topic_name = command.get("topic_name")
      topic = topics.get(topic_name)
      if topic and username in topic.members:
        topic.members.remove(username)
        print(f"{username} left topic '{topic_name}'")
      conn.sendall(json.dumps({"status": "left", "topic_name": topic_name}))


    # Use news microservice to search news by keyword
    if action == "search_news":
      keyword = command.get("topic_name")
      news = handle_news(keyword)
      if news == False:
        conn.sendall(json.dumps({"status": "error", "content": ""}).encode())
      else:
        conn.sendall(json.dumps({"status": "OK", "content": news}).encode())


  except Exception as error:
    conn.sendall(b"Internal server error.")
    print(f"Error {error} from command {action}")
  return



# main handler for client connections
def handle_client(conn, addr):
  global running
  username = None

  try:
    data = conn.recv(1024)
    if not data:
      return
    username = data.decode().strip()

    # connect user to socket
    with locking:
      if username not in clients:
        clients[username] = conn
        conn.send(b"OK")
        print(f'User {username} connected @ {addr[0]}, {addr[1]}')
      else:
        conn.sendall(b"Username already in use.")
        return  # Don't continue if username is taken

    while running:
      # connection functionality
      request = conn.recv(1024)
      if not request:
        with locking:  # Added lock
          if username in clients:
            del clients[username]
        print(f"User {username} disconnected.")
        break

      message = request.decode().strip()
      handle_client_request(username, conn, message)

  except (ConnectionResetError, BrokenPipeError) as error:
    print(f"Connection error from {addr}: {error}")
  finally:  # connection cleanup on closure
    with locking:
      if username and username in clients:
        del clients[username]
    print(f"Cleaned up connection for {username}")



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


# Use storage proxy to retrieve old messages from former server instances
def restore_topics():
  topics = {}
  old_messages = storage_proxy.get_messages()
  for content in old_messages:
    _id, timestamp, topic_name, username, message = content


    # if topic doesn't exist, create it
    if topic_name not in topics:
      topics[topic_name] = Topic(topic_name)
    # add message to correct topic
    topics[topic_name].add_message(
        timestamp = timestamp,
        username = username,
        message = message
    )
  return topics



# Server state
running = True
locking = threading.Lock()
clients = {}  # Dict: k: username, v: socket connection
topics = {}   # Dict: k: topicname, v: list of messages
storage_proxy = xmlrpc.client.ServerProxy("http://localhost:8080/")



# main server 
def server():
  # host options
  hostname = socket.gethostname()
  ip=socket.gethostbyname(hostname)
  PORT = 12347

  global topics
  try:
    topics = restore_topics()
  except Exception as e:
    print(f"Warning: failed to load topics from storage proxy: {e}")
    topics = {}
  define_socket(hostname, ip, PORT)




if __name__=="__main__":  
  server()
