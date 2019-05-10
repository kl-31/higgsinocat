#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 13:23:05 2019

@author: liangkc
partly from https://www.kaggle.com/kinguistics/classifying-news-headlines-with-scikit-learn
and
mostly from https://scikit-learn.org/stable/auto_examples/text/plot_document_classification_20newsgroups.html#sphx-glr-auto-examples-text-plot-document-classification-20newsgroups-py
"""

# get some libraries that will be useful
import string
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)


from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_selection import SelectFromModel
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import RidgeClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.linear_model import SGDClassifier, LogisticRegression
from sklearn.linear_model import Perceptron
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.ensemble import RandomForestClassifier,AdaBoostClassifier, GradientBoostingClassifier
from sklearn.utils.extmath import density
from sklearn import metrics
from sklearn.externals import joblib
from time import time
import matplotlib.pyplot as plt
import numpy as np


def normalize_text(s):
	s=''.join([i for i in s if not i.isdigit()]) # remove numbers
	s = s.replace('-',' ')
	s=s.translate(s.maketrans('', '', string.punctuation)) # remove punctuation
	s = s.lower() # make lowercase
	return s

vectorizer = HashingVectorizer()

# grab the data
titles = pd.read_csv("new-paper-titles-data.csv", names=['title','category'])
titles['text'] = [normalize_text(str(s)) for s in titles['title']]

# unseen data
#unseen_pd = pd.read_csv("paper-titles-unseen-optica.csv",names=['title','link','journal_name'],sep='\t',encoding ='latin1')
#unseen_pd['text'] = [normalize_text(str(s)) for s in unseen_pd['title']]
#unseen = vectorizer.fit_transform(unseen_pd['text'])





# split into train and test sets
data_train, data_test, y_train, y_test = train_test_split(titles['text'], titles['category'], test_size=0.2)

target_names = ['0','1','2']

# pull the data into vectors

X_train = vectorizer.fit_transform(data_train)
X_test = vectorizer.fit_transform(data_test)

# test unseen data




## uncomment if want to compare models
#def benchmark(clf):
#	print('_' * 80)
#	print("Training: ")
#	print(clf)
#	t0 = time()
#	clf.fit(X_train, y_train)
#	train_time = time() - t0
#	print("train time: %0.3fs" % train_time)
#
#	t0 = time()
#	pred = clf.predict(X_test)
#	test_time = time() - t0
#	print("test time:  %0.3fs" % test_time)
#
#	score = metrics.accuracy_score(y_test, pred)
#	print("accuracy:   %0.3f" % score)
#	
#
#	
#	print("classification report:")
#	print(metrics.classification_report(y_test, pred,
#											target_names=target_names))
#	print("confusion matrix:")
#	print(metrics.confusion_matrix(y_test, pred))
#	print()
#	clf_descr = str(clf).split('(')[0]
#	return clf_descr, score, train_time, test_time
#
#results = []
#for clf, name in (
#		(LogisticRegression(),"Logistic Regression"),
#		#(RidgeClassifier(tol=1e-2, solver="sag"), "Ridge Classifier"),
#		#(Perceptron(max_iter=50, tol=1e-3), "Perceptron"),
#		#(PassiveAggressiveClassifier(max_iter=50, tol=1e-3),
#		# "Passive-Aggressive")):
#		#(KNeighborsClassifier(n_neighbors=10), "kNN")):
#		):
#	print('=' * 80)
#	print(name)
#	results.append(benchmark(clf))
#
#for penalty in ["l2", "l1"]:
#	print('=' * 80)
#	print("SGD %s penalty" % penalty.upper())
#	# Train Liblinear model
##	results.append(benchmark(LinearSVC(penalty=penalty, dual=False,
#	#								   tol=1e-3)))
#
#	# Train SGD model
#	results.append(benchmark(SGDClassifier(alpha=.0001, max_iter=50,loss='modified_huber',
#										   penalty=penalty)))
#
## Train SGD with Elastic Net penalty
#print('=' * 80)
#print("SGD Elastic-Net penalty")
#results.append(benchmark(SGDClassifier(alpha=.0001, max_iter=50,loss='modified_huber',
#									   penalty="elasticnet")))
#
## Train NearestCentroid without threshold
##print('=' * 80)
##print("NearestCentroid (aka Rocchio classifier)")
##results.append(benchmark(NearestCentroid()))
#
## Train sparse Naive Bayes classifiers
#print('=' * 80)
#print("Naive Bayes")
#results.append(benchmark(MultinomialNB(alpha=.01)))
#results.append(benchmark(BernoulliNB(alpha=.01)))
##results.append(benchmark(ComplementNB(alpha=.1)))
#
#print('=' * 80)
#print("Ensemble")
#results.append(benchmark(RandomForestClassifier(n_estimators=20,max_depth=25)))
#results.append(benchmark(AdaBoostClassifier(n_estimators=20)))
#results.append(benchmark(GradientBoostingClassifier(n_estimators=20)))
#
#
#accuracies = [i[1] for i in results]
#best_acc = accuracies.index(max(accuracies))
#best_clf = results[best_acc][0]
#print('Best clf: %s' % best_clf)

#
#clf = LogisticRegression()
#benchmark(clf)
clf = LogisticRegression()
grid_values = {'penalty': ['l1', 'l2'],'C':[0.001,.009,0.01,.09,1,5,10,25]}
grid_clf = GridSearchCV(clf, param_grid = grid_values,scoring = 'recall_weighted')
grid_clf.fit(X_train, y_train)
print('Best Score: ', grid_clf.best_score_)
print('Best Params: ', grid_clf.best_params_)
_ = joblib.dump(grid_clf, 'new_trained_model.pkl', compress=9)
#Predict values based on new parameters
y_pred = grid_clf.predict(X_test)
score = metrics.accuracy_score(y_test, y_pred)
print("accuracy:   %0.3f" % score)
	

print("classification report:")
print(metrics.classification_report(y_test, y_pred,
											target_names=target_names))
print("confusion matrix:")
print(metrics.confusion_matrix(y_test, y_pred))
#
##compare to old model
#clf = joblib.load('trained_model.pkl')
#print("classification report:")
#y_pred = clf.predict(X_test)
#score = metrics.accuracy_score(y_test, y_pred)
#print("accuracy:   %0.3f" % score)
#print(metrics.classification_report(y_test, y_pred,
#											target_names=target_names))

#unseen_pred = clf.predict_proba(unseen)
#relevant = np.where([i[2]>=0.5 for i in unseen_pred])[0]
#irrelevant = np.where([i[2]<0.5 for i in unseen_pred])[0]
##print(unseen_pred)
#relevant_arr = np.empty((len(relevant),4),dtype=object)
#relevant_arr[:,0] = np.array(unseen_pd.loc[relevant,'title'])
#relevant_arr[:,1] = np.array(unseen_pd.loc[relevant,'link'])
#relevant_arr[:,2] = np.array(unseen_pd.loc[relevant,'journal_name'])
#relevant_arr[:,3] = unseen_pred[relevant,2]
#print(relevant_arr)
#print('%d relevant papers found.' % len(relevant))
#print(np.array(unseen_pd.loc[irrelevant,'title']))
#print('%d irrelevant papers found.' % len(irrelevant))



