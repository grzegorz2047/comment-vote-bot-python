import pprint
from pick import pick
# initialize Hive class
from beem import Hive
from beem.discussions import Query, Discussions
from datetime import datetime
import configparser
import schedule
import time
from beem.account import Account
from beem.vote import ActiveVotes
from beem.transactionbuilder import TransactionBuilder
from beembase.operations import Vote
import getpass

h = Hive()
q = Query(limit=2, tag="")
d = Discussions()
config = configparser.ConfigParser()
config.read('settings.ini')

postingKey = config['DEFAULT']['postingKey']
author = config['DEFAULT']['authorToVoteComment']
voter = config['DEFAULT']['voterName']
weight = int(config['DEFAULT']['weight'])

posts = d.get_discussions('created', q, limit=2)
client = Hive('https://api.hive.blog/')


def vote(voter, author, permlink, weight):
  
  
  try:
    tx = TransactionBuilder(blockchain_instance=client)
    tx.appendOps(Vote(**{
      "voter": voter,
      "author": author,
      "permlink": permlink,
      "weight": int(float(weight) * 100)
    }))

    #wif_posting_key = getpass.getpass('Posting Key: ')
    tx.appendWif(postingKey)
    signed_tx = tx.sign()
    broadcast_tx = tx.broadcast(trx_id=True)

    print("Vote cast successfully: " + str(broadcast_tx))
  except Exception as e:
    print('\n' + str(e) + '\nException encountered.  Unable to vote')

def get_comments_to_vote(author, voter):
  # 5 comments from selected author
  q = Query(limit=20, start_author=author) 

  # get comments of selected account
  comments = d.get_discussions('comments', q, limit=20)
  minPostLifeInMinutes = int(config['DEFAULT']['minPostLifeInMinutes'])
  maxMinutes = 7
  now = datetime.now().astimezone()
  commentsToVote = []
  # print comment details for selected account
  for comment in comments:
    comment_created_time = comment['created']
    diff = now - comment_created_time
    minutes = divmod(diff.total_seconds(), 60) 
    minutes = minutes[0]

    if minutes >= minPostLifeInMinutes and minutes < maxMinutes:
      votes = comment['active_votes']
      for vote in votes:
        if vote['voter'] != voter:
          commentsToVote.append(comment)
          break
  return commentsToVote


def main():
  print("I'm on my duty, sir!")

  commentsToVote = get_comments_to_vote(author, voter)
  number_of_comments_to_vote = len(commentsToVote)
  if number_of_comments_to_vote == 0:
    print("No comments to vote")
  else:
    print(number_of_comments_to_vote)


  for commentToVote in commentsToVote:
    permlink = commentToVote['permlink']
    vote(voter, author, permlink, weight)


checkSecondsInterval = int(config['DEFAULT']['checkSecondsInterval'])
schedule.every(checkSecondsInterval).seconds.do(main)
while True:
    schedule.run_pending()
    time.sleep(1)
