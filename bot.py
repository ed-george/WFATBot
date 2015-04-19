import praw
import re
import signal
import sys
import time
from credentials import REDDIT_USERNAME, REDDIT_PASS

r = praw.Reddit('desktop:wfatBot:0.1 (by /u/edgeorge92)')
r.login(REDDIT_USERNAME, REDDIT_PASS)

subreddit = r.get_subreddit('WaitingForATrain')

already_done = []
with open('previous.txt', 'r') as f:
    for i in f:
        already_done.append(i.replace("\n", ""))


def bot_main():
    for submission in subreddit.get_new(limit=5):
        id = submission.id
        if id not in already_done:
            print submission.title
            search = 'title:'
            title = re.sub("\[.*\]", "", submission.title)
            title = re.sub("-.*", "", title)
            search += title.lower().replace("station", "").strip()
            print search
            previous = []
            for search_submission in r.search(search, subreddit='WaitingForATrain'):
                if search_submission.id != id:
                    previous.append(search_submission)
            if len(previous) > 0:
                print 'Posting comment on %s (link: %s)' % (id, submission.permalink)
                submission.add_comment(comment(previous))
            already_done.append(id)


def comment(list):
    formatted_comment = 'It looks like other members of WFAT have been to this station previously!' \
                        '\n\nWhy not also check out these related submissions:\n\n'
    for submission in list:
        formatted_comment += '+ [%s](%s)\n' % (submission.title, submission.permalink)
    formatted_comment += '\n^^WFATBot ^^is ^^an ^^experimental ^^bot ^^by ^^/u/edgeorge92'
    return formatted_comment


def signal_handler(signal, frame):
    write_done()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


def write_done():
    with open("previous.txt", "w") as f:
        for i in already_done:
            f.write(str(i) + '\n')

while True:
    time.sleep(5)
    bot_main()
    time.sleep(5)
    write_done()
    time.sleep(100)
