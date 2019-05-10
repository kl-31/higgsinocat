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
			'optica': 
				{'name':'Optica', 
				 'path': 'http://metadata.osa.org/rss/infobase/optica_feed.xml',
				 'etag':''},
			 'lsa':
				 {'name': 'Light: Science and Applications',
				'path': 'http://feeds.nature.com/lsa/rss/current?fmt=xml',
				  'etag': ''},
			  'nat_photon':
				  {'name':'Nature Photonics',
				   'path': 'http://www.nature.com/nphoton/journal/vaop/ncurrent/rss.rdf',
				   'etag': ''},
			'oe':
				{'name': 'Optics Express',
					 'path': 'http://metadata.osa.org/rss/infobase/opex_feed.xml',
					 'etag': ''},
				'boe':
					{'name': 'Biomedical Optics Express',
					  'path': 'http://metadata.osa.org/rss/infobase/boe_feed.xml',
					  'etag': ''},
				'ol':
					{'name': 'Optics Letters',
					  'path': 'http://metadata.osa.org/rss/infobase/ol_feed.xml',
					  'etag': ''},
				'nat_meth':
					{'name': 'Nature Methods',
						'path': 'http://www.nature.com/nmeth/journal/vaop/ncurrent/rss.rdf',
						'etag': ''},
				'nat_bme':
					{'name': 'Nature BME',
						  'path': 'http://feeds.nature.com/natbiomedeng/rss/current?fmt=xml',
						  'etag': ''},
					'science':
					{'name': 'Science',
						  'path': 'http://science.sciencemag.org/rss/express.xml',
						  'etag': ''},
					'nat_comms':
					{'name': 'Nature Communications',
						  'path': 'http://feeds.nature.com/ncomms/rss/current?fmt=xml',
						  'etag': ''},
					  'science_advances':
					{'name': 'Science Advances',
						  'path': 'https://advances.sciencemag.org/rss/current.xml',
						  'etag': ''}
					}

written = 0
posted = 0
titles_list = helpers.get_titles_db()
for feed in feed_info.keys():	
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
				if helpers.tweet_post('%s (relevance: %.0f%%) %s #biophotonics #biomedicaloptics' % (entry.title, proba_out[-1]* 100,entry.link)):
						posted = posted + 1
			elif proba_out[-1] < 0.5 and (feed_name == 'Biomedical Optics Express' or feed_name == 'Journal of Biophotonics'):
				if helpers.tweet_post('%s (relevance: %.0f%% but this is in %s so my model probably meowssed up) %s #biophotonics #biomedicaloptics' % (entry.title, proba_out[-1]* 100, feed_name, entry.link)):
						posted = posted + 1
				
		if posted >=22: # 22 hours elapsed  
		   break
	if posted >=22: # 22 hours elapsed  
		break
			#print('%d: %s' % (i,row[0]))
print('%d rows written.' % written)
print('%d tweets posted.' % posted)