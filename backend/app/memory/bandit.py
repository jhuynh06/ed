from dataclasses import dataclass
import numpy as np
import time

SUCCESS_THRESHOLD = 15.0


@dataclass
class BetaPrior:
    alpha: float = 1.0
    beta: float = 1.0

    def sample(self) -> float:
        return float(np.random.beta(self.alpha, self.beta))

    def update(self, success: bool) -> None:
        if success:
            self.alpha += 1.0
        else:
            self.beta += 1.0


class RecipeBandit:
    """Thompson sampling bandit over comfort recipes, stratified by time-of-day."""

    def __init__(self) -> None:
        self._priors: dict[str, dict[int, BetaPrior]] = {}

    def _bucket(self, hour: int | None = None) -> int:
        h = hour if hour is not None else time.localtime().tm_hour
        return h // 6

    def register_recipe(self, recipe_id: str) -> None:
        """Register a recipe with uniform priors across all time buckets."""
        if recipe_id not in self._priors:
            self._priors[recipe_id] = {b: BetaPrior() for b in range(4)}

    def select(self, candidate_ids: list[str], hour: int | None = None) -> str:
        """Thompson sample: return recipe_id with highest sampled reward."""
        for rid in candidate_ids:
            self.register_recipe(rid)
        bucket = self._bucket(hour)
        return max(candidate_ids, key=lambda rid: self._priors[rid][bucket].sample())

    def update(self, recipe_id: str, success: bool, hour: int | None = None) -> None:
        """Update Beta prior for the recipe in the current time bucket."""
        self.register_recipe(recipe_id)
        self._priors[recipe_id][self._bucket(hour)].update(success)


_bandit = RecipeBandit()


def select_recipe(candidate_ids: list[str], hour: int | None = None) -> str:
    return _bandit.select(candidate_ids, hour)


def update_recipe(recipe_id: str, success: bool, hour: int | None = None) -> None:
    _bandit.update(recipe_id, success, hour)
