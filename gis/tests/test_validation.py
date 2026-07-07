from __future__ import annotations

from dmdt_gis import load_network, validate_full_network


class TestValidation:
    def test_full_network_validates(self):
        vr = validate_full_network()
        assert vr.valid, f"validation failed: {vr.errors}"

    def test_station_count(self):
        n = load_network()
        assert n.station_count >= 190

    def test_line_count(self):
        n = load_network()
        assert len(n.lines) == 12

    def test_all_line_codes(self):
        n = load_network()
        codes = {ln.code for ln in n.lines}
        expected = {
            "RD",
            "YL",
            "BL",
            "BR",
            "GR",
            "GB",
            "VL",
            "PK",
            "MG",
            "GY",
            "OR",
            "RM",
        }
        assert codes == expected
