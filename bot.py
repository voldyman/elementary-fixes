#!/bin/python

try:
    import settings as config
except Exception, e:
    print("To run this bot you need to provide the API tokens in the settings")

from launchpadlib.launchpad import Launchpad
from Queue import Queue
from datetime import datetime
import time
import threading
import twitter



class BugInfo:
    def __init__(self, bug_title, bug_assignee_link, bug_url):
        self.title = bug_title
        self.assignee= bug_assignee_link[31:] # only use the username part
        self.url = bug_url

    def get_summary(self):
        summary = ""
        if self.assignee is not None:
            summary = self.linkify(self.assignee, '~') + " fixed " + self.linkify(self.title, 'bug')
        else:
             summary = "We fixed " + self.linkify(self.title)

        return summary

    def linkify(self, link, link_type):
        if link_type == "~":
            return "pad.lv/~" + link
        elif link_type == "bug":
            return link.replace("Bug #", "pad.lv/")
        else:
            return link


class LaunchpadFetcher(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        # use this to send data
        self.queue = queue

        # the API is stateless so loging in once is enough
        lp = Launchpad.login_anonymously(config.bot_name, "production", config.lp_cache_dir)

        # we are only interested in elementary bugs
        self.project = lp.projects[config.lp_project]

        self.last_checked = datetime.utcnow()

    def fetch(self):
        bugs = self.project.searchTasks(status=config.bug_type)

        for bug in bugs:
            release_date = bug.date_fix_released.replace(tzinfo=None)

            if release_date > self.last_checked:
                # Get the required details
                bug_title = bug.title
                bug_url = bug.bug_link
                bug_assignee_link = bug.assignee_link

                bug_info_obj = BugInfo(bug_title, bug_assignee_link, bug_url)

                # put it on the queue
                self.queue.put(bug_info_obj)

    def run(self):
        while True:
            try:
                print "Fetching"
                self.fetch()

                time.sleep(config.sleep_time)

                self.last_checked = datetime.utcnow()
            except:
                self.queue.put(None)
                break

class TwitterUpdater:
    def __init__(self, queue):
        self.twitter_api = twitter.Api(consumer_key = config.consumer_key,
                                       consumer_secret = config.consumer_secret,
                                       access_token_key = config.access_token_key,
                                       access_token_secret = config.access_token_secret)

        self.queue = queue

    def poll(self):
        while True:
            obj = self.queue.get()

            if obj is None:
                break

            print("Tweeting about bug " + obj.title)
            self.twitter_api.PostUpdate(obj.get_summary())

def main():
    # make a queue for communication
    queue = Queue()

    fetcher = LaunchpadFetcher(queue)
    tweeter = TwitterUpdater(queue)

    fetcher.start()
    tweeter.poll()

if __name__ == "__main__":
    main()
