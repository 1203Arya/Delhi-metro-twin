from __future__ import annotations

import math
from enum import Enum, auto

from ..types import MotionState, TrainSpec


class DrivingMode(Enum):
    ACCELERATING = auto()
    CRUISING = auto()
    COASTING = auto()
    BRAKING = auto()
    STOPPED = auto()


class TrainMotionModel:
    def __init__(self, spec: TrainSpec, seed: int = 42) -> None:
        self.spec = spec
        self.state = MotionState()
        self.mode = DrivingMode.STOPPED
        self.target_speed_mps: float = 0.0
        self.braking_target_position: float = float("inf")
        self._rng = __import__("random").Random(seed)

    @property
    def speed_kmh(self) -> float:
        return self.state.speed_mps * 3.6

    @property
    def max_speed_mps(self) -> float:
        return self.spec.max_speed_kmh / 3.6

    def coast(self, dt: float, gradient_pct: float = 0.0) -> None:
        self.mode = DrivingMode.COASTING
        drag = self._calc_drag_force()
        grade = self._calc_grade_force(gradient_pct)
        total_force = -(drag + grade)
        a = total_force / (
            self.spec.mass_tonnes * 1000 * self.spec.rotational_inertia_factor
        )
        self.state.acceleration_mps2 = max(a, -self.spec.deceleration_ms2)
        self._integrate(dt)

    def accelerate(
        self,
        dt: float,
        gradient_pct: float = 0.0,
        speed_limit_mps: float = float("inf"),
    ) -> None:
        self.mode = DrivingMode.ACCELERATING
        effective_limit = min(speed_limit_mps, self.max_speed_mps)
        if self.state.speed_mps >= effective_limit:
            self.cruise(dt, gradient_pct, effective_limit)
            return
        drag = self._calc_drag_force()
        grade = self._calc_grade_force(gradient_pct)
        power_limit_a = self._calc_power_limit_accel()
        a_requested = min(self.spec.acceleration_ms2, power_limit_a)
        total_force = (
            a_requested
            * self.spec.mass_tonnes
            * 1000
            * self.spec.rotational_inertia_factor
        )
        net_force = total_force - drag - grade
        a = net_force / (
            self.spec.mass_tonnes * 1000 * self.spec.rotational_inertia_factor
        )
        a = min(a, self.spec.acceleration_ms2)
        if self.state.speed_mps + a * dt > effective_limit:
            a = (effective_limit - self.state.speed_mps) / dt
            a = max(a, 0.0)
        self.state.acceleration_mps2 = a
        self._integrate(dt)
        if self.state.speed_mps >= effective_limit:
            self.state.speed_mps = effective_limit

    def cruise(
        self,
        dt: float,
        gradient_pct: float = 0.0,
        target_speed_mps: float | None = None,
    ) -> None:
        self.mode = DrivingMode.CRUISING
        target = (
            target_speed_mps if target_speed_mps is not None else self.state.speed_mps
        )
        target = min(target, self.max_speed_mps)
        self._calc_drag_force()
        self._calc_grade_force(gradient_pct)
        if self.state.speed_mps < target:
            a = (target - self.state.speed_mps) / dt
            a = min(a, self.spec.acceleration_ms2)
            self.state.acceleration_mps2 = a
        elif self.state.speed_mps > target:
            a = (target - self.state.speed_mps) / dt
            a = max(a, -self.spec.deceleration_ms2)
            self.state.acceleration_mps2 = a
        else:
            self.state.acceleration_mps2 = 0.0
        self._integrate(dt)

    def brake(
        self, dt: float, gradient_pct: float = 0.0, service_brake: bool = True
    ) -> None:
        self.mode = DrivingMode.BRAKING
        brake_rate = (
            self.spec.deceleration_ms2
            if service_brake
            else self.spec.deceleration_ms2 * 1.3
        )
        grade = self._calc_grade_force(gradient_pct)
        grade_a = grade / (
            self.spec.mass_tonnes * 1000 * self.spec.rotational_inertia_factor
        )
        drag = self._calc_drag_force()
        drag_a = drag / (
            self.spec.mass_tonnes * 1000 * self.spec.rotational_inertia_factor
        )
        a = -(brake_rate + grade_a + drag_a)
        a = max(a, -self.spec.deceleration_ms2 * 1.5)
        self.state.acceleration_mps2 = a
        self._integrate(dt)
        if self.state.speed_mps < 0:
            self.state.speed_mps = 0.0
            self.state.acceleration_mps2 = 0.0
            self.mode = DrivingMode.STOPPED

    def emergency_brake(self, dt: float, gradient_pct: float = 0.0) -> None:
        self.state.acceleration_mps2 = -self.spec.deceleration_ms2 * 1.5
        self._integrate(dt)
        if self.state.speed_mps < 0:
            self.state.speed_mps = 0.0
            self.state.acceleration_mps2 = 0.0
            self.mode = DrivingMode.STOPPED

    def brake_to_stop(
        self, dt: float, distance_to_stop_m: float, gradient_pct: float = 0.0
    ) -> None:
        if distance_to_stop_m <= 0:
            self.state.speed_mps = 0.0
            self.state.acceleration_mps2 = 0.0
            self.mode = DrivingMode.STOPPED
            return
        v0 = self.state.speed_mps
        required_decel = (v0 * v0) / (2 * distance_to_stop_m)
        required_decel = min(required_decel, self.spec.deceleration_ms2 * 1.3)
        if required_decel > 0.01:
            a = -required_decel
            grade = self._calc_grade_force(gradient_pct)
            grade_a = grade / (
                self.spec.mass_tonnes * 1000 * self.spec.rotational_inertia_factor
            )
            a -= grade_a
            self.state.acceleration_mps2 = max(a, -self.spec.deceleration_ms2 * 1.5)
            self._integrate(dt)
            if self.state.speed_mps < 0:
                self.state.speed_mps = 0.0
                self.state.acceleration_mps2 = 0.0
                self.mode = DrivingMode.STOPPED
        else:
            self.state.acceleration_mps2 = 0.0

    def brake_distance(self, speed_mps: float | None = None) -> float:
        v = speed_mps if speed_mps is not None else self.state.speed_mps
        return (v * v) / (2 * self.spec.deceleration_ms2)

    def _calc_drag_force(self) -> float:
        v = self.state.speed_mps
        if v < 0.01:
            return 0.0
        rho = self.spec.air_density_kgm3
        cd = self.spec.drag_coefficient
        a_f = self.spec.frontal_area_m2
        drag = 0.5 * rho * cd * a_f * v * v
        rolling = self.spec.rolling_resistance_N
        return drag + rolling

    def _calc_grade_force(self, gradient_pct: float) -> float:
        if abs(gradient_pct) < 0.001:
            return 0.0
        angle = math.atan(gradient_pct / 100.0)
        mass = self.spec.mass_tonnes * 1000
        return mass * 9.81 * math.sin(angle)

    def _calc_power_limit_accel(self) -> float:
        v = self.state.speed_mps
        if v < 0.01:
            return self.spec.acceleration_ms2
        p = self.spec.max_power_kw * 1000
        mass = self.spec.mass_tonnes * 1000 * self.spec.rotational_inertia_factor
        a_max = p / (v * mass)
        return min(a_max, self.spec.acceleration_ms2)

    def _integrate(self, dt: float) -> None:
        v0 = self.state.speed_mps
        a = self.state.acceleration_mps2
        self.state.speed_mps = v0 + a * dt
        self.state.position_m += v0 * dt + 0.5 * a * dt * dt
        self.state.distance_travelled_m += abs(v0 * dt + 0.5 * a * dt * dt)
        self.state.cumulative_energy_wh += self._calc_energy(dt)
        if self.state.speed_mps < 0:
            self.state.speed_mps = 0.0

    def _calc_energy(self, dt: float) -> float:
        p_traction = 0.0
        p_aux = self.spec.auxiliary_power_kw
        if self.mode == DrivingMode.ACCELERATING or self.mode == DrivingMode.CRUISING:
            force = (
                self.state.acceleration_mps2
                * self.spec.mass_tonnes
                * 1000
                * self.spec.rotational_inertia_factor
            )
            p_traction = max(0, force * self.state.speed_mps) / 1000
        elif self.mode == DrivingMode.BRAKING and self.state.speed_mps > 0.1:
            force = (
                abs(self.state.acceleration_mps2)
                * self.spec.mass_tonnes
                * 1000
                * self.spec.rotational_inertia_factor
            )
            p_regen = min(
                force * self.state.speed_mps * self.spec.regen_efficiency / 1000,
                self.spec.auxiliary_power_kw,
            )
            p_traction = -p_regen
        total_kw = p_traction + p_aux
        return total_kw * (dt / 3600.0)
