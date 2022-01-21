#!/usr/bin/env python3
import fileinput, re, random, sys, argparse
from functools import reduce, partial
from pprint import pprint
from random import Random
from termcolor import colored
from math import *


def main(argv):
    parser = argparse.ArgumentParser()

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--game", action="store_true")
    mode_group.add_argument("--stats", action="store_true")
    mode_group.add_argument("--helper", action="store_true")

    parser.add_argument("--dictionary-path", dest="dictionary_path", type=str, nargs=1, default="/usr/share/dict/words")
    parser.add_argument("--word-length", dest="word_length", type=int, nargs=1, default=None)
    parser.add_argument("--words", dest="known_words", type=str, nargs="+", default=None)

    loop_group = parser.add_mutually_exclusive_group(required=False)
    loop_group.add_argument("--loop", dest="loop", action="store_true", default=True)
    loop_group.add_argument("--once", dest="loop", action="store_false")

    pretty_group = parser.add_mutually_exclusive_group(required=False)
    pretty_group.add_argument("--pretty", dest="pretty", action="store_true", default=True)
    pretty_group.add_argument("--simple", dest="pretty", action="store_false")


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
            else:
                helper = InteractiveHelper(dictionary, args.word_length)
                helper.start()
    except KeyboardInterrupt:
        pass



inf = float("inf")

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


class SelfSolver:
    def run(dictionary, *args, word_length=None, seed=None, answer=None, **kwargs):
        game = WordleGame(dictionary, word_length=word_length, seed=seed, answer=answer)
        return SelfSolver(game).solve(*args, **kwargs)

    def run_loop_with_stats(*args, **kwargs):
        if "pretty_print" in kwargs:
            with_pad = not kwargs["pretty_print"]
        else:
            with_pad = False
        attempt_len = []
        sln_max_len = 0
        mintts = inf
        maxtts = -inf
        while True:
            (solution, attempts) = SelfSolver.run(*args, **kwargs)
            sln_max_len = max(sln_max_len, len(solution))
            attempt_len.append(len(attempts))
            mtts = sum(attempt_len) / len(attempt_len)
            maxtts = max(maxtts, len(attempts))
            mintts = min(mintts, len(attempts))
            stddevs = stddev(attempt_len, mtts)
            pad = " " * max(sln_max_len - len(solution), 0) if with_pad else ""
            print(f"{pad}\"{solution}\" after {len(attempts):2} ([{mintts:2} .. {mtts:2.03f} ±{stddevs:2.03f} .. {maxtts:2}]) {attempts}")

    def __init__(this, game):
        this.dictionary = game.dictionary
        this.game = game
        this.optimizer = WordChoiceOptimizer(this.dictionary)
        this.helper = CumulativeHelper(this.dictionary, game.word_length)
        this.attempts = []

    def check_and_inform(this, word):
        this.attempts.append(word)
        result = this.game.attempt(word)
        solved = WordleGame.check_attempt_solved(result)

        if solved:
            return word

        this.helper.merge_attempt_result(result)

        return False

    def solve(this, pretty_print = True):
        min_candidates = 15
        start_words = 5
        solved = False
        solution = None
        start_words = this.optimizer.starter_words(this.game.word_length, start_words)

        candidates = list(range(min_candidates+1))
        for word in start_words:
            if word in this.attempts or len(candidates) < min_candidates or solved:
                break

            solved = this.check_and_inform(word)
            if pretty_print:
                print(this.game.formatted_attempt(word))
            if solved:
                solution = solved

            candidates = this.helper.suggest()
            for p in this.attempts:
                if p in candidates:
                    candidates.remove(p)

        while not solved and len(candidates) != 0:
            word = candidates[0]

            solved = this.check_and_inform(word)
            if pretty_print:
                print(this.game.formatted_attempt(word))
            if solved:
                solution = solved

            candidates = this.helper.suggest()
            for p in this.attempts:
                if p in candidates:
                    candidates.remove(p)
        if pretty_print:
            print(f"SOLVED! \"{solution}\" after {len(this.attempts)} {this.attempts}")
        return (solution, this.attempts)


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


def chooseMax(iterable, score_function):
    currMax = None
    currScore = -inf
    for thing in iterable:
        score = score_function(thing)
        if currScore < score:
            currMax = thing
            currScore = score
    return currMax

def stddev(collection, mean=None):
    if mean is None:
        mean = sum(collection) / len(collection)
    sumsqr = sum( (pow(e - mean, 2) for e in collection) )
    return sqrt( sumsqr / len(collection))



if __name__ == "__main__":
    main(sys.argv)
