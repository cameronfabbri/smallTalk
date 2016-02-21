from textblob import TextBlob
from textblob.classifiers import NaiveBayesClassifier
import numpy as np
import operator
import cPickle as pickle
import time
import sys

# Your configuration file(s)
import sockets
import config

BUFFER_SIZE = 1024

"""
Cameron Fabbri
1/31/2016
Parser.py

Main file for the framework.  This will control the flow and call functions
from other classes.

We want to parse each command given. We will only be able to support a 
limited number of functions, then the developer using this will be able
to write their own algorithms.
"""

# classifier file defined in config.py
classifier_file = config.classifier_file
try:
   cll = pickle.load(open(classifier_file, 'rb'))  
   print "Loaded classifier"
except:
   raise
   exit(-1)

"""
   Allows the user to input a label and command to better
   train the robot if it is having difficulty understanding
"""
def train():
   sockets.send("What's the label?\n")
   label    = sockets.recv(BUFFER_SIZE)
   command  = sockets.send("What's the command?\n")
   new_data = [(command, label)]
   f = open(classifier_file, 'wb')
   pickle.dump(cll, f)

"""
   Tests out a command
"""
def test_command(cll):
   sockets.send("What command would you like to test?\n")
   command = sockets.recv(BUFFER_SIZE)
   labels = cll.labels()
   mpl = labels[0]
   prob_dist = cll.prob_classify(command)
   for label in labels:
      if prob_dist.prob(label) > prob_dist.prob(mpl):
         mpl = label
   sockets.send("I think this is a %s command" %(str(mpl)))

def learn_new_command(command):
   sockets.send("What type of command is this? (The label for the command, one word only)")
   new_label = sockets.recv(BUFFER_SIZE)
   # could change this to "nevermind" or similar label
   if new_label == "no command":
      return -1
   sockets.send("Okay, what's the command?")
   new_command = sockets.recv(BUFFER_SIZE)
   new_data = [(new_command, new_label)]
   cll.update(new_data)
   f = open(classifier_file, 'wb')
   pickle.dump(cll, f)
   return -1

"""
   This is updating the classifier when we know what label it should be
"""
def addKnowledge(new_data, cll):
   cll.update(new_data)
   f = open(classifier_file, 'wb')
   pickle.dump(cll, f)

def update_classifier(cll, prob_label_dict):
   sockets.send("Please give me an example command for which this falls into\n")
   l = sockets.recv(BUFFER_SIZE)
   if l == "no command":
      return -1
   ll = TextBlob(l, classifier=cll).classify()
   prob_label_dict = sorted(prob_label_dict.items(), key=operator.itemgetter(1))[::-1]
   prob_label_list = list(prob_label_dict)
   new_label = prob_label_list[0][0]
   sockets.send("Adding command " + str(command) + " with label " + str(new_label))
   new_data = [(command, new_label)]
   cll.update(new_data)
   f = open(classifier_file, 'wb')
   pickle.dump(cll, f)
   return -1

"""
   Method for handling built in commands. Built in commands should only
   be one word commands that are hard to classify or are used frequently
   e.g "exit", "hello", "stop", etc

   If the command is built in, the parser will simply return the command
   instead of the label, so make sure you handle that on the robot side.
"""
def isBuiltIn(command):
   built_in = config.built_in
   for b_command in built_in:
      if b_command == command:
         print "Built in.."
         return True
   return False

"""
   Parses the command given, returns a json blob of possible location, object, subject, etc
"""
def parseCommand(command, cll, classifier_file):
   confidence_threshold = config.confidence_threshold
   prob_dist            = cll.prob_classify(command)
   labels               = cll.labels()
   prob_label_dict      = dict()
   mpl  = -1

   # before using the classifier, check if it is a built in command
   if isBuiltIn(command):
      return command

   for label in labels:
      if prob_dist.prob(label) > prob_dist.prob(mpl):
         mpl = label
      prob_label_dict[label] = prob_dist.prob(label)
   print "Most probable label: " + str(mpl) + ", prob: " + str(prob_dist.prob(mpl))

   # this is if the threshold wasn't passed. Add more to knowledge
   if prob_dist.prob(mpl) < confidence_threshold:
      sockets.send("Is this a " + mpl + " command?")
      a = sockets.recv(BUFFER_SIZE)
      if a == "yes" or ans == "yeah":
         new_data = [(command, mpl)]
         addKnowledge(new_data, cll)
         return mpl
      else:
         sockets.send("Want to add this to something I already know?\n")
         ans = sockets.recv(BUFFER_SIZE)
         if ans == "yes" or ans == "yeah":
            return update_classifier(cll, prob_label_dict)
         else:
            sockets.send("Okay then!")
            return -1

   # add what was just said to the classifier if it passed the threshold
   if prob_dist.prob(mpl) > confidence_threshold:
      new_data = [(command, mpl)]
      addKnowledge(new_data, cll)
      #print "adding knowledge..."
      #sockets.send("Adding " + str(new_data) + " to classifier")
   risk = 0
   return mpl, risk