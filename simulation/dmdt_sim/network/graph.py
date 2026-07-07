from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..types import Direction


class NetworkGraph:
    def __init__(self) -> None:
        self.lines: dict[str, dict[str, Any]] = {}
        self.stations: dict[str, dict[str, Any]] = {}
        self.platforms: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.track_segments: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.depots: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.junctions: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.train_classes: list[dict[str, Any]] = []
        self._adjacency: dict[str, dict[str, list[tuple[str, str, float, str]]]] = {}
        self._line_stations: dict[str, list[dict[str, Any]]] = {}

    def add_line(self, data: dict[str, Any]) -> None:
        self.lines[data["code"]] = data

    def add_station(self, station: dict[str, Any]) -> None:
        code = station["code"]
        self.stations[code] = station
        self._line_stations.setdefault(station["line_code"], []).append(station)

    def add_track_segment(self, segment: dict[str, Any]) -> None:
        lc = segment["line_code"]
        self.track_segments[lc].append(segment)

    def add_depot(self, depot: dict[str, Any]) -> None:
        self.depots[depot["line_code"]].append(depot)

    def add_platform(self, platform: dict[str, Any]) -> None:
        self.platforms[platform["station_id"]].append(platform)

    def add_junction(self, junction: dict[str, Any]) -> None:
        self.junctions[junction["line_code"]].append(junction)

    def add_train_class(self, tc: dict[str, Any]) -> None:
        self.train_classes.append(tc)

    def build_graph(self) -> None:
        self._adjacency = {}
        for lc, segments in self.track_segments.items():
            line = self.lines.get(lc)
            if not line:
                continue
            dir_map: dict[str, dict[str, list[tuple[str, str, float, str]]]] = {
                Direction.UP.value: defaultdict(list),
                Direction.DOWN.value: defaultdict(list),
            }
            for seg in segments:
                direction = seg.get("direction", Direction.UP.value)
                from_s = seg.get("from_station_code", "")
                to_s = seg.get("to_station_code", "")
                length = seg.get("length_m", 0.0)
                d = direction
                dir_map[d][from_s].append((to_s, lc, length, d))
                opp = Direction.DOWN.value if d == Direction.UP.value else Direction.UP.value
                dir_map[opp][to_s].append((from_s, lc, length, opp))
            for dn, adj in dir_map.items():
                key = f"{lc}:{dn}"
                self._adjacency[key] = dict(adj)

    def get_stations_on_line(self, line_code: str) -> list[dict[str, Any]]:
        stns = self._line_stations.get(line_code, [])
        stns.sort(key=lambda s: s.get("sequence", 0))
        return stns

    def find_path(
        self,
        from_station: str,
        to_station: str,
        direction: Direction | None = None,
    ) -> list[tuple[str, str, str]]:
        visited: set[str] = set()
        queue: list[list[tuple[str, str, str]]] = [[(from_station, "", "")]]
        while queue:
            path = queue.pop(0)
            current = path[-1][0]
            if current == to_station:
                return path
            if current in visited:
                continue
            visited.add(current)
            for lc, adj in self._adjacency.items():
                line_code, dn = lc.split(":")
                if direction and dn != direction.value:
                    continue
                for neighbor, seg_line, seg_len, seg_dir in adj.get(current, []):
                    if seg_line == line_code and seg_dir == dn:
                        new_path = path + [(neighbor, line_code, dn)]
                        queue.append(new_path)
        return []

    def find_transfer_path(
        self, from_station: str, to_station: str
    ) -> list[tuple[str, str, str]]:
        if from_station not in self.stations or to_station not in self.stations:
            return []
        visited_stations: set[str] = set()
        queue: list[list[tuple[str, str, str]]] = [[(from_station, "", "")]]
        while queue:
            path = queue.pop(0)
            current = path[-1][0]
            if current == to_station:
                return path
            if current in visited_stations:
                continue
            visited_stations.add(current)
            current_station = self.stations.get(current, {})
            current_line = current_station.get("line_code", "")
            for lc, adj in self._adjacency.items():
                line_code, dn = lc.split(":")
                for neighbor, seg_line, seg_len, seg_dir in adj.get(current, []):
                    if seg_line != line_code:
                        continue
                    if current_line and seg_line != current_line:
                        continue
                    station = self.stations.get(neighbor, {})
                    new_line = station.get("line_code", seg_line)
                    new_path = path + [(neighbor, new_line, dn)]
                    queue.append(new_path)
        return []

    def get_interchange_stations(self) -> dict[str, list[str]]:
        station_lines: dict[str, set[str]] = defaultdict(set)
        for code, stn in self.stations.items():
            station_lines[code].add(stn.get("line_code", ""))
        for code, stn in self.stations.items():
            for j in self.junctions.get(stn.get("line_code", ""), []):
                if j.get("station_id", "") == stn.get("id", ""):
                    for lc in j.get("lines", "").split(","):
                        lc = lc.strip()
                        if lc:
                            station_lines[code].add(lc)
        return {
            code: list(lines) for code, lines in station_lines.items() if len(lines) > 1
        }
