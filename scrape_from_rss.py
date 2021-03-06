import feedparser
#import csv
#import string
from unidecode import unidecode
import json
from os.path import isfile
import helpers
from time import sleep
import datetime
import numpy as np


if isfile('feed_info.txt'):
	feed_info = json.load(open("feed_info.txt"))
else:
	feed_info = {

					}

time = 3 * 60 # 3 hours
interval = 30 # minutes
written = np.zeros(len(feed_info.keys()),dtype=np.int)
posted = np.zeros(len(feed_info.keys()),dtype=np.int)
attempts = 0

twit_handles =helpers.pull_handles_from_twitter(['higgsinocat','Xenon1T','luxdarkmatter','CelineBoehm1'])

# check if any one of the feeds has been empty. not just all empty
while sum(written) == 0 and not (datetime.datetime.today().weekday()==5 or datetime.datetime.today().weekday()==6) and attempts < 10:
	n_feed = 0
	for feed in feed_info.keys():	
		titles_list = helpers.get_titles_db()
		#print(feed)
		feed_name = feed_info[feed]['name']
		feed_path = feed_info[feed]['path']
		feed_rss = feedparser.parse(feed_path)
		for i in range(len(feed_rss.entries)):
			entry = feed_rss.entries[i]
			abstract = feed_rss.entries[i].summary[3:-4].replace('\n',' ')
			row = [[unidecode(entry.title), abstract, entry.link, feed_name]] # 2D array of size (1,3)
			
			if row[0][0] not in titles_list:
				proba_out = helpers.compute_proba(row)
				#print(row)
				#print(proba_out)
				helpers.write_to_db(proba_out)
				written[n_feed] = written[n_feed] + 1
				#print(proba_out)
				if proba_out[-1] >=0.3:
					handles = helpers.get_author_handles(entry.authors, unidecode(entry.title), twit_handles)
					title = entry.title
					if len(title) > 150:
						title = title[:150] + '...'
					if helpers.tweet_post('%s relevance:%.0f%% %s #darkmatter %s' % (title, proba_out[-1]* 100,entry.link,handles),helpers.scrape_image(entry.link),interval):
							posted[n_feed] = posted[n_feed] + 1
				
			if sum(posted) >=int(time/interval-1): # 46/4 hours elapsed  
			   break
		if sum(posted) >=int(time/interval-1): # 46/4 hours elapsed  
			break
				#print('%d: %s' % (i,row[0]))
		sleep(1)
		n_feed = n_feed +1
	print('%d rows written.' % sum(written))
	print('%d tweets posted.' % sum(posted))
	attempts = attempts + 1

	sleep(10*60)
	
while datetime.datetime.today().weekday()==5 or datetime.datetime.today().weekday()==6:
	helpers.retweet_old(int(time/interval-1),interval)
	