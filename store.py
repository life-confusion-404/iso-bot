import praw
from pymongo import MongoClient
import os
from keep_alive import keep_alive

USER_AGENT=os.environ['user_agent']
CLIENT_ID=os.environ['client_id']
CLIENT_SECRET=os.environ['client_secret']
USERNAME=os.environ['bot_id']
PASSWORD=os.environ['bot_secret']

CONNECTION_STRING=os.environ['conn_str']

MClient = MongoClient(CONNECTION_STRING)
SUBREDDIT = "indiasocial"

def entry(user, month):
    db = MClient["2023"]
    col = db[month]
    comments=1
    if col.count_documents({'user':user}) > 0:
        data=col.find_one( { "user": user } )
        col.delete_one({'user':user})
        comments=data['comments']+1
    col.insert_one({'user':user, 'comments':comments})

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD,
                     user_agent=USER_AGENT)

subreddit = reddit.subreddit(SUBREDDIT)
keep_alive()
comments = subreddit.stream.comments()
months = ["january", "february", "march", "april", "may", "june", "july", "august", 
        "september","october", "november", "december"]
for comment in comments:
    post =reddit.submission(id=comment.submission).title
    if post.find("Random Discussion Thread")!=-1 and post.find("2023")!=-1:
        for month in months:
            if post.lower().find(month)!=-1 and post.find("2023"):
                entry(str(comment.author), month)
                break
   
