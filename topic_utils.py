import collections
import itertools
import re
import string
import timeit

import matplotlib.pyplot as plt
import nltk
#nltk.download('popular')
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize.api import StringTokenizer
from nltk.tokenize import TweetTokenizer
import numpy as np
import pandas as pd
from wordcloud import WordCloud

from sklearn.decomposition import LatentDirichletAllocation
from sklearn.preprocessing import Normalizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

import sklearn
from sklearn.feature_extraction.text import CountVectorizer


def plot_top_words(model, 
                   feature_names, 
                   n_top_words, 
                   n_components,
                   title):
    fig, axes = plt.subplots(2, n_components//2, figsize=(30, 15), sharex=True)
    axes = axes.flatten()
    
    for topic_idx, topic in enumerate(model.components_[:n_components]):
        top_features_ind = topic.argsort()[:-n_top_words - 1:-1]
        top_features = [feature_names[i] for i in top_features_ind]
        weights = topic[top_features_ind]

        ax = axes[topic_idx]
        ax.barh(top_features, weights, height=0.7)
        ax.set_title(f'Topic {topic_idx +1}',
                     fontdict={'fontsize': 30})
        ax.invert_yaxis()
        ax.tick_params(axis='both', which='major', labelsize=20)
        for i in 'top right left'.split():
            ax.spines[i].set_visible(False)
        fig.suptitle(title, fontsize=40)

    plt.subplots_adjust(top=0.90, bottom=0.05, wspace=0.90, hspace=0.3)
    plt.show()


def extract_topics(documents_list,
                   n_samples = 2000,
                   n_features = 1000,
                   n_components = 10,
                   n_top_words = 20,
                   apply_preprocessing=True,
                   stop_words=None,
                   preprocessor=None,
                   tokenizer=None):
    
    if apply_preprocessing:
        print('preprocessing...')
        t1 = default_timer()
        documents_list = (documents_list
                         .map(long_string)
                         .map(preprocess_string)
                          )
        print('elapsed: {}'.format(default_timer() - t1))
    
    vectorizer = CountVectorizer(analyzer='word',
                                 strip_accents='ascii',
                                 stop_words=[*stopwords.words(),
                                              '<-url->', '<-@->', '<-#->', 
                                              '...','`',',','-',"'"],
                                 ngram_range=(1,2),
                                 tokenizer=TweetTokenizer(preserve_case=False,
                                           reduce_len=True,
                                           strip_handles=True).tokenize
                                )

    print('vectorizing...')
    t1 = default_timer()
    tf = vectorizer.fit_transform(documents_list)
    
    print('elapsed: {}'.format(default_timer() - t1))
    
    
    print(('LDA:\nn_samples: {}\nn_features: {}')
          .format(n_samples, n_features))

    lda = LatentDirichletAllocation(n_components=n_components, 
                                    max_iter=5,
                                    learning_method='online',
                                    learning_offset=50.,
                                    random_state=0)

    lda.fit(tf)
    
    tf_feature_names = vectorizer.get_feature_names()

    plot_top_words(lda, 
                   tf_feature_names, 
                   n_top_words,
                   n_components,
                   'Categories in LDA model')
    plt.tight_layout()
    
    

def long_string(list_of_strings):
    """
    Concatenate a list of strings into a single string.
    """
    return ' '.join([string for string in list_of_strings])

def long_list(list_of_lists):
    """
    Concatenate items from multiple lists into a single list.
    """
    return list(itertools.chain(*list_of_lists))

def long_string(list_of_strings):
    """
    Concatenate a list of strings into a single string.
    """
    return ' '.join([string for string in list_of_strings])

def long_list(list_of_lists):
    """
    Concatenate items from multiple lists into a single list.
    """
    return list(itertools.chain(*list_of_lists))

def preprocess_string(string, placeholders=False):
    """Remove symbols; replace urls, hashtags, and user 
       mentions with a placeholder token.
    """
    # "rt" ("retweet") 
    string = re.sub('rt', '', string.lower())
    
    if placeholders:
        # @-mentions
        string = re.sub(r'@\w+', '<-@->', string)

        # hyperlinks
        string = re.sub(r'http\S+', '<-URL->', string)
        string = re.sub(r'www.[^ ]+', '<-URL->', string)
    
        # hashtags
        string = re.sub(r'#\w+', '<-#->', string)
        
    else:
        # @-mentions
        string = re.sub(r'@\w+', '', string)

        # hyperlinks
        string = re.sub(r'http\S+', '', string)
        string = re.sub(r'www.[^ ]+', '', string)
    
        # hashtags
        string = re.sub(r'#\w+', '', string)
    
    # digits
    string = re.sub(r'[0-9]+', '', string)
    
    # symbols
    string = re.sub(r'[!"$%&()*+,./:;=?[\]^_`{|}~]+', '', string)
    
    return string

def tokenize_string(input_string, 
                    stop_words,
                    tokenizer=TweetTokenizer(preserve_case=False,
                                             reduce_len=True,
                                             strip_handles=False),
                    preprocess=False,
                   ):
    """Preprocess and tokenize a raw tweet string.
    
    Args:
        in_string: string to tokenize
        tokenizer: object with a ``tokenize'' method for strings
        
    Return:
        tokens: list of strings (tokens)
    """
    if preprocess == True:
        input_string = preprocess_string(input_string)
    
    tokens = tokenizer.tokenize(input_string)
    
    # remove stop words
    cache = set(stop_words)
    no_stop_words = [token for token in tokens
                     if token.lower() not in cache]
    
    return no_stop_words

def lemmatize(tokens, lemmatizer):
    """Lemmatize a set of tokens.
    
    Args:
        tokens: list of tokens to lemmatize
        lemmatizer: object with a ``lemmatize'' method for strings
        
    Return:
        lemmatized: list of lemmatized tokens
    """
    lemmatized = [lemmatizer.lemmatize(token) for token in tokens]
    
    return lemmatized