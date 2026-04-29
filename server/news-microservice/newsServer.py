from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import requests
import json

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2')

with SimpleXMLRPCServer(('localhost', 8000),
                        requestHandler=RequestHandler) as server:
    server.register_introspection_functions

    def getNews(topic):
        
        url = ('https://newsapi.org/v2/everything?'
            'q={topic}&'
            'sortBy=popularity&'
            'pageSize=10&'
            'language=en&'
            'apiKey=1b5bb8dd11604a898ca733c287980a53'
            )
        
        response = requests.get(url)
        content = response.json()

        
        if content.get('status') == 'error':
            print(content.get('code'))
            return 'Error: unable to get news.'


        newslist = []

        for article in content.get('articles', []):
            newslist.append({
                "source": article['source']['name'],
                "title": article['title'],
                "description": article['description'],
                "publishTime": article['publishedAt']
            })

        return newslist


    server.register_function(getNews, 'getNews')

    server.serve_forever()

if __name__ == '__main__':
    RequestHandler()
    
