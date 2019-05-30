import feedparser
#import csv
#import string
from unidecode import unidecode
import json
from os.path import isfile
import helpers
from time import sleep
import re
import datetime
import numpy as np

if isfile('feed_info.txt'):
	feed_info = json.load(open("feed_info.txt"))
else:
	feed_info = {

					}

written = np.zeros(len(feed_info.keys()),dtype=np.int)
posted = np.zeros(len(feed_info.keys()),dtype=np.int)
attempts = 0

# check if any one of the feeds has been empty. not just all empty
while np.count_nonzero(written) < len(feed_info.keys()) and not (datetime.datetime.today().weekday()==5 or datetime.datetime.today().weekday()==6) and attempts < 72:
	n_feed = 0
	for feed in feed_info.keys():	
		titles_list = helpers.get_titles_db()
		#print(feed)
		feed_name = feed_info[feed]['name']
		feed_path = feed_info[feed]['path']
		feed_rss = feedparser.parse(feed_path)
	#	feed_etag = feed_info[feed]['etag']
	#	if feed_etag == '':
	#		feed_rss = feedparser.parse(feed_path)
	#		feed_etag = feed_rss.etag
	#		feed_info[feed]['etag'] = feed_rss.etag
	#	else:
	#		feed_rss = feedparser.parse(feed_path, etag=feed_etag)
	#		
	#	if feed_rss.status == 304:
	#		#print('No new items in %s since last update.' % feed_name)
	#		continue
	#	else:
			#print('Number of RSS posts : %d' % len(feed_rss.entries))	
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
					handles = helpers.get_author_handles(entry.authors, unidecode(entry.title))
					title = entry.title
					if len(title) > 160:
						title = title[:160] + '...'
					if helpers.tweet_post('%s relevance:%.0f%% %s #darkmatter %s' % (title, proba_out[-1]* 100,entry.link,handles),helpers.scrape_image(entry.link)):
							posted[n_feed] = posted[n_feed] + 1
	#			elif proba_out[-1] < 0.5 and (feed_name == 'Biomedical Optics Express' or feed_name == 'Journal of Biophotonics'):
	#				if helpers.tweet_post('%s (relevance: %.0f%% but this is in %s so my model probably meowssed up) %s #biophotonics #biomedicaloptics' % (entry.title, proba_out[-1]* 100, feed_name, entry.link)):
	#						posted = posted + 1
					
			if sum(posted) >=46: # 46/2 hours elapsed  
			   break
		if sum(posted) >=46: # 46/2 hours elapsed  
			break
				#print('%d: %s' % (i,row[0]))
		sleep(1)
		n_feed = n_feed +1
	print('%d rows written.' % sum(written))
	print('%d tweets posted.' % sum(posted))
	attempts = attempts + 1

	sleep(5*60)