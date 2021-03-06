# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 05:28:51 2019

@author: KCLIANG
Helper functions for biophotobot.
"""
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.externals import joblib
import pandas as pd
import numpy as np
from unidecode import unidecode
import string
import json
from os.path import isfile
from os import environ
import tweepy
from time import sleep
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fuzzywuzzy import fuzz
import re
import urllib.request
import patoolib
from shutil import rmtree
import os
import glob
from random import choice
from imageio import imwrite
from subprocess import call
import html2text
import datetime
import fitz

#import bitly_api
#import sys

scopes = ['https://spreadsheets.google.com/feeds',
	  'https://www.googleapis.com/auth/drive']
keyfile_dict = {
    'auth_provider_x509_cert_url': environ['GSPREAD_AUTH_PROVIDER'],
    'auth_uri': environ['GSPREAD_AUTH_URI'],
    'client_email': environ['GSPREAD_CLIENT_EMAIL'],
    'client_id': environ['GSPREAD_CLIENT_ID'],
    'client_x509_cert_url': environ['GSPREAD_CLIENT_X509'],
    'private_key': environ['GSPREAD_PRIVATE_KEY'].replace('\\n', '\n'),
    'private_key_id': environ['GSPREAD_PRIVATE_KEY_ID'],
    'project_id': environ['GSPREAD_PROJECT_ID'],
    'token_uri': environ['GSPREAD_TOKEN_URI'],
    'type': environ['GSPREAD_TYPE']
}


def get_titles_db():
	#print(keyfile_dict)
	creds = ServiceAccountCredentials.from_json_keyfile_dict(
    keyfile_dict=keyfile_dict, scopes=scopes)
	#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
	while 1:
		try:
			client = gspread.authorize(creds)
			break
		except:
			sleep(60)
			continue	
	sh = client.open_by_key('1DHGj_3CybB2hewWu8XsUbFer6iUcaLHBLjtGM9YHUIw')
	worksheet = sh.sheet1
	titles_list = worksheet.col_values(1)
	sleep(1)	
	return titles_list

def write_to_db(row_to_write):
	creds = ServiceAccountCredentials.from_json_keyfile_dict(
    keyfile_dict=keyfile_dict, scopes=scopes)
	#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
	while 1:
		try:
			client = gspread.authorize(creds)
			break
		except:
			sleep(60)
			continue	
	sh = client.open_by_key('1DHGj_3CybB2hewWu8XsUbFer6iUcaLHBLjtGM9YHUIw')
	worksheet = sh.sheet1
	#row_to_write.append(str(datetime.date.today())) #append is problematic
	worksheet.insert_row(row_to_write+[str(datetime.date.today())] ,1)
	sleep(1) # google api 60 write requests per 60 sec
	return None


def normalize_text(s):
	s=''.join([i for i in s if not i.isdigit()]) # remove numbers
	s = s.replace('-',' ')
	s = s.replace('/',' ')
	s = s.replace('μ','u')
	s = unidecode(str(s))
	s=s.translate(s.maketrans('', '', string.punctuation)) # remove punctuation
	s = s.lower() # make lowercase
	s = s.replace('  ',' ') # remove double spaces
	s = s.strip() # strip leading and trailing whitespace
	return s

def compute_proba(titles):
	vectorizer = HashingVectorizer(ngram_range=(1, 3))
	
	titles = pd.DataFrame(titles,columns=['title','abstract','link','journal_name'])
	titles['text'] = [normalize_text(re.sub(r'\([^()]*\)', '', str(s))) for s in titles['title']+' '+titles['abstract']] 
	X_test = vectorizer.fit_transform(titles['text'])
	clf = joblib.load('new_trained_model.pkl')
	
	pred = clf.predict_proba(X_test)
	#arr = np.empty((np.size(titles,0),4),dtype=object)
	arr = [None] * 5
	arr[0] = titles['title'][0]
	arr[1] = titles['abstract'][0]
	arr[2] = titles['link'][0]
	arr[3] = titles['journal_name'][0]
	arr[4] = float(pred[:,1])
	return arr
	
def pull_handles_from_twitter(accounts):
	# twitter followers
	auth = tweepy.OAuthHandler(environ['TWITTER_CONSUMER_KEY'], environ['TWITTER_CONSUMER_SECRET'])
	auth.set_access_token(environ['TWITTER_ACCESS_TOKEN'], environ['TWITTER_ACCESS_SECRET'])
	api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,retry_count=10, retry_delay=5, retry_errors=set([503])	)
	ids = []
	names = []
	handles = []
	for account in accounts:
		for page in tweepy.Cursor(api.followers_ids, screen_name=account).pages():
			ids.extend(page)
			sleep(5)
	ids = list(set(ids)) # dedupe
	#print(len(ids))
	for chunk_i in range(0,len(ids),100):
		users_obj = api.lookup_users(ids[chunk_i:chunk_i+100])
		names.extend([unidecode(user.name) for user in users_obj])
		handles.extend(['@'+user.screen_name for user in users_obj])
		sleep(5)
	add_handles_data = dict(zip(names,handles))
	#print(add_handles_data)
	#print(len(add_handles_data))
	
	return add_handles_data

def get_author_handles(raw_author_list,title,twitter_handles_data):
	creds = ServiceAccountCredentials.from_json_keyfile_dict(
	keyfile_dict=keyfile_dict, scopes=scopes)
	#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
	while 1:
		try:
			client = gspread.authorize(creds)
			break
		except:
			sleep(60)
			continue	
	
	# authors
	sh = client.open_by_key('1mvv1ZtqWnxQWk6FUV6b14Po4J0MlYyjq5jh0W8vU49o')
	worksheet = sh.sheet1
	names = worksheet.col_values(1)
	handles = worksheet.col_values(2)	
	author_handles_data = dict(zip(names,handles))
	sleep(1) # always pause 1 sec after every gsheet read/write
	
	# twitter authors
	#twitter_handles_data = pull_follower_handles(['Xenon1T','luxdarkmatter','CelineBoehm1'])
	author_handles_data.update(twitter_handles_data)
	
	# collabs
	sh = client.open_by_key('1L-IYx86R63bB1t2j-9tI6uL5qRUATPEfaKMr9DoBRmw')
	worksheet = sh.sheet1
	names = worksheet.col_values(1)
	handles = worksheet.col_values(2)	
	collab_handles_data = dict(zip(names,handles))
	sleep(1) # always pause 1 sec after every gsheet read/write
	

	
	handles_all = ''
	h = html2text.HTML2Text()
	h.ignore_links = True	
	author_list = h.handle(raw_author_list[0]['name'])
	author_list = (author_list).replace('\n',' ').split(', ')
	
		#author = raw_author['name']
	for handle_query in collab_handles_data.keys():
		if fuzz.partial_ratio(title,handle_query) > 90:
			handles_all = handles_all + collab_handles_data[handle_query] + ' '
			
	for author in author_list:
		for handle_query in author_handles_data.keys():
			if fuzz.ratio(normalize_text(author),normalize_text(handle_query)) > 90:
				handles_all = handles_all + author_handles_data[handle_query] + ' '
				#print(author+' matched with ' +handle_query)
				break
	return handles_all
				
def scrape_image(link):
	urllib.request.urlretrieve(link.replace('abs','e-print'),'source')
	if os.path.isdir('./data/'):
		rmtree('./data/')
	os.makedirs('./data/',exist_ok=True)
	try:	
		patoolib.extract_archive("source", outdir="./data/")
	except:
		print('Arxiv: eprint not a zip file, so probably PDF.')
		try:
			doc = fitz.open('source')
		except: # source file not a PDF file, just post first page of PDF
			print('eprint not a pdf file either. scraping pdf file for first page.')
			urllib.request.urlretrieve(link.replace('abs','pdf'),'source')
			call(['convert','-density','150','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./source[0]','./data/tweet_pic.png'])
			print('Page 0 saved as image.')
			return True			

		img_pgs = []
		for i in range(len(doc)):
			if len(doc.getPageImageList(i)) > 0:
				img_pgs.append(str(i)) # pages with images
		if len(img_pgs) > 0:
			pg_choice = choice(img_pgs)
			call(['convert','-density','150','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./source['+ pg_choice+']','./data/tweet_pic.png'])
			print('Page %s saved as image.' % pg_choice)
		else:
			call(['convert','-density','150','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./source[0]','./data/tweet_pic.png'])
			print('Page 0 saved as image.')
			return True
#	if glob.glob('./data/' + '**/*.tex', recursive=True) !=[]:

	higfiles = glob.glob('./data/' + '**/hig.*', recursive=True)
	if higfiles != []:
		print('Found higfiles!')
		picraw = choice(higfiles)
		try:
			call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off', picraw+'[0]','./data/tweet_pic.png'])
			return (True, True)			
		except Exception:
			pass

	files = glob.glob('./data/' + '**/*.png', recursive=True)
	if files != []:
		print('Found png files.')
		tries = 0
		while tries < 5:
			picraw = choice(files)
			tries += 1
			if not ('ORCID' in picraw or 'example' in picraw): # check that example or ORCID images are not selected
				break
			if tries==5:
				return False
		call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off', picraw+'[0]','./data/tweet_pic.png'])
		return True
	else:
		otherfiles = glob.glob('./data/' + '**/*.jpg', recursive=True) + glob.glob('./data/' + '**/*.jpeg', recursive=True) + glob.glob('./data/' + '**/*.pdf', recursive=True) + glob.glob('./data/' + '**/*.eps', recursive=True) + glob.glob('./data/' + '**/*.ps', recursive=True)
		if otherfiles != []:
			print('Found jpeg/pdf/eps/ps files.')
			tries = 0
			while tries < 5:
				picraw = choice(otherfiles)
				tries += 1
				if not ('ORCID' in picraw or 'example' in picraw): # check that example or ORCID images are not selected
					break
				if tries==5:
					return False
			call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off', picraw+'[0]','./data/tweet_pic.png'])
			return True
		else:
			print('Found no picture files, scraping pdf for first page.')
			urllib.request.urlretrieve(link.replace('abs','pdf'),'./data/paper.pdf')
			call(['convert','-density','150','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./data/paper.pdf[0]','./data/tweet_pic.png'])
			print('Page 0 saved as image.')
			return True

#	else:
#		if glob.glob('./data/' + '**/*.pdf', recursive=True) !=[]:	
	

def tweet_post(line,image_flag,interv):
	auth = tweepy.OAuthHandler(environ['TWITTER_CONSUMER_KEY'], environ['TWITTER_CONSUMER_SECRET'])
	auth.set_access_token(environ['TWITTER_ACCESS_TOKEN'], environ['TWITTER_ACCESS_SECRET'])
	api = tweepy.API(auth,retry_count=10, retry_delay=15, retry_errors=set([503])	)

	if isinstance(image_flag,tuple):
		try:
			api.update_with_media('./data/tweet_pic.png',line + ' (fig picked by authors)')
			sleep(interv*60) #30 mins for arxiv
			return True			
		except tweepy.TweepError as e:
			sleep(60)
			try:
				api.update_with_media('./data/tweet_pic.png',line + ' (fig picked by authors)')
				sleep(interv*60) #30 mins for arxiv
				return True					
			except tweepy.TweepError as e:	
				print('Something went wrong with Twitter API.')
				return False

	else:
		try:
			if image_flag == False:
				api.update_status(line)
				sleep(interv*60) #30 mins for arxiv
				return True
			else:
				api.update_with_media('./data/tweet_pic.png',line)
				sleep(interv*60) #30 mins for arxiv
				return True
		except tweepy.TweepError as e:
			sleep(60) # wait 60 seconds, try tweeting again
			try:
				if image_flag == False:
					api.update_status(line)
					sleep(interv*60) #30 mins for arxiv
					return True
				else:
					api.update_with_media('./data/tweet_pic.png',line)
					sleep(interv*60) #30 mins for arxiv
					return True
			except tweepy.TweepError as e:
				print('Something went wrong with Twitter API.')
					#print(e.args[0][0]['message'])		
			#print(e.args[0][0]['message'])
				return False

def retweet_old(number,interv):
	auth = tweepy.OAuthHandler(environ['TWITTER_CONSUMER_KEY'], environ['TWITTER_CONSUMER_SECRET'])
	auth.set_access_token(environ['TWITTER_ACCESS_TOKEN'], environ['TWITTER_ACCESS_SECRET'])
	api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,retry_count=10, retry_delay=15, retry_errors=set([503]))
	tweets = []
	# retweeting tweets
	tweets = api.user_timeline(count = 200)
	
	for i in range(number):
		while 1:
			tweet = choice(tweets)
			if tweet.retweeted == False:
				break
		try:
			api.retweet(tweet.id)
			sleep(interv*60)	
		except:
			pass
	return 