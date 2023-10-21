from keep_alive import keep_alive
import os
import praw
import schedule
import time
import threading
from pymongo import MongoClient
import random

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

memes = [
  '### Shaddap 3%', '### nirlajj tu fir aa gya', '### Teri Keh Ke Lunga',
  '### Behti hai nadi girta hai jharna,\n\n ee meowdalchod apna kaam karna',
  '### pel dunga'
]

optoutReplies = [
  '### Ab aapka username bas dil mai aayega, mere replies mai nhi',
  '### Accha chalta huu, duaaoon mai yaad rakha, mujhe dekhte hi upvote pe haath rakhna',
  '### Sorry ji ab hum karenge aapko ignore, itni jaldi kyo ho gye aap humse bore'
]

optinReplies = [
  '### Tera mujhse tha pehle ka naata koi, yuhi thodi wapas bulata koi',
  '### Dooba Dooba rehta tha yaadon mei teri, wapas aa gya hu ab replies mai teri',
  '### koi chahe, chahta rhe, mushil hai humko bhulana\n\n ### hum aa gye, andaaz leke purana'
]

verdicts = {
  (201, 1000): "Mr/Mrs Vellaverse",
  (121, 201): "Legendary Vella",
  (101, 121): "Expert Vella",
  (81, 101): "Bohot Vella",
  (61, 81): "Vella",
  (41, 61): "Thodusa Vella",
  (21, 41): "Biji",
  (1, 21): "Very Biji",
  (0, 0): 'Lmao ded'
}

query_month = [i[:3] for i in month]


def clearData():
  db = MClient["2023"]
  db["limit"].delete_many({})


def reset():
  schedule.every().day.at("12:00").do(clearData)
  while True:
    schedule.run_pending()
    time.sleep(1)


def query():
  db = MClient["2023"]
  for comment in comments:
    post = reddit.submission(id=comment.submission).title
    if comment.body.lower().find(trigger) != -1:
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
      if query_count > 15:
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
        reply = 'Top 5 Vellas in ' + text[1] + ': \n\n'
        reply += 'User|Comments Count\n:-:|:-:\n'
        for m in month:
          if text[1][:3].lower() == m[:3]:
            ignore_collection = db["ignore"]
            users_to_ignore = [
              user['_id'] for user in ignore_collection.find()
            ]
            data = db[m].find({
              "user": {
                "$nin": users_to_ignore
              }
            }).sort("comments", -1).limit(5)
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
        if 'vellabot' in user:
          reply = random.choices(memes, k=1)
          try:
            comment.reply(reply)
          except:
            continue
          continue
      if_ignored = db['ignore'].find({'_id': {"$in": user}})
      if if_ignored.count() > 0:
        continue
      total_comments = 0
      current_month = 0
      for i in range(0, 12):
        data = db[month[i]].find()
        flag = 0
        for entry in data:
          flag = 1
        if flag == 0:
          break
        current_month = i
      count = 0
      for i in range(0, current_month - 2):
        data = db[month[i]].find()
        flag = 0
        for entry in data:
          flag = 1
          if entry['user'].lower() in user:
            count += entry['comments']
      if current_month - 3 >= 0:
        reply += 'Till ' + month[current_month -
                                 3].capitalize()[:3] + '|' + str(count) + '\n'
      for i in range(current_month - 2, current_month + 1):
        data = db[month[i]].find()
        count = 0
        flag = 0
        for entry in data:
          flag = 1
          if entry['user'].lower() in user:
            count += entry['comments']
        total_comments = count
        reply += month[i].capitalize()[:3] + '|' + str(count) + '\n'

      average = total_comments // total_days
      verdict = 'Lmao ded'
      for range_, result in verdicts.items():
        lower, upper = range_
        if lower <= average <= upper:
          verdict = result
          break
      reply += '\nAvg no of Comments/Day made by ' + user[
        0] + ' in this month: ' + str(average) + '\n\n\
            Verdict: ' + verdict
      try:
        reply += '\n\n^([How to use.](https://www.reddit.com/r/vellabot/comments/10fd998/launching_lnrdt_vellabot))'
        comment.reply(reply)
      except:
        continue


def reply():
  unread_replies = reddit.inbox.stream()
  for unread_reply in unread_replies:
    try:
      unread_reply.mark_read()
    except:
      continue
    if 'delete' in unread_reply.body.lower():
      try:
        deleting_user = unread_reply.author
        bot_comment = reddit.comment(unread_reply.parent_id.split('_')[-1])
        parent_comment = reddit.comment(
          bot_comment.parent_id.split('_')[-1]).author
        if parent_comment == deleting_user:
          comment = bot_comment
          comment.delete()
      except:
        continue
    elif '!optout' in unread_reply.body.lower():
      try:
        user = unread_reply.author
        db = MClient["2023"]
        db["ignore"].insert_one({'_id': str(user)})
        reply = 'You have unsubscribed from vellabot, your name will no longer show up in any of my replies.\n\n'
        reply += "".join(random.choices(optoutReplies, k=1))
        unread_reply.reply(reply)
      except:
        continue
    elif '!optin' in unread_reply.body.lower():
      try:
        user = unread_reply.author
        db = MClient["2023"]
        db["ignore"].delete_one({'_id': str(user)})
        reply = 'You have subscribed back to vellabot, your name _might_ show up in _some_ of my replies.\n\n'
        reply += "".join(random.choices(optinReplies, k=1))
        unread_reply.reply(reply)
      except:
        continue


process1 = threading.Thread(target=query)
process2 = threading.Thread(target=reply)
process3 = threading.Thread(target=reset)
process1.start()
process2.start()
process3.start()
