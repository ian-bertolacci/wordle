import fileinput, re, random, sys, argparse
from functools import reduce, partial
from pprint import pprint
from random import Random
from termcolor import colored
from math import *


class Dictionary:
    def __init__(this, path):
        this.words = set()
        this.letters = set()
        # length -> list[str] (words of this length)
        this.length_bucketed_words = {}
        # letter -> int (count of this letter's occurence in the dictionary)
        this.letter_frequency = {}


        for line in fileinput.input(files=path):
            word = line.strip().lower()
            if word in this.words:
                continue

            if len(word) not in this.length_bucketed_words:
                this.length_bucketed_words[len(word)] = [word]
            else:
                this.length_bucketed_words[len(word)].append(word)

            letter_set = set(word)
            this.letters |= letter_set
            for char in letter_set:
                count = word.count(char)

                if char not in this.letter_frequency:
                    this.letter_frequency[char] = count
                else:
                    this.letter_frequency[char] += count

            this.words.add(word)
        this.letters = reduce(lambda letters, word: letters | set(word), this.words, set())


    def frequency_of(this, letter):
        return this.letter_frequency[letter]

    def words_with_length(this, length):
        return this.length_bucketed_words[length]

    def word_lengths(this):
        return list(this.length_bucketed_words.keys())

__all__ = ["Dictionary"]
