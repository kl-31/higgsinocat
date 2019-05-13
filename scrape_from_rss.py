import feedparser
#import csv
#import string
from unidecode import unidecode
import json
from os.path import isfile
import helpers

if isfile('feed_info.txt'):
	feed_info = json.load(open("feed_info.txt"))
else:
	feed_info = {

					}

written = 0
posted = 0
while written == 0:
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
			row = [[unidecode(entry.title), entry.link, feed_name, entry.description]] # 2D array of size (1,3)
			if row[0][0] not in titles_list:
				proba_out = helpers.compute_proba(row)
				#print(proba_out)
				helpers.write_to_db(proba_out)
				written = written + 1
				if proba_out[-1] >=0.5:
					handles = helpers.get_author_handles(entry.authors)
					if helpers.tweet_post('%s (relevance: %.0f%%) %s #darkmatter %s' % (entry.title, proba_out[-1]* 100,entry.link,handles)):
							posted = posted + 1
	#			elif proba_out[-1] < 0.5 and (feed_name == 'Biomedical Optics Express' or feed_name == 'Journal of Biophotonics'):
	#				if helpers.tweet_post('%s (relevance: %.0f%% but this is in %s so my model probably meowssed up) %s #biophotonics #biomedicaloptics' % (entry.title, proba_out[-1]* 100, feed_name, entry.link)):
	#						posted = posted + 1
					
			if posted >=46: # 46/2 hours elapsed  
			   break
		if posted >=46: # 46/2 hours elapsed  
			break
				#print('%d: %s' % (i,row[0]))
	print('%d rows written.' % written)
	print('%d tweets posted.' % posted)