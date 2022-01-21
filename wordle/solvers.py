import fileinput, re, random, sys, argparse
from functools import reduce, partial
from pprint import pprint
from random import Random
from termcolor import colored
from math import *

from dictionary import *

class WordChoiceOptimizer:
    def __init__(this, dictionary):
        this.dictionary = dictionary

    def score(this, word, some_existing_letter_coverage=set()):
        return sum( (this.dictionary.frequency_of(letter) for letter in set(word) - some_existing_letter_coverage) )

    def starter_words(this, length, n_best_words = 5):
        word_list = this.dictionary.words_with_length(length).copy()
        first_choice = chooseMax(word_list, this.score)
        word_list.remove(first_choice)

        best_words = [first_choice]
        cumulative_coverage = set(first_choice)
        for i in range(n_best_words - 1):
            if len(word_list) == 0 or cumulative_coverage == this.dictionary.letters:
                break
            next_best = chooseMax(
                word_list,
                partial(this.score, some_existing_letter_coverage=cumulative_coverage)
            )
            best_words.append(next_best)
            word_list.remove(next_best)
            cumulative_coverage |= set(next_best)
        return best_words

    def starter_words_with_stats(this, *args, **kwargs):
        starting_words = this.starter_words(*args, **kwargs)
        n_letters = len(this.dictionary.letters)
        coverage = set()
        for word in starting_words:
            word_set = set(word)
            len_set = len(word_set)
            old_coverage = set(list(coverage))
            coverage |= set(word)
            local_utility = len_set/n_letters
            cumulative_utility = len(coverage)/n_letters
            improved_utility = cumulative_utility - (len(old_coverage)/n_letters)
            print((
                word,
                this.score(word, old_coverage),
                "".join(sorted(word_set)),
                local_utility,
                (
                    "".join(sorted(coverage)),
                    "+" + "".join(sorted(coverage - old_coverage)),
                    ("r" + "".join(sorted(this.dictionary.letters - coverage)),),
                    improved_utility,
                    cumulative_utility
                )
            ))

class Suggestor:
    def __init__(this, dictionary):
        this.dictionary = dictionary

    def help(this, length, regex=None, including=None, excluding=None):

        including = set( including if including is not None else "" )
        excluding_rx = "[^" + "".join(sorted(set(excluding))) + "]" if excluding is not None and excluding != [] and excluding != "" and excluding != set() else "."


        regex = regex if regex is not None else "." * length

        if len(regex) != length:
            raise Exception(f"regex length ({regex}, {len(regex)}) differs from given length ({length})")
        regex = regex.replace(".", excluding_rx)
        cregex = re.compile(regex)

        candidates = [
            word
            for word in this.dictionary.words_with_length(length)
                if cregex.match(word) and set(word) >= including
        ]

        return candidates

class CumulativeHelper:
    def __init__(this, dictionary, word_length):
        this.dictionary = dictionary
        this.word_length = word_length
        this.suggestor = Suggestor(this.dictionary)
        this.cumulative_regex = None
        this.cumulative_including = None
        this.cumulative_excluding = None
        this.reset()

    def reset(this):
        this.reset_regex()
        this.reset_excluding()
        this.reset_including()

    def reset_regex(this):
        this.cumulative_regex = "." * this.word_length

    def reset_including(this):
        this.cumulative_including = set()

    def reset_excluding(this):
        this.cumulative_excluding = set()

    def merge_regex(this, regex):
        if len(regex) != this.word_length:
            raise Exception(f"given regex is of incompativle length {len(regex)} vs {this.word_length}")

        this.cumulative_regex = "".join( ( n if n != "." and n != " " and n != "-" else p for (p,n) in zip(this.cumulative_regex, regex) ) )

    def merge_including(this, thing):
        set_like = thing if type(thing) == set else set(thing)

        if len(set_like & this.cumulative_excluding) != 0:
            raise Exception(f"Cannot merge into including things set({set_like & this.cumulative_excluding}) which are included by excluding")

        this.cumulative_including |= set_like

    def merge_excluding(this, thing):
        set_like = thing if type(thing) == set else set(thing)

        if len(set_like & this.cumulative_including) != 0:
            raise Exception(f"Cannot merge into including things set({set_like & this.cumulative_including}) which are included by including")

        this.cumulative_excluding |= set_like

    def merge_attempt_result(this, attempt_result):
        regex = "".join(( w if ans == WordleGame.YES else "." for (ans, w) in attempt_result))
        include = [ w for (ans, w) in attempt_result if ans == WordleGame.SOMEWHERE ]
        exclude = [ w for (ans, w) in attempt_result if ans == WordleGame.NO ]

        this.merge_regex(regex)
        this.merge_including(include)
        this.merge_excluding(exclude)


    def regex(this):
        return this.cumulative_regex

    def including(this):
        return this.cumulative_including

    def excluding(this):
        return this.cumulative_excluding

    def suggest(this):
        return this.suggestor.help(this.word_length, regex=this.regex(), including=this.including(), excluding=this.excluding())