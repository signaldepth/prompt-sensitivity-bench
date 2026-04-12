# Methodology

The benchmark uses deterministic programming tasks with executable tests. A model receives a prompt, returns Python code, and the harness runs the generated function against fixed test cases.

## Current Task Set

- fizzbuzz
- reverse_words
- flatten
- two_sum
- run_length_encode
- chunk_list

## Sampling

The default is `k=3` per condition. Single-shot measurements are not accepted for contributed runs because boundary models can flip conclusions between k=1 and repeated trials.

## Temperature

The default temperature is `0.0` to isolate prompt effects from sampling variance.

## Evaluation

The harness extracts a Python function from the model response, executes it in a subprocess, and compares the printed representation of the result with the expected value.

## Scope

In scope: prompt specificity, delimiter format, prompt complexity, compression sensitivity, and deterministic coding tasks.

Out of scope: human preference, safety evaluation, multi-turn chat dynamics, image/audio tasks, and general capability ranking.
