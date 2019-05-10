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
	sh = client.open_by_key('1PoD8M5_fg33gdAktthKXrsyPwHMqSMASDRIX1i_zYtk')
	worksheet = sh.sheet1
	titles_list = worksheet.col_values(1)	
	return titles_list

def write_to_db(row):
	creds = ServiceAccountCredentials.from_json_keyfile_dict(
    keyfile_dict=keyfile_dict, scopes=scopes)
	#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
	client = gspread.authorize(creds)
	sh = client.open_by_key('1PoD8M5_fg33gdAktthKXrsyPwHMqSMASDRIX1i_zYtk')
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
	titles['text'] = [normalize_text(str(s)) for s in titles['title']]
	X_test = vectorizer.fit_transform(titles['text'])
	clf = joblib.load('new_trained_model.pkl')
	
	pred = clf.predict_proba(X_test)
	#arr = np.empty((np.size(titles,0),4),dtype=object)
	arr = [None] * 5
	arr[0] = titles['title'][0]
	arr[1] = titles['link'][0]
	arr[2] = titles['journal_name'][0]
	arr[3] = titles['abstract'][0]
	arr[4] = float(pred[:,2])
	return arr
	

def tweet_post(line):
	auth = tweepy.OAuthHandler(environ['TWITTER_CONSUMER_KEY'], environ['TWITTER_CONSUMER_SECRET'])
	auth.set_access_token(environ['TWITTER_ACCESS_TOKEN'], environ['TWITTER_ACCESS_SECRET'])
	api = tweepy.API(auth)	
	try:
		api.update_status(line)
		sleep(60*60)
		return True
	except tweepy.TweepError as e:
		print(e.args[0][0]['message'])
		return False

#def shorten_link(link):
#	b = bitly_api.Connection(API_USER, API_KEY)
#	response = b.shorten(link)
#	return response['url']