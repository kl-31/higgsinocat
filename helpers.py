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
from pdf2image import convert_from_path
from imageio import imwrite

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
	client = gspread.authorize(creds)
	sh = client.open_by_key('1EwXRCRo3SUgm5GAH5mvKwQbesWL5Xqu8xMkJPxFaH64')
	worksheet = sh.sheet1
	titles_list = worksheet.col_values(1)	
	return titles_list

def write_to_db(row):
	creds = ServiceAccountCredentials.from_json_keyfile_dict(
    keyfile_dict=keyfile_dict, scopes=scopes)
	#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
	client = gspread.authorize(creds)
	sh = client.open_by_key('1EwXRCRo3SUgm5GAH5mvKwQbesWL5Xqu8xMkJPxFaH64')
	worksheet = sh.sheet1
	worksheet.insert_row(row,1)
	sleep(1) # google api 60 write requests per 60 sec
	return


def normalize_text(s):
	s=''.join([i for i in s if not i.isdigit()]) # remove numbers
	s = s.replace('-',' ')
	s = s.replace('/',' ')
	s = s.replace('μ','u')
	s = unidecode(str(s))
	s=s.translate(s.maketrans('', '', string.punctuation)) # remove punctuation
	s = s.lower() # make lowercase
	return s

def compute_proba(titles):
	vectorizer = HashingVectorizer()
	
	titles = pd.DataFrame(titles,columns=['title','link','journal_name','abstract'])
	titles['text'] = [normalize_text(re.sub(r'\([^()]*\)', '', str(s))) for s in titles['title']]
	X_test = vectorizer.fit_transform(titles['text'])
	clf = joblib.load('new_trained_model.pkl')
	
	pred = clf.predict_proba(X_test)
	#arr = np.empty((np.size(titles,0),4),dtype=object)
	arr = [None] * 5
	arr[0] = titles['title'][0]
	arr[1] = titles['link'][0]
	arr[2] = titles['journal_name'][0]
	arr[3] = titles['abstract'][0]
	arr[4] = float(pred[:,1])
	return arr
	
def get_author_handles(raw_author_list):
	if isfile('author_handles.json'):
		handles_data = json.load(open('author_handles.json'))
	else:
		handles_data = {}
	handles_all = ''
#	h = html2text.HTML2Text()
#	h.ignore_links = True	
#	author_list = h.handle(raw_author_list)
#	author_list = author_list.replace('\n','').split(', ')
	for raw_author in raw_author_list:
		author = raw_author['name']
		for handle_query in handles_data.keys():
			if fuzz.partial_ratio(normalize_text(author),normalize_text(handle_query)) > 90:
				handles_all = handles_all + handles_data[handle_query] + ' '
				break
	return handles_all
				
def scrape_image(link):
	urllib.request.urlretrieve(link.replace('abs','e-print'),'source')
	if os.path.isdir('./data/'):
		rmtree('./data/')
	os.makedirs('./data/',exist_ok=True)
	patoolib.extract_archive("source", outdir="./data/")
	if glob.glob('./data/' + '**/*.tex', recursive=True) !=[]:
		files = glob.glob('./data/' + '**/*.pdf', recursive=True)
		if files != []:
			picpdf = choice(files)
			pic = convert_from_path(picpdf)
			imwrite('./data/tweet_pic.png',np.array(pic))
			return True
		else:
			return False
	else:
		return False
	

def tweet_post(line,image_flag):
	auth = tweepy.OAuthHandler(environ['TWITTER_CONSUMER_KEY'], environ['TWITTER_CONSUMER_SECRET'])
	auth.set_access_token(environ['TWITTER_ACCESS_TOKEN'], environ['TWITTER_ACCESS_SECRET'])
	api = tweepy.API(auth)	
	try:
		if image_flag == False:
			api.update_status(line)
			sleep(30*60) #30 mins for arxiv
			return True
		else:
			api.update_with_media('./data/tweet_pic.png',line)
			sleep(30*60) #30 mins for arxiv
			return True
	except tweepy.TweepError as e:
		print(e.args[0][0]['message'])
		return False

