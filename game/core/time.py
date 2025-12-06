# AUTHORED BY: Scott Petty
# Class: FixedClock

# converts real dt into a number of fixed simulation steps
# used to make sure we get deterministic, stable physics/logic ticks

class FixedClock:
    def __init__(self) -> None:
        self.accum = 0.0 # this is left-over time we havent simulated yet

    # add this frames real time to the accumulator and return how many fixed
    # simulation steps we should run. any remainder stays in the accumulator
    def step(self, real_dt: float, fixed_dt: float) -> int:
        self.accum += real_dt
        steps = 0
        while self.accum >= fixed_dt:
            self.accum -= fixed_dt
            steps += 1
        return steps
