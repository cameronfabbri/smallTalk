from textblob import TextBlob
from textblob.classifiers import NaiveBayesClassifier
import time
import cPickle as pickle

# Your config file with training sets
import config

"""

Cameron Fabbri
1/31/2016
setup.py

A setup file where the user can define their application parameters.
This setup file trains the classifiers and puts the 'cl' object into
the database

I think what's going on is the classification is really bad with 
single word commands. Try to train on multiple words

---
 TODO Combine this with setup_from_db.py. Just have one big setup that does it all with
 all options. Another thought is to have the user put in locations in the setup which
 will store in the db, so when they say 'bring my plate to the kitchen', it will know
 the kitchen. Could have that as a totally seperate projcet though
---

"""

def train(filename):
   print "Training classifier..."
   s = time.time()
   train = config.train
   cll = NaiveBayesClassifier(train)
   print "Training complete " + str(time.time()-s)
   s = time.time()
   print "Saving classifier..."
   f = open(filename, 'wb')
   pickle.dump(cll, f)

try:
   with open('classifier.pickle', 'r'):
      inp = raw_input("A classifier has already been trained! Enter in a new filename or simply enter 'o' to overwrite the current classifier\n")
      if inp == "o":
         train("classifier.pickle")
      else:
         train(inp)
except:
   train("classifier.pickle")
