# Vendored VADER lexicon

`vader_lexicon.zip` is vendored here (not downloaded at runtime) so
sentiment scoring is reproducible on a clean checkout without a network
call: `pip install nltk` does **not** include this resource - it must
normally be fetched separately via `nltk.download("vader_lexicon")`, which
this project's tests and CLI must never do (no network access during
import or feature extraction).

`src/features.py` adds this directory to `nltk.data.path` at import time,
so `nltk.data.find("sentiment/vader_lexicon.zip")` locates it exactly as
if `nltk.download("vader_lexicon")` had already been run - no setup step
required, and behavior is identical on every machine instead of silently
depending on whether that download happened to occur already.

Source: NLTK's own distribution of the VADER lexicon (C.J. Hutto and
Eric Gilbert, "VADER: A Parsimonious Rule-based Model for Sentiment
Analysis of Social Media Text," ICWSM-14, 2014), MIT-licensed in its
original repository (cjhutto/vaderSentiment). Unmodified from the copy
`nltk.download("vader_lexicon")` itself provides.
