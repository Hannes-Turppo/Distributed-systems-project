import requests

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

    return content

if __name__ == '__main__':
    getNews('tesla')
