
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import socket
import json
import threading

class Client:

    def __init__(self, HOST, PORT):

        self.name = inquirer.text(message='What is your username?').execute()

        self.client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
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
                "action": "join_Topic",
                "Topic_name": topic
            }).encode())

            response = self.client_socket.recv(4096).decode()
            join_data = json.loads(response)

            if join_data.get("status") == "joined":
                self.current_topic = topic
                print(f"Joined topic: {topic}")

                for msg in join_data.get("messages", []):
                    print(msg)

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
            "action": "create_Topic",
            "Topic_name": new_subject
        }).encode())

        response = self.client_socket.recv(4096).decode()
        print(response)

        self.client_socket.sendall(json.dumbs({
            "action": "join_Topic",
            "Topic_name": new_subject
        }).encode())

        join_response = json.loads(self.client_socket.recv(4096).decode())
        print("Joined: " +  join_response)

        self.current_topic = new_subject
        self.openChatRoom()


    def openChatRoom(self):
        threading.Thread(target=self.receiveMessage).start()

        while True:
            chat = inquirer.select(
                choices=[
                    'Send message',
                    'Stop following topic',
                    Choice(value=None, name='Return main menu')
                ],
                default=1
            ).execute()

            if chat == 'Send message':
                self.sendMessage()
            elif chat == 'Stop following topic':
                self.leaveTopic()
                break
            else:
                break


    def sendMessage(self):
        message = inquirer.text(
            message='Type message'
        ).execute()


        self.client_socket.sendall(json.dumps({
            "action": "send_Topic_message",
            "Topic_name": self.current_topic,
            "message": message
        }).encode())


    def receiveMessage(self):
        
        while True:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break

                message = json.loads(data.decode())

                if message.get("type") == "Topic_message":
                    print(
                        f"\n[{message['Topic_name']}] "
                        f"{message['from']}: {message['message']}"
                    )
            except:
                break

    def leaveTopic(self):
        self.client_socket.sendall(json.dumps({
            "action": "leave_Topic",
            "Topic_name": self.current_topic
        }).encode())

        response = self.client_socket.recv(4096).decode()
        print(response)

if __name__ == '__main__':
    Client('localhost', 12347)
