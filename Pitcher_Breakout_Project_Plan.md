# Which Pitcher Breakouts Will Last?

## Project question

Can a pitcher’s performance and pitch characteristics through June 30 help predict their strikeout rate minus walk rate (K-BB%) from July onward? The goal is to identify apparent early-season improvements that have a better chance of continuing.

## Why it matters

A baseball operations group may need to decide whether a pitcher’s strong first half reflects a meaningful change or a short stretch of good results. This project will produce predictions and a brief player report that explains the evidence behind them.

## Data and scope

Use publicly available MLB Statcast data. Each observation will be one pitcher in one season. Build features using only games through June 30; calculate the outcome using games from July 1 onward. Start with pitchers who have enough first-half opportunities to measure their performance, and report how many cannot be evaluated because they have limited second-half playing time.

## Approach

Measure first-half K-BB%, swing-and-miss rate, velocity, pitch mix, and pitch movement. Fit a simple statistical model to predict second-half K-BB%. Compare it with two baselines: using first-half K-BB% alone and pulling that rate toward the league average.

Use forward checks in 2023 and 2024 to choose the approach, inspect the chosen model on 2025 as a development readout, and hold out 2026 for the final evaluation. Judge the predictions by their average error and by how well they rank pitchers. Show examples where the model succeeds and fails.

## Final deliverables

- Reproducible Python code and documented data-cleaning steps
- A short explanation of the model and its results against the baselines
- A scouting-style report for a few pitchers, with predictions, supporting evidence, and uncertainty

## Limits

The model can test whether patterns predict later performance; it cannot prove that a new pitch or velocity change *caused* an improvement. Injuries, changing roles, and pitchers with little second-half playing time may affect the results and will be discussed explicitly.

**Success criterion:** The project is successful if it gives an honest, reproducible answer to the question—even if the more complex model does not beat the simple baselines.
