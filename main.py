#!/usr/bin/env python3
import fileinput, re, random, sys, argparse
from functools import reduce, partial
from pprint import pprint
from random import Random
from termcolor import colored
from math import *

from wordle import *

def main(argv):
    parser = argparse.ArgumentParser()

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--game", action="store_true", description="Play a wordle game")
    mode_group.add_argument("--stats", action="store_true", description="Have the solver play sames and print solver statistics")
    mode_group.add_argument("--helper", action="store_true", description="Help you cheat at a wordle game")

    parser.add_argument("--dictionary-path", dest="dictionary_path", type=str, nargs=1, default="./wordle-words.txt", description="Path to a list of word available for attempts and answers in a gam")
    parser.add_argument("--word-length", dest="word_length", type=int, nargs=1, default=None)
    parser.add_argument("--words", dest="known_words", type=str, nargs="+", default=None, "set pre-defined words for solver")

    loop_group = parser.add_mutually_exclusive_group(required=False)
    loop_group.add_argument("--loop", dest="loop", action="store_true", default=True, "run solver in infinite loop")
    loop_group.add_argument("--once", dest="loop", action="store_false", "run solver once (can use with --words)")

    pretty_group = parser.add_mutually_exclusive_group(required=False)
    pretty_group.add_argument("--pretty", dest="pretty", action="store_true", default=True, "run solver in pretty-print mode with highlighting")
    pretty_group.add_argument("--simple", dest="pretty", action="store_false", "run solver without pretty-print mode")


    args = parser.parse_args(argv[1:])
    args.word_length = args.word_length if args.word_length is None else args.word_length[0]

    # dictionary_path = "/Users/ian.bertolacci/code/misc/wordle/wordle-words.txt"

    dictionary = Dictionary(args.dictionary_path)

    try:
        if args.stats:
            if args.known_words:
                if args.loop:
                    print("ignoring loop argument")
                for word in args.known_words:
                    print(word)
                    (solution, attempts) = SelfSolver.run(dictionary, answer=word, pretty_print=args.pretty)
                    print(f"SOLVED! \"{solution}\" after {len(attempts)} {attempts}")
            elif args.loop:
                if args.known_words:
                    print("ignoring words argument")
                SelfSolver.run_loop_with_stats(dictionary, word_length=args.word_length, pretty_print=args.pretty)
            else:
                (solution, attempts) = SelfSolver.run(dictionary, word_length=args.word_length, pretty_print=args.pretty)
                print(f"SOLVED! \"{solution}\" after {len(attempts)} {attempts}")
        elif args.game:
            if args.known_words:
                print("ignoring words argument")
            game = WordleGame(dictionary, word_length=args.word_length)
            WordleGameUi(game).run()
        elif args.helper:
            if args.word_length is None:
                print("must define a word length")
                parser.print_help()
            else:
                helper = InteractiveHelper(dictionary, args.word_length)
                helper.start()
    except KeyboardInterrupt:
        pass

class WordleGameUi:
    def __init__(this, game):
        this.game = game

    def run(this):
        print(f"Word is {this.game.word_length} letters long")
        solved = False
        while not solved:
            try:
                word = input("Enter word: ")
                result = this.game.attempt(word)
                print(WordleGame.format_attempt(result))
                solved = WordleGame.check_attempt_solved(result)
            except GameException as e:
                print(e)
                print("try again")


class InteractiveHelper:
    def __init__(this, dictionary, word_length):
        this.dictionary = dictionary
        this.word_length = word_length
        this.optimizer = WordChoiceOptimizer(this.dictionary)
        this.helper = CumulativeHelper(this.dictionary, this.word_length)

    def start(this):
        print("Some possible first word suggestions with statistics, in descending order of utility:")
        this.optimizer.starter_words_with_stats(this.word_length)

        while True:
            valid = False
            while not valid:
                regex = input("literal regex matching this hint: ")
                if regex == "":
                    regex = "." * this.word_length
                try:
                    this.helper.merge_regex(regex)
                    valid = True
                except Exception as e:
                    print(f"There was an error with the regex input: {e}")
                    print("Try again")


            valid = False
            while not valid:
                including = input("letters included in hint: ")

                try:
                    this.helper.merge_including(including)
                    valid = True
                except Exception as e:
                    print(f"There was an error with the include input: {e}")
                    print("Try again")

            valid = False
            while not valid:
                excluding = input("letters excluded in hint: ")

                try:
                    this.helper.merge_excluding(excluding)
                    valid = True
                except Exception as e:
                    print(f"There was an error with the include input: {e}")
                    print("Try again")

            print(f"Current regex: {this.helper.regex()}")
            print(f"Current includes: {this.helper.including()}")
            print(f"Current excludes: {this.helper.excluding()}")

            try:
                candidates = this.helper.suggest()
                if len(candidates) > 25:
                    print(f"Currently {len(candidates)} candidates. Try more hints.")
                else:
                    print("Possible words matching the collected hints:\n\t" + "\n\t".join(candidates))
            except Exception as e:
                print(f"oops! Something went wrong: {e}\ntry again.")

if __name__ == "__main__":
    main(sys.argv)
