#!/usr/bin/env python3
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL) 
import io
import os
import sys
import gzip
import faulthandler; faulthandler.enable()
import sys
import fileinput
import argparse
from argparse import RawTextHelpFormatter
from termcolor import colored

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn import preprocessing
from sklearn.metrics import confusion_matrix
from matplotlib import pyplot as plt

def is_valid_file(x):
	if not os.path.exists(x):
		raise argparse.ArgumentTypeError("{0} does not exist".format(x))
	return x


if __name__ == '__main__':
	usage = '%s [-opt1, [-opt2, ...]] infile' % __file__
	parser = argparse.ArgumentParser(description='', formatter_class=RawTextHelpFormatter, usage=usage)
	#parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
	#parser.add_argument('clusters', type=is_valid_file, help='clusters file')
	parser.add_argument('infile', type=is_valid_file, help='input file')
	args = parser.parse_args()

	'''
	clusters = list()
	with open(args.clusters) as fp:
		for line in fp:
			cols = line.rstrip().split()
			cols = cols[1:]
			clusters.append(cols)
	'''

	le = preprocessing.LabelEncoder()
	oe = preprocessing.OrdinalEncoder()
	he = preprocessing.OneHotEncoder()

	df = pd.read_csv(args.infile, sep='\t')
	# this removes duplicate positive TYPEs that are more than 10 bases away from annotated shift
	df.loc[abs(df.I - df.CURRLEFT) > 10 ,'TYPE'] = 0
	#print(df.loc[df.TYPE==1,'NAME'].nunique()) ; exit()


	#idx = df.loc[df.TYPE==1,:].groupby(['NAME','MODEL','PARAM']).PROB.idxmin()
	#df['TYPE'] = 0 ; df.loc[idx,['TYPE']] = 1
	#print(df.loc[df.TYPE==1,:]) ; exit()


	# this is to drop genomes that do not have a chaperone annotated
	has = df.groupby('NAME')['TYPE'].any().to_frame('HAS')
	df = df.merge(has, left_on='NAME', right_index=True)
	df = df.loc[df.HAS,:]

	#df = df[df.MOTIF != "is_twoonethree"]

	#print(df.loc[df.NAME=='Abigail',["NAME",'I','TYPE','BEST']]) ; exit()

	# label encoder is prob not the best to use
	#df.loc[:,'MOTIF'] = le.fit_transform(df['MOTIF'])
	oh = pd.get_dummies(df['MOTIF'])

	take = [False] * len(df.columns)
	#for i in [1,10,11,12,16,17,18,19,20]:
	for i in [1,10,11,12,18,86,247]: #,87,167,186]:
		take[i] = True

	#print(df.loc[:,take]) ; exit()

	column = 'CLUSTER' #'mash_k16s400c90'
	model,param = ('DP','parameters_DP09.txt')
	X = df.loc[(df['MODEL']==model) & (df['PARAM']==param),take].join(oh)
	Y = df.loc[(df['MODEL']==model) & (df['PARAM']==param),['TYPE']]
	take.extend( [True] * len(oh.columns))
	TN = FP = FN = TP = 0
	for cluster in df[column].unique():
		cluster = 'ClusterA'
		#print(cluster)
		#Y = df.loc[:,['BEST']]
		X_train = X.loc[df[column] != cluster, :]
		X_test  = X.loc[df[column] == cluster, :]
		#print(X_train)  ; exit()
		Y_train = Y.loc[df[column] != cluster, :]
		Y_test  = Y.loc[df[column] == cluster, :]

		if X_test.empty:
			continue
		clf = RandomForestClassifier(max_depth=100, random_state=0)
		clf.fit(X_train, Y_train.values.ravel())
		preds = clf.predict(X_test)
		#print(cluster)
		#print(confusion_matrix(Y_test, preds, labels=[0,1]))
		tn, fp, fn, tp = confusion_matrix(Y_test, preds, labels=[0,1]).ravel()
		TN += tn ; FP += fp ; FN += fn ; TP += tp
		print(cluster, colored(tn, 'green'),colored(fp, 'red'),colored(fn, 'red'),colored(tp, 'green') , sep='\t')
		#print(cluster, model, param, TN, FP, FN, TP, precis, recall, f1, sep='\t', flush=True)
		exit()

	print(colored(TN, 'green'),colored(FP, 'red'),colored(FN, 'red'),colored(TP, 'green') )
	precis = TP / (TP+FP) if (TP+FP) else 0
	recall = TP / (TP+FN) if (TP+FN) else 0
	f1 = (2 * precis * recall) / (precis+recall) if (precis+recall) else 0
	print(precis, recall, f1) ; exit()
		#print(tp,tn,fp,fn)
		#true = [bool(p) for p in preds]
		#print(X_test.loc[ true ,].join(Y_test.loc[true,]) )
		#sel = [bool(p) for p in Y_test.to_numpy()]
		#print(X_test.loc[ sel ,].join(Y_test.loc[sel,]) )
		#print(df.loc[ X_test.loc[ true ,].index.tolist() ,:] )
		#exit()
	




