# Distributed-systems-project
Final project for DS course.

## Description
This project includes a CLI interface, that users can use to search for news about anything, and chat about them.

## Infrastructure
### Frontend: python CLI client 
Easy to use, modern interactive CLI client, that includes the following functionality:
- Search for news by keywords
- Create and view topics based on found news stories
- Engage in live chats with other users
- Connects to server by TCP-sockets

### Backend: Main server and microservices
- Main server
    - Receives and handles client TCP-socket connections
    - Maintains available topics and chatrooms to provide live updates to connected clients
    - Uses XMLRPC microservices to provide additional functionality
- News microservice
    - XMLRPC2 proxy
    - Handles requests to NewsAPIv2 to get news.
- Storage microservice
    - Threaded XMLRPC proxy
    - Maintains connection to PostgreSQL database
    - Handles saving new messages to DB
    - Pulls old messages from DB when server is started

## Instructions
