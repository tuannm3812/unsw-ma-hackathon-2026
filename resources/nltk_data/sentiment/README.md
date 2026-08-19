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

**License:** `LICENSE.txt` in this directory is the upstream MIT license
text (Copyright (c) 2016 C.J. Hutto), fetched verbatim from
`cjhutto/vaderSentiment`'s own `LICENSE.txt` and included alongside the
lexicon per that license's own requirement.

**Provenance:** `vader_lexicon.zip`, SHA-256
`8adba4294eef3964d820bf655e37e61bdc3a341994356af59b74fb3b4a36ce5c`
(90,486 bytes) - copied unmodified from a local NLTK installation's
`nltk_data/sentiment/vader_lexicon.zip` (the same file
`nltk.download("vader_lexicon")` fetches), added 2026-08-19.
