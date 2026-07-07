from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import geoalchemy2
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "gis"))

from dmdt_db.models import (
    Crossover,
    Depot,
    Junction,
    Line,
    Siding,
    Station,
    Switch,
    TrainClass,
)
from dmdt_db.repositories import (
    CrossoverRepository,
    DepotRepository,
    JunctionRepository,
    LineRepository,
    StationRepository,
    SwitchRepository,
    TrainClassRepository,
)


@pytest.fixture
def line(transaction):
    repo = LineRepository(transaction)
    line_obj = Line(
        code="XX",
        name="Test Line",
        number=99,
        color_hex="#000000",
        corridor="Test Corridor",
        opened_year=2020,
        operator="DMRC",
        gauge_mm=1435,
        electrification="25 kV AC OHE",
        signalling_system="ATP",
        total_length_km=10.0,
    )
    repo.add(line_obj)
    return line_obj


@pytest.fixture
def station(transaction, line):
    repo = StationRepository(transaction)
    pt = geoalchemy2.WKBElement(
        b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        srid=4326,
    )
    s = Station(
        line_code=line.code,
        code="TST",
        name="Test Station",
        location=pt,
        structure="underground",
        platforms=4,
        opened_year=2020,
        is_terminus=False,
        has_junction=True,
        coordinate_confidence="high",
        sequence=0,
        latitude=28.6314,
        longitude=77.2196,
    )
    repo.add(s)
    return s


class TestLineModel:
    def test_create_line(self, transaction, line):
        assert line.id is not None
        assert isinstance(line.id, UUID)
        assert line.code == "XX"

    def test_get_by_code(self, transaction, line):
        repo = LineRepository(transaction)
        found = repo.get_by_code("XX")
        assert found is not None
        assert found.name == "Test Line"

    def test_list_all(self, transaction, line):
        repo = LineRepository(transaction)
        lines = repo.list_all()
        assert len(lines) >= 1

    def test_unique_number(self, transaction, line):
        with pytest.raises(Exception):
            dup = Line(
                code="YY",
                name="Dup",
                number=99,
                color_hex="#000000",
                corridor="test",
                opened_year=2020,
                operator="DMRC",
                gauge_mm=1435,
                electrification="25 kV AC OHE",
                signalling_system="ATP",
                total_length_km=10,
            )
            transaction.add(dup)
            transaction.flush()

    def test_timestamps(self, transaction, line):
        assert line.created_at is not None
        assert line.updated_at is not None

    def test_repr(self, line):
        r = repr(line)
        assert "Test Line" in r


class TestStationModel:
    def test_create_station(self, transaction, line, station):
        assert station.id is not None
        assert station.code == "TST"

    def test_get_by_code(self, transaction, line, station):
        repo = StationRepository(transaction)
        stations = repo.get_by_code("TST")
        assert len(stations) == 1

    def test_list_by_line(self, transaction, line, station):
        repo = StationRepository(transaction)
        stations = repo.list_by_line("XX")
        assert len(stations) == 1

    def test_terminus_query(self, transaction, line):
        repo = StationRepository(transaction)
        pt = geoalchemy2.WKBElement(
            b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            srid=4326,
        )
        t = Station(
            line_code=line.code,
            code="TRM",
            name="Terminal",
            location=pt,
            is_terminus=True,
            sequence=99,
            latitude=28.7,
            longitude=77.2,
        )
        transaction.add(t)
        transaction.flush()
        terminals = repo.list_terminals()
        assert any(s.code == "TRM" for s in terminals)


