import re
import signal
import sys

import time
import sqlite3
import praw
import log_color as log
from time import strftime
from credentials import REDDIT_USERNAME, REDDIT_PASS

try:
    log.verbose("-> Connecting to DB")
    con = sqlite3.connect('wfat.db')
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS wfat_posts("
                    "id INTEGER PRIMARY KEY,"
                    " author TEXT, post_id TEXT,"
                    " permalink TEXT, title TEXT, url TEXT)")
except sqlite3.Error, e:
    log.error("Error %s:" % e.args[0])
    sys.exit(1)

r = praw.Reddit('desktop:wfat:0.1 (by /u/edgeorge92)')
try:
    r.login(REDDIT_USERNAME, REDDIT_PASS)
except Exception, e:
    log.error("Error %s:" % e.args[0])
    log.error("Connection error - Could not connect to Reddit")
    sys.exit(1)

log.verbose("-> Connecting to Reddit")
subreddit = r.get_subreddit('WaitingForATrain')


def db_disconnect():
    if con:
        log.warning("\n-> Disconnecting from DB")
        con.close()


def has_completed(id):
    with con:
        cur.execute("SELECT * FROM wfat_posts WHERE post_id = ?", (id,))
        log.verbose("Checking completion of %s" % id)
        return len(cur.fetchall()) > 0


def complete(submission):
    with con:
        cur.execute("INSERT INTO wfat_posts VALUES(NULL,?,?,?,?,?)",
                    (submission.author.name, submission.id, submission.permalink, submission.title, submission.url))
        log.success("Completed %s" % submission.id)


def bot_main():
    for submission in subreddit.get_new(limit=5):
        if not has_completed(submission.id):
            log.success("<- Submission: %s" % submission.title)
            search = 'title:'
            title = re.sub("\[.*\]", "", submission.title)
            title = re.sub("-.*", "", title)
            search += title.lower().replace("station", "").strip()
            log.verbose("-> Searching: %s" % search)
            relevant_previous_submissions = []
            for searched_submission in r.search(search, subreddit='WaitingForATrain'):
                if searched_submission.id != submission.id:
                    log.success("<- found relevant post: %s" % searched_submission.id)
                    relevant_previous_submissions.append(searched_submission)
            if len(relevant_previous_submissions) > 0:
                log.verbose("-> Posting comment on %s (link: %s)" % (id, submission.permalink))
                # submission.add_comment(comment(relevant_previous_submissions))
            complete(submission)
        else:
            log.warning("Previously completed %s" % submission.id)
    log.verbose("-- Sleeping @ %s --" % strftime("%d/%m/%Y %H:%M:%S"))


def comment(submission_list):
    formatted_comment = 'It looks like members of /r/WaitingForATrain have been to this station previously!' \
                        '\n\nWhy not also check out these related submissions:\n\n'
    for submission in submission_list:
        formatted_comment += '+ [%s](%s)\n' % (submission.title, submission.permalink)
    formatted_comment += '\n*If you believe this was posted in error - please message the mods*' \
                         '\n\n^^WFATBot ^^is ^^an ^^experimental ^^bot ^^by ^^/u/edgeorge92'
    return formatted_comment


def signal_handler(signal, frame):
    db_disconnect()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


# Main Loop
while True:
    time.sleep(5)
    bot_main()
    time.sleep(115)