# Class: FixedClock

# converts real dt into a number of fixed simulation steps
# used to make sure we get deterministic, stable physics/logic ticks

class FixedClock:
    def __init__(self) -> None:
        self._accum = 0.0

    def step(self, real_dt: float, fixed_dt: float) -> int:
        self._accum += real_dt
        steps = 0
        while self._accum >= fixed_dt:
            self._accum -= fixed_dt
            steps += 1
        return steps