class TestTrainClassModel:
    def test_create_train_class(self, transaction):
        repo = TrainClassRepository(transaction)
        tc = TrainClass(
            name="TestTrain",
            max_speed_kmh=80.0,
            acceleration_ms2=0.9,
            deceleration_ms2=1.1,
            length_m=208.0,
            capacity_seated=328,
            capacity_standing=1200,
        )
        repo.add(tc)
        assert tc.id is not None

    def test_unique_name(self, transaction):
        repo = TrainClassRepository(transaction)
        tc1 = TrainClass(
            name="Unique",
            max_speed_kmh=80.0,
            acceleration_ms2=0.9,
            deceleration_ms2=1.1,
            length_m=208.0,
            capacity_seated=328,
            capacity_standing=1200,
        )
        repo.add(tc1)
        with pytest.raises(Exception):
            tc2 = TrainClass(
                name="Unique",
                max_speed_kmh=80.0,
                acceleration_ms2=0.9,
                deceleration_ms2=1.1,
                length_m=208.0,
                capacity_seated=328,
                capacity_standing=1200,
            )
            repo.add(tc2)
            transaction.flush()

    def test_get_by_name(self, transaction):
        repo = TrainClassRepository(transaction)
        tc = TrainClass(
            name="FindMe",
            max_speed_kmh=80.0,
            acceleration_ms2=0.9,
            deceleration_ms2=1.1,
            length_m=208.0,
            capacity_seated=328,
            capacity_standing=1200,
        )
        repo.add(tc)
        found = repo.get_by_name("FindMe")
        assert found is not None
        assert found.max_speed_kmh == 80.0

    def test_list_all(self, transaction):
        repo = TrainClassRepository(transaction)
        repo.add(
            TrainClass(
                name="A",
                max_speed_kmh=60,
                acceleration_ms2=0.5,
                deceleration_ms2=0.5,
                length_m=100,
                capacity_seated=100,
                capacity_standing=200,
            )
        )
        repo.add(
            TrainClass(
                name="B",
                max_speed_kmh=80,
                acceleration_ms2=0.5,
                deceleration_ms2=0.5,
                length_m=100,
                capacity_seated=100,
                capacity_standing=200,
            )
        )
        all_tc = repo.list_all()
        assert len(all_tc) >= 2


class TestDepotModel:
    def test_create_depot(self, transaction, line):
        repo = DepotRepository(transaction)
        pt = geoalchemy2.WKBElement(
            b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            srid=4326,
        )
        d = Depot(
            line_code=line.code,
            name="Test Depot",
            location=pt,
            latitude=28.67,
            longitude=77.25,
            area_m2=90000,
            capacity_stabling=48,
        )
        repo.add(d)
        assert d.id is not None
        found = repo.get_by_name("Test Depot")
        assert found is not None


class TestSidingModel:
    def test_create_siding(self, transaction, line):
        depot_repo = DepotRepository(transaction)
        pt = geoalchemy2.WKBElement(
            b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            srid=4326,
        )
        d = Depot(
            line_code=line.code,
            name="Siding Depot",
            location=pt,
            latitude=28.67,
            longitude=77.25,
            area_m2=90000,
            capacity_stabling=48,
        )
        depot_repo.add(d)
        ls_geom = geoalchemy2.WKBElement(
            b"\x01\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            srid=4326,
        )
        sid = Siding(
            depot_id=d.id,
            name="Test Siding",
            geometry=ls_geom,
            length_m=200.0,
            capacity_trains=2,
        )
        transaction.add(sid)
        transaction.flush()
        assert sid.id is not None


class TestJunctionModel:
    def test_create_junction(self, transaction, line, station):
        pt = geoalchemy2.WKBElement(
            b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            srid=4326,
        )
        j = Junction(
            station_id=station.id,
            name="Test Junction",
            location=pt,
            is_interchange=True,
            is_turnout=False,
            lines="XX,YY",
        )
        transaction.add(j)
        transaction.flush()
        assert j.id is not None

        repo = JunctionRepository(transaction)
        interchanges = repo.list_interchanges()
        assert any(j.name == "Test Junction" for j in interchanges)


class TestCrossoverModel:
    def test_create_crossover(self, transaction, line, station):
        ls_geom = geoalchemy2.WKBElement(
            b"\x01\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            srid=4326,
        )
        c = Crossover(
            line_code=line.code,
            station_id=station.id,
            geometry=ls_geom,
            heading_deg=90.0,
        )
        transaction.add(c)
        transaction.flush()
        assert c.id is not None

        repo = CrossoverRepository(transaction)
        by_line = repo.list_by_line("XX")
        assert len(by_line) == 1
        by_station = repo.list_by_station(station.id)
        assert len(by_station) == 1


class TestSwitchModel:
    def test_create_switch(self, transaction, line, station):
        pt = geoalchemy2.WKBElement(
            b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            srid=4326,
        )
        j = Junction(
            station_id=station.id,
            name="Switch Junction",
            location=pt,
            is_interchange=False,
            is_turnout=True,
            lines="XX",
        )
        transaction.add(j)
        transaction.flush()

        sw = Switch(
            line_code=line.code,
            junction_id=j.id,
            location=pt,
            switch_label="entry",
            heading_deg=0.0,
        )
        transaction.add(sw)
        transaction.flush()
        assert sw.id is not None

        repo = SwitchRepository(transaction)
        by_junction = repo.list_by_junction(j.id)
        assert len(by_junction) == 1
