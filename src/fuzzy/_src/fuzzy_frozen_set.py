import sys
from difflib import SequenceMatcher
from typing import Any, Generic, TypeVar

if sys.version_info < (3, 9):
    from typing import AbstractSet, Dict, Iterable, Iterator, List
else:
    from builtins import dict as Dict, list as List
    from collections.abc import Set as AbstractSet, Iterable, Iterator

T = TypeVar("T", bound=Iterable)


class FuzzySetView(Generic[T]):
    _matches: Dict[str, T]
    _tolerance: float

    def __init__(self, matches: Dict[str, T], tolerance: float) -> None:
        self._matches = matches
        self._tolerance = tolerance

    def __contains__(self, x: Any) -> bool:
        if not isinstance(x, str):
            return False
        elif x in self._matches:
            return True
        matcher = SequenceMatcher()
        matcher.set_seq2(x)
        for key in self._matches:
            matcher.set_seq1(key)
            if all(
                ratio() >= self._tolerance
                for ratio in (
                    matcher.real_quick_ratio,
                    matcher.quick_ratio,
                    matcher.ratio,
                )
            ):
                return True
        return False

    def __iter__(self) -> Iterator[str]:
        seen = set()
        for key, matches in self._matches.items():
            if len(matches) == 1:
                yield key
            elif id(matches) not in seen:
                yield key
                seen.add(id(matches))

    def __len__(self) -> int:
        return len({*map(id, self._matches.values())})

    def matches(self, x: str) -> T:
        if x in self._matches:
            return self._matches[x]
        matcher = SequenceMatcher()
        matcher.set_seq2(x)
        best = x
        ratio = self._tolerance
        for key in self._matches:
            matcher.set_seq1(key)
            if all(
                ratio() >= self._tolerance
                for ratio in (
                    matcher.real_quick_ratio,
                    matcher.quick_ratio,
                    matcher.ratio,
                )
            ):
                best = key
                ratio = matcher.ratio()
        if best is not x:
            return self._matches[best]
        raise KeyError(x)


class FuzzyFrozenSet(AbstractSet[str]):
    _matches: Dict[str, List[str]]
    _tolerance: float

    def __init__(self, iterable: Iterable[str], *, tolerance: float = 0.6) -> None:
        self._matches = {}
        matcher = SequenceMatcher()
        for x in iterable:
            if x in self._matches:
                continue
            matcher.set_seq2(x)
            for key, matches in self._matches.items():
                matcher.set_seq1(key)
                if any(
                    ratio() < tolerance
                    for ratio in (
                        matcher.real_quick_ratio,
                        matcher.quick_ratio,
                        matcher.ratio,
                    )
                ):
                    continue
                matches.append(x)
                self._matches[x] = matches
                break
            else:
                self._matches[x] = [x]
        self._tolerance = tolerance

    def __contains__(self, x: Any) -> bool:
        return isinstance(x, str) and x in self._matches

    def __iter__(self) -> Iterator[str]:
        return iter(self._matches)

    def __len__(self) -> int:
        return len(self._matches)

    def fuzzy(self) -> FuzzySetView[List[str]]:
        return FuzzySetView(self._matches, self._tolerance)
