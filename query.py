from keep_alive import keep_alive
import os
import praw
import schedule
import time
import threading
from pymongo import MongoClient

USER_AGENT = os.environ['user_agent']
CLIENT_ID = os.environ['client_id']
CLIENT_SECRET = os.environ['client_secret']
USERNAME = os.environ['username']
PASSWORD = os.environ['password']

CONNECTION_STRING = os.environ['conn_str']

MClient = MongoClient(CONNECTION_STRING)
SUBREDDIT = "indiasocial"

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     username=USERNAME,
                     password=PASSWORD,
                     user_agent=USER_AGENT)

subreddit = reddit.subreddit(SUBREDDIT)
comments = subreddit.stream.comments(skip_existing=True)

trigger = "!vellabot"
keep_alive()
month = [
  "january", "february", "march", "april", "may", "june", "july", "august",
  "september", "october", "november", "december"
]
query_month = [i[:3] for i in month]


def clearData():
  db = MClient["2023"]
  db["limit"].delete_many({})


schedule.every().day.at("12:00").do(clearData)


def reset():
  while True:
    schedule.run_pending()
    time.sleep(1)


def query():
  db = MClient["2023"]
  curr_time=""
  for comment in comments:
    post = reddit.submission(id=comment.submission).title

    if post.find("Random Discussion Thread") != -1 and comment.body.lower().find(trigger) != -1 and (curr_time == "" or curr_time < comment.created_utc):
      text = comment.body
      text = text[comment.body.lower().find(trigger):]
      text = text.split(' ')
      query_count = 1

      ### Rate Limit
      request_user = str(comment.author)
      if db["limit"].count_documents({'user': request_user}) > 0:
        data = db["limit"].find_one({"user": request_user})
        query_count = data['count'] + 1
        db["limit"].delete_one({'user': request_user})
      db["limit"].insert_one({'user': request_user, 'count': query_count})
      if query_count > 20:
        continue
      ### Rate Limit

      total_days = 1
      
      words = post.split(' ')
      for word in words:
        try:
          total_days = int(word)
          break
        except:
          continue
      if len(text) > 1 and (text[1].lower() in query_month):
        reply = 'User|Comments Count\n:-:|:-:\n'
        for m in month:
          if text[1][:3].lower() == m[:3]:
            data = db[m].find().sort("comments", -1).limit(5)
            for i in data:
              reply += i['user'] + '|' + str(i['comments']) + '\n'
        try:
          reply += '\n\n^([How to use.](https://www.reddit.com/r/vellabot/comments/10fd998/launching_lnrdt_vellabot))'
          comment.reply(reply)
          continue
        except:
          continue
      reply = 'Month|Comments Count\n:-:|:-:\n'
      user = [str(comment.author).lower()]
      if len(text) > 1:
        user = text[1]
        user = user.lower()
        user = user.split('+')
      total_comments = 0
      for i in range(12):
        data = db[month[i]].find()
        count = 0
        flag = 0
        for entry in data:
          flag = 1
          if entry['user'].lower() in user:
            count += entry['comments']
        if flag:
          total_comments = count
          reply += month[i].capitalize()[:3] + '|' + str(count) + '\n'

      average = total_comments // total_days
      verdict = "Lmao ded"
      if average > 120:
        verdict = "Legendary Vella"
      elif average > 100:
        verdict = "Expert Vella"
      elif average > 80:
        verdict = "Bohot Vella"
      elif average > 60:
        verdict = "Vella"
      elif average > 40:
        verdict = "Thodusa Vella"
      elif average > 20:
        verdict = "Biji"
      elif average > 0:
        verdict = "Very Biji"

      reply += '\nAvg no of Comments/Day made by ' + user[
        0] + ' in this month: ' + str(average) + '\n\n\
            Verdict: ' + verdict
      try:
        reply += '\n\n^([How to use.](https://www.reddit.com/r/vellabot/comments/10fd998/launching_lnrdt_vellabot))'
        comment.reply(reply)
      except:
        continue


process1 = threading.Thread(target=query)
process2 = threading.Thread(target=reset)

process1.start()
process2.start()
