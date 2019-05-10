
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 13:50:39 2019

@author: liangkc
"""

# you need to install Biopython:
# pip install biopython

# Full discussion:
# https://marcobonzanini.wordpress.com/2015/01/12/searching-pubmed-with-python/

from Bio import Entrez
from xml.etree.ElementTree import iterparse
import csv
import time
import datetime
import urllib.request as libreq
import feedparser
from unidecode import unidecode



def search(query,retmax):
	Entrez.email = 'your.email@example.com'
	handle = Entrez.esearch(db='pubmed', 
							sort='relevant', 
							retmax=str(retmax),
							retstart = '10',
							retmode='xml', 
							#reldate = '3650',
							term=query)
	results = Entrez.read(handle)
	return results

def fetch_details(id_list):
	ids = ','.join(id_list)
	Entrez.email = 'your.email@example.com'
	handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
	results = Entrez.read(handle)
	return results

if __name__ == '__main__':
	chunk_size = 50
#	# PUBMED QUERY
#	groups = [['physics', 'biology','engineering'],
#			   ['biomedical optics', 'biophotonics','biology optics','optical biomedical microscopy']]
	start = time.time()
	with open('dmcat_data.csv', mode='w') as data_file:
		file_writer =  csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#		for group in groups:
#			retmax = 15000
#			for query in group:
#				num = 0
#				results = search(query,retmax)
#				id_list = results['IdList']
#				
#				for chunk_i in range(0, len(id_list), chunk_size):
#					chunk = id_list[chunk_i:chunk_i + chunk_size]
#					try:
#						papers = fetch_details(chunk)
#						for i, paper in enumerate(papers['PubmedArticle']):
#							file_writer.writerow([unidecode(paper['MedlineCitation']['Article']['ArticleTitle']), str(2*groups.index(group))])
#							num = num+1
#					except:
#						pass
#					#print('%d titles written.' % min(int(chunk_i + chunk_size), len(id_list)))
#				print('%d titles saved in %s.' % (num,query))
	
	# ARXIV QUERY
		num=0
		for chunk_i in range(0, 30000, chunk_size):
			feed = feedparser.parse('http://export.arxiv.org/api/query?search_query=cat:astro-ph&start=%d&max_results=%d' % (chunk_i,chunk_size))
			
			for i in range(len(feed.entries)):
				entry = feed.entries[i]
				title = (entry.title).replace('\n', "")
				file_writer.writerow([unidecode(title), str(0)])
				num = num+1
		print('%d titles saved from Arxiv astro-ph.' % num)	
		num=0
		for chunk_i in range(0, 30000, chunk_size):
			feed = feedparser.parse('http://export.arxiv.org/api/query?search_query=all:dark+AND+all:matter&start=%d&max_results=%d' % (chunk_i,chunk_size))
			
			for i in range(len(feed.entries)):
				entry = feed.entries[i]
				title = (entry.title).replace('\n', "")
				file_writer.writerow([unidecode(title), str(1)])
				num = num+1
		print('%d titles saved from Arxiv search of \'dark matter\'.' % num)		
	
	
	end = time.time()
	print('Time elapsed: %s' % datetime.timedelta(seconds=round(end - start)))
	data_file.close()
#		for i, paper in enumerate(papers['PubmedArticle']):
#			#file_writer.writerow([paper['MedlineCitation']['Article']['ArticleTitle'], '1'])
#			print("%d) %s" % (i+1, paper['MedlineCitation']['Article']['ArticleTitle']))