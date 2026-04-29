# This file is meant for testing storage server connection functionality.

import xmlrpc.client
from datetime import datetime, timezone

storage_proxy = xmlrpc.client.ServerProxy("http://localhost:8080/")

def insert_message(topic_name, username, msg):
  timestamp = datetime.now(timezone.utc)

  storage_proxy.set_message({
    "timestamp": timestamp.isoformat(),
    "topic_name": topic_name,
    "username": username,
    "message": msg
  })


def get_topics(target):
  topics = {}
  old_messages = storage_proxy.get_messages()
  for content in old_messages:
    _id, timestamp, topic_name, username, message = content


    if topic_name not in topics:
      topics[topic_name] = {
        "name": topic_name,
        "messages": []
      }
    # add message to correct topic
    topic = topics[topic_name]["messages"].append({
        "timestamp": timestamp,
        "username": username,
        "message": message,
    })

  if target == "":
    print(topics)
  else:
    print(topics.get(target))
  return topics


if __name__=="__main__":
  # insert_message()
  get_topics("")
