import re
import signal
import sys

import time
import sqlite3
import praw
import log_color as log
from time import strftime
from credentials import REDDIT_USERNAME, REDDIT_PASS

__version__ = "0.1"
DEBUG = True

# Warning if debug mode is enabled
if DEBUG:
    log.warning("DEBUG MODE ENABLED")

# Connect to Sqlite3 Database
try:
    log.verbose("=> Connecting to DB")
    con = sqlite3.connect('wfat.db')
    # Create database table if not exists
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS wfat_posts("
                    "id INTEGER PRIMARY KEY,"
                    " author TEXT, post_id TEXT,"
                    " permalink TEXT, title TEXT, url TEXT)")
except sqlite3.Error, e:
    log.error("Error %s:" % e.args[0])
    sys.exit(1)


# Close cursor and connection to database
def db_disconnect():
    if con:
        log.warning("\n=> Disconnecting from DB")
        cur.close()
        con.close()


# Connect to reddit with correctly formatted User-Agent
r = praw.Reddit('desktop:wfat:%s (by /u/edgeorge92)' % (__version__,))
try:
    log.verbose("=> Connecting to Reddit")
    r.login(REDDIT_USERNAME, REDDIT_PASS)
except Exception, e:
    log.error("Error %s:" % e.args[0])
    log.error("Connection error - Could not connect to Reddit")
    db_disconnect()
    sys.exit(1)

# Access subreddit
log.verbose("<= Receiving subreddit info /r/WaitingForATrain")
subreddit = r.get_subreddit('WaitingForATrain')


# Check if post id has been accessed and saved previously
def has_completed(post_id):
    with con:
        cur.execute("SELECT * FROM wfat_posts WHERE post_id = ?", (post_id,))
        log.verbose("Checking completion of %s" % post_id)
        return len(cur.fetchall()) > 0


# Add submission information to database
def complete(submission):
    with con:
        cur.execute("INSERT INTO wfat_posts VALUES(NULL,?,?,?,?,?)",
                    (submission.author.name, submission.id, submission.permalink, submission.title, submission.url))
        log.success("Completed %s" % submission.id)


# Main functionality of bot
def bot_main():
    # Get latest 5 posts from subreddit
    for submission in subreddit.get_new(limit=5):
        # Check if post has not been checked previously
        if not has_completed(submission.id):
            log.success("<= Submission: %s" % submission.title)
            search_title = 'title:'
            # Remove formatting from title
            title = re.sub("\[.*\]", "", submission.title)
            title = re.sub("-.*", "", title)
            # Generate subreddit title search
            search_title += title.lower().replace("station", "").strip()
            log.verbose("=> Searching: %s" % search_title)

            # Stored search results
            relevant_previous_submissions = []
            # Get search results for generated search title
            for searched_submission in r.search(search_title, subreddit='WaitingForATrain'):
                # If a search result is found, that is not the same as the base post
                # add it to the list of relevant submissions
                if searched_submission.id != submission.id:
                    log.success("<= found relevant post: %s" % searched_submission.id)
                    relevant_previous_submissions.append(searched_submission)\

            # If any relevant submissions were found, add comment to base post
            if len(relevant_previous_submissions) > 0:
                if not DEBUG:
                    log.verbose("=> Posting comment on %s (link: %s)" % (submission.id, submission.permalink))
                    submission.add_comment(comment(relevant_previous_submissions))
                else:
                    log.warning("DEBUG MODE: Comment would be posted on %s (link: %s)"
                                % (submission.id, submission.permalink))
            # Add base post to database
            complete(submission)
        # Submission has been previously added to database
        else:
            log.warning("\tPreviously completed %s" % submission.id)
    log.verbose("-- Sleeping @ %s --" % strftime("%d/%m/%Y %H:%M:%S"))


# Define comment to post
def comment(submission_list):
    formatted_comment = 'It looks like members of /r/WaitingForATrain have been to this station previously!' \
                        '\n\nWhy not also check out these related submissions:\n\n'
    for submission in submission_list:
        formatted_comment += '+ [%s](%s)\n' % (submission.title, submission.permalink)
    formatted_comment += '\n*If you believe this was posted in error - please message the mods*' \
                         '\n\n^^WFATBot ^^is ^^an ^^experimental ^^bot ^^by ^^/u/edgeorge92'
    return formatted_comment


# Gracefully handle program killed by SIGINT (Ctrl+C)
def signal_handler(signal, frame):
    db_disconnect()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


# Main Bot Loop
while True:
    time.sleep(5)
    bot_main()
    time.sleep(115)