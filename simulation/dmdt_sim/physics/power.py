from __future__ import annotations


class PowerCalculator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def tractive_effort(
        power_kw: float, speed_mps: float, efficiency: float = 0.88
    ) -> float:
        if speed_mps < 0.01:
            return 0.0
        return (power_kw * 1000 * efficiency) / speed_mps

    @staticmethod
    def tractive_power(force_n: float, speed_mps: float) -> float:
        return force_n * speed_mps / 1000.0

    @staticmethod
    def regen_power(
        force_n: float, speed_mps: float, efficiency: float = 0.85
    ) -> float:
        if force_n <= 0 or speed_mps <= 0:
            return 0.0
        return force_n * speed_mps * efficiency / 1000.0

    @staticmethod
    def air_drag_power(
        speed_mps: float, drag_coefficient: float = 0.5, frontal_area: float = 10.0
    ) -> float:
        if speed_mps < 0.01:
            return 0.0
        rho = 1.225
        force = 0.5 * rho * drag_coefficient * frontal_area * speed_mps * speed_mps
        return force * speed_mps / 1000.0

    @staticmethod
    def energy_consumption_kwh(
        power_kw: float,
        time_s: float,
    ) -> float:
        return power_kw * (time_s / 3600.0)

    @staticmethod
    def specific_energy(
        energy_kwh: float,
        mass_tonnes: float,
        distance_km: float,
    ) -> float:
        if distance_km <= 0:
            return 0.0
        return energy_kwh / (mass_tonnes * distance_km)
