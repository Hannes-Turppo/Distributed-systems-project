
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import socket
import json
import threading

class Client:

    def __init__(self, HOST, PORT):
        # handle receiver thread and it's shutdown
        self.stop_receiving = threading.Event()
        self.receiver_thread = None

        self.name = inquirer.text(message='What is your username?').execute()

        self.client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.client_socket.settimeout(1)
        try:
            self.client_socket.connect((HOST, PORT))
            self.client_socket.send(self.name.encode())
            self.client_socket.recv(1024)
        except ConnectionRefusedError:
            print("Error connecting server.")
        except Exception as err:
            print(err)

        self.Menu()

        

    def Menu(self):

        while True:
            main_menu = inquirer.select(
                message='Welcome to newsHub',
                choices=[
                    'Find new subject',
                    'Open subjects',
                    Choice(value=None, name='Exit'),
                ],
                default=1,
            ).execute()

            if main_menu == 'Find new subject':
                self.NewSubject()
            elif main_menu == 'Open subjects':
                self.OpenSubjects()
            else:
                self.client_socket.close()
                break

    def OpenSubjects(self):

        topics = self.GetOpenNews()
        
        if not topics:
            print('No open topics available')
            return
        
        topics.append(Choice(value=None, name='Return main menu'))

        while True:
            topic = inquirer.select(
                message='Open topics',
                choices=topics,
                default=1
            ).execute()

            if topic is None:
                break
            
            self.client_socket.sendall(json.dumps({
                "action": "join_topic",
                "topic_name": topic
            }).encode())

            response = self.client_socket.recv(4096).decode()
            join_data = json.loads(response)

            if join_data.get("status") == "joined":
                self.current_topic = topic
                print(f"Joined topic: {topic}\n")

                # print message history
                print("------ Message history ------")
                for msg in join_data.get("messages", []):
                    print(f"{msg.get("username")}: {msg.get("message")}")
                print("------ Message history ------")

                self.openChatRoom()
                break

            else:
                print('Failed to join topic.')


    def GetOpenNews(self):
        ## NewsList where open chats from database

        self.client_socket.sendall(json.dumps({"action": "list_topics"}).encode())

        response = self.client_socket.recv(4096).decode()
        data = json.loads(response)

        return data.get("topics", [])
    
    def NewSubject(self):

        new_subject = inquirer.text(message='Find new subject').execute()                

        self.client_socket.sendall(json.dumps({
            "action": "search_news",
            "topic_name": new_subject
        }).encode())

        # process server response
        response = self.client_socket.recv(4096).decode()
        data = json.loads(response)
        newsList = data["content"]

        if data["status"] and data["status"] == "error":
            print(f'Error while receiving news')
            return
        else:
            choices = [
                Choice(
                    value=article,
                    name=f"Source: {article['source']}\nTitle: {article['title']}"
                )
                for article in newsList
            ]

            choices.append(Choice(value=None, name='Return main menu'))

            while True:

                select_article = inquirer.select(
                    message="Select article of your topic",
                    choices=choices,
                    default=1
                ).execute()

                if select_article is None:
                    return
                else:

                    selected_article = inquirer.select(
                        message=f"Source {select_article['source']}\nTitle: {select_article['title']}\nPublish time: {select_article['publishTime']}\nDescription: {select_article['description']}",
                                    choices=[
                                        'Open chat room',
                                        Choice(value=None, name='Return article list')
                                    ],
                                    default=1
                    ).execute()

                    if selected_article != None:
                        
                        self.client_socket.sendall(json.dumps({
                        "action": "create_topic",
                        "topic_name": new_subject
                        }).encode())

                        join_response = json.loads(self.client_socket.recv(4096).decode())
                        print(join_response)

                        self.current_topic = new_subject
                        self.openChatRoom()


    # handle stopping the message receiver thread
    def stopReceiverThread(self):
        self.stop_receiving.set()
        if self.receiver_thread and self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout=1)


    def openChatRoom(self):
        self.stop_receiving.clear()
        self.receiver_thread = threading.Thread(target=self.receiveMessage, daemon=True)
        self.receiver_thread.start()

        while True:
            chat = inquirer.select(
                message='Chat options',
                choices=[
                    'Send message',
                    Choice(value=None, name='Return main menu')
                ],
                default=1
            ).execute()

            if chat == 'Send message':
                self.sendMessage()
            else:
                self.stopReceiverThread()
                self.leaveTopic()
                break


    def sendMessage(self):
        message = inquirer.text(
            message='Type message'
        ).execute()


        self.client_socket.sendall(json.dumps({
            "action": "send_topic_message",
            "topic_name": self.current_topic,
            "message": message
        }).encode())

    def receiveMessage(self):
        while not self.stop_receiving.is_set():
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break

                message = json.loads(data.decode())

                if message.get("type") == "topic_message":
                    print(
                        f"\n[{message['topic_name']}] "
                        f"{message['username']}: {message['message']}"
                    )
            except socket.timeout:
                continue
            except:
                break

    def leaveTopic(self):
        self.client_socket.sendall(json.dumps({
            "action": "leave_topic",
            "topic_name": self.current_topic
        }).encode())

        response = self.client_socket.recv(4096).decode()
        print(response)

        return

if __name__ == '__main__':
    Client('localhost', 12347)
