This is why I don't get involved in little puzzle games.

# Wordle Clone with Solver

```
usage: main.py [-h] (--game | --stats | --helper)
               [--dictionary-path DICTIONARY_PATH] [--word-length WORD_LENGTH]
               [--words KNOWN_WORDS [KNOWN_WORDS ...]] [--loop | --once]
               [--pretty | --simple]

optional arguments:
  -h, --help            show this help message and exit
  --game                play a wordle game
  --stats               have the solver play sames and print solver statistics
  --helper              help you cheat at a wordle game
  --dictionary-path DICTIONARY_PATH
                        Path to a list of word available for attempts and
                        answers in a game. Defaults to ./wordle-words.txt
  --word-length WORD_LENGTH
  --words KNOWN_WORDS [KNOWN_WORDS ...]
                        set pre-defined words for solver
  --loop                run solver in infinite loop
  --once                run solver once (can use with --words)
  --pretty              run solver in pretty-print mode with highlighting
  --simple              run solver without pretty-print mode
```

## Modes

### Game Mode
Does what it says on the tin.

### Cheater-Cheater-Pumpkin-Eater Mode
Use `--helper` argument. You need to specify a word length.
It will suggest 5 starting words in descending order of utility.
The score function is:
```
sum( (dictionary.frequency_of(letter) for letter in set(word) - some_existing_letter_coverage) )
```
this gives better scores to words with increased letter coverage over previous words

### Stats Mode
Infinitely plays the game using it's own solver mechanism, printing stats about number of attempts.


## Dictionaries
You can provide any list of words.
They will all be lowercased.
There is no restriction on word length
Common dictionaries such as the unix dictionary (`/usr/share/dict/words` on macOS) can be used.
This repository provides the full wordle dictionary (both attempts and answers) in `wordle-words.txt`.
These are sorted, so you shouldn't see any spoilers.

## The Solver

### Proficiency

| Dictionary        | Mean attempts | STDDEV | trials |
|-------------------|---------------|--------|--------|
| wordle            | 5.243         | 1.511  | 23136  |
| Unix (any length) | 3.749         | 3.162  | 28270  |


## Requirements
- Python3
- termcolor
