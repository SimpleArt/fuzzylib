import sys
from difflib import SequenceMatcher
from typing import Any, TypeVar, Union

if sys.version_info < (3, 9):
    from typing import Dict, Iterable, Iterator, Mapping, Set, Tuple
else:
    from builtins import dict as Dict, list as List, set as Set, tuple as Tuple
    from collections.abc import Set as Iterable, Iterator, Mapping

from .fuzzy_frozen_set import FuzzySetView

VT = TypeVar("VT")


class FuzzyFrozenDict(Mapping[str, VT]):
    _items: Dict[str, VT]
    _matches: Dict[str, Set[str]]
    _tolerance: float

    def __init__(
        self,
        mapping: Union[Iterable[Tuple[str, VT]], Mapping[str, VT]],
        *,
        tolerance: float = 0.6,
    ) -> None:
        self._items = dict(mapping)
        self._matches = {}
        matcher = SequenceMatcher()
        for x in self._items:
            if x in self._matches:
                continue
            matcher.set_seq2(x)
            for key, matches in self._matches.items():
                matcher.set_seq1(key)
                if not matcher.quick_ratio() > tolerance < matcher.ratio():
                    continue
                matches.add(x)
                self._matches[x] = matches
                break
            else:
                self._matches[x] = {x}
        self._tolerance = tolerance

    def __contains__(self, x: Any) -> bool:
        return x in self._items

    def __getitem__(self, key: str) -> VT:
        return self._items[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def fuzzy(self) -> FuzzySetView[Set[str]]:
        return FuzzySetView(self._matches, self._tolerance)
