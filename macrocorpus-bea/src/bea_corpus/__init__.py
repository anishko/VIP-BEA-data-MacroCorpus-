"""BEA slice of the MacroCorpus project: fetch, standardize and profile BEA series."""

from .client import BEAClient, BEAError
from .profile import profile_corpus, profile_series, transform
from .standardize import SeriesSpec, standardize

__version__ = "0.1.0"
__all__ = ["BEAClient", "BEAError", "SeriesSpec", "standardize", "profile_corpus", "profile_series", "transform"]
