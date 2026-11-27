"""PID controller: decides how much heater power to use to hold a temperature."""


class PID:
    def __init__(self, kp: float = 0.08, ki: float = 0.002, kd: float = 0.0,
                 out_min: float = 0.0, out_max: float = 1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self.integral = 0.0
        self.prev_error: float | None = None

    def reset(self) -> None:
        self.integral = 0.0
        self.prev_error = None

    def update(self, target: float, measured: float, dt: float) -> float:
        error = target - measured
        derivative = 0.0 if self.prev_error is None else (error - self.prev_error) / dt
        self.prev_error = error

        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        # anti-windup: only integrate when not saturated
        if self.out_min < output < self.out_max:
            self.integral += error * dt
        return max(self.out_min, min(self.out_max, output))
