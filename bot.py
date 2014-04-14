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
        if bug_assignee_link is not None:
            self.assignee = bug_assignee_link[31:] # only use the username part
        else:
            self.assignee = None
        self.url = bug_url

    def get_summary(self):
        summary = ""
        if self.assignee is not None:
            summary = self.linkify(self.assignee, '~') + " fixed " + self.linkify(self.title, 'bug')
        else:
             summary = "We fixed " + self.linkify(self.title, "bug")

        return summary

    def linkify(self, link, link_type):
        if link_type == "~":
            return "pad.lv/~" + link
        elif link_type == "bug":
            return link.replace("Bug #", "pad.lv/")
        else:
            return link


class LaunchpadFetcher:
    def __init__(self, consumer):
        # the API is stateless so loging in once is enough
        lp = Launchpad.login_anonymously(config.bot_name, "production", config.lp_cache_dir)

        # we are only interested in elementary bugs
        self.project = lp.projects[config.lp_project]

        self.last_checked = datetime.utcnow()

        self.consumer = consumer

    def fetch(self):
        print "Searching for bugs after " + str(self.last_checked)
        bugs = self.project.searchTasks(modified_since=self.last_checked)
        
        for bug in bugs:
            if bug.status == 'Fix Released' or bug.status == 'Fix Committed':
                # Get the required details
                bug_title = bug.title
                bug_url = bug.bug_link
                bug_assignee_link = bug.assignee_link

                bug_info_obj = BugInfo(bug_title, bug_assignee_link, bug_url)

                # send it to the consumer
                self.consumer.send(bug_info_obj)


    def run(self):
        while True:
            try:
                print "Fetching " + str(datetime.now())
                self.fetch()

                time.sleep(config.sleep_time)

                self.last_checked = datetime.utcnow()
            except Exception, e:
                print "Error occured"
                print e
                break


class TwitterUpdater:
    def __init__(self):
        self.twitter_api = twitter.Api(consumer_key = config.consumer_key,
                                       consumer_secret = config.consumer_secret,
                                       access_token_key = config.access_token_key,
                                       access_token_secret = config.access_token_secret)
            
    def consumer(self):
        while True:
            bug = yield
            if bug is not None:
                print "Tweeting about bug " + bug.title + " at time " + str(datetime.now())
                self.twitter_api.PostUpdate(bug.get_summary())

def main():
    tweeter = TwitterUpdater().consumer()
    tweeter.send(None)
    
    fetcher = LaunchpadFetcher(tweeter)

    fetcher.run()

if __name__ == "__main__":
    main()
