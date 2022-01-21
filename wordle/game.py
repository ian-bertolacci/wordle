import fileinput, re, random, sys, argparse
from functools import reduce, partial
from pprint import pprint
from random import Random
from termcolor import colored
from math import *

from dictionary import *

class GameException(Exception):
    pass

class WordleGame:
    YES = "YES"
    NO = "NO"
    SOMEWHERE = "SOMEWHERE"

    def __init__(this, dictionary, word_length = None, seed = None, answer=None):
        this.dictionary = dictionary

        if seed is None:
            this.rand = random
        else:
            this.rand = Random(seed)

        if word_length is None:
            if answer is None:
                this.word_length = this.rand.choice(this.dictionary.word_lengths())
            else:
                this.word_length = len(answer)
        else:
            this.word_length = word_length

        this.allowed_words = this.dictionary.words_with_length(this.word_length)
        if len(this.allowed_words) == 0:
            raise Exception(f"No words in dictionary with length {this.word_length}")

        if answer is None:
            this.answer = this.rand.choice(this.allowed_words)
        else:
            this.answer = answer

    def attempt(this, word):
         if len(word) != len(this.answer):
             raise GameException(f"Bad word length {len(word)} != {this.word_length}")
         if word not in this.allowed_words:
             raise GameException(f"Invalid word: {word}")

         word = word.lower()
         return [
                   (WordleGame.YES,w) if w == a else
             (WordleGame.SOMEWHERE,w) if w in this.answer
                       else (WordleGame.NO,w)
            for (w,a) in zip(word, this.answer)
        ]

    def format_attempt(attempt_result):
        return "".join((
           colored(w.upper(), "grey", "on_green")  if ans == WordleGame.YES else
           colored(w,         "grey", "on_yellow") if ans == WordleGame.SOMEWHERE
                     else colored(w, "white", "on_grey")
           for (ans, w) in attempt_result
        ))

    def formatted_attempt(this, word):
        return WordleGame.format_attempt(this.attempt(word))

    def check_attempt_solved(attempt_result):
        return all( ( ans == WordleGame.YES for (ans, _) in attempt_result) )
