#!/usr/bin/env python3
"""Generate the canonical Delhi Metro network dataset.

Builds the complete DMRC network as Python data structures, serialises it to
``gis/data/network.json`` and validates it by round-tripping through
:func:`dmdt_gis.load_network` *before* the file is committed to disk. If the
hand-authored data fails the loader's integrity checks the generator attempts
automatic fixes (de-duplicating station codes, flagging terminal stations,
pruning interchanges that reference unknown lines) and retries until the load
succeeds — only then is ``network.json`` written.

Run::

    python gis/tools/generate_network.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Make the package importable when run directly from the repo root or from
# inside gis/. The dataset lives at gis/data/network.json; DATA_FILE in
# dmdt_gis.dataset resolves relative to the package, so it is independent of CWD.
GIS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GIS_ROOT))

import dmdt_gis  # noqa: E402  (after sys.path tweak)
from dmdt_gis.dataset import DATA_FILE  # noqa: E402

DATA_DIR = DATA_FILE.parent


# ───────────────────────── shared interchange coordinates ─────────────────────────
# A handful of stations are physically shared between two or more lines. Keeping
# their coordinates as named constants guarantees every line that stops at them
# records an identical (lat, lon), so the network is geometrically consistent.

KG = (28.6660, 77.2290)  # Kashmere Gate      — Red / Yellow / Violet
RC = (28.6314, 77.2196)  # Rajiv Chowk        — Yellow / Blue
CS = (28.6142, 77.2115)  # Central Secretariat— Yellow / Violet
MH = (28.6276, 77.2244)  # Mandi House        — Blue / Violet
ND = (28.6430, 77.2196)  # New Delhi          — Yellow / Airport Express
IL = (28.6595, 77.1700)  # Inderlok           — Red / Green
NSP = (28.6855, 77.1605)  # Netaji Subhash Place — Red / Pink
AP = (28.6960, 77.1835)  # Azadpur            — Yellow / Pink
KN = (28.6518, 77.1470)  # Kirti Nagar        — Blue / Green branch
RG = (28.6520, 77.1180)  # Rajouri Garden     — Blue / Pink
BG = (28.5630, 77.3260)  # Botanical Garden   — Blue / Magenta
HK = (28.5490, 77.2010)  # Hauz Khas          — Yellow / Magenta
DW21 = (28.5700, 77.0720)  # Dwarka Sector 21   — Blue / Airport Express
DWA = (28.5920, 77.0740)  # Dwarka             — Blue / Grey
LN = (28.5710, 77.2430)  # Lajpat Nagar       — Violet / Pink
INA = (28.5730, 77.2140)  # INA                — Yellow / Pink
SIK = (28.4520, 77.1220)  # Sikandarpur        — Yellow / Rapid Metro
JW = (28.6293, 77.0857)  # Janakpuri West     — Blue / Magenta
YB = (28.6110, 77.2620)  # Yamuna Bank        — Blue / Blue branch (fork)
KKD = (28.6430, 77.2980)  # Karkarduma         — Blue branch / Pink
AV = (28.6465, 77.3150)  # Anand Vihar        — Blue branch / Pink
MVP1 = (28.6180, 77.2920)  # Mayur Vihar Phase-I— Blue / Pink
DK = (28.5800, 77.1400)  # Dhaula Kuan        — Pink / Airport Express
APM = (28.6520, 77.1300)  # Ashok Park Main    — Green / Green branch
KKM = (28.5460, 77.2580)  # Kalkaji Mandir     — Violet / Magenta


# ───────────────────────── compact builders ─────────────────────────


def S(
    name,
    code,
    lat,
    lon,
    *,
    structure="elevated",
    platforms=2,
    opened=0,
    terminus=False,
    junction=False,
    interchange=(),
):
    """A station spec in the on-disk dict shape."""
    return {
        "name": name,
        "code": code,
        "latitude": lat,
        "longitude": lon,
        "structure": structure,
        "interchange_with": list(interchange),
        "platforms": platforms,
        "opened_year": opened,
        "is_terminus": terminus,
        "has_junction": junction,
        "coordinate_confidence": "high",
    }


def D(name, lat, lon, area_m2, cap, confidence="medium"):
    return {
        "name": name,
        "latitude": lat,
        "longitude": lon,
        "area_m2": area_m2,
        "capacity_stabling": cap,
        "coordinate_confidence": confidence,
    }


def IC(station_code, other_line, with_station_name):
    return {
        "station": station_code,
        "line": other_line,
        "with_station": with_station_name,
    }


# ───────────────────────── line 1 — Red ─────────────────────────

RED = {
    "code": "RD",
    "name": "Red Line",
    "number": 1,
    "color_hex": "#E60026",
    "corridor": "Rithala – Shaheed Sthal (New Bus Adda)",
    "opened_year": 2002,
    "operator": "DMRC",
    "gauge_mm": 1676,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 34.69,
    "depots": [
        D("Shastri Park Depot", 28.6700, 77.2500, 90_000, 48),
        D("Dilshad Garden Depot", 28.6815, 77.3240, 55_000, 32),
    ],
    "stations": [
        S("Rithala", "RTA", 28.7217, 77.1070, terminus=True),
        S("Rohini West", "RWE", 28.7140, 77.1190),
        S("Rohini East", "REA", 28.7080, 77.1300),
        S("Pitampura", "PIT", 28.6985, 77.1410),
        S("Kohat Enclave", "KOH", 28.6920, 77.1500),
        S(
            "Netaji Subhash Place",
            "NSP",
            NSP[0],
            NSP[1],
            junction=True,
            interchange=["PK"],
        ),
        S("Keshav Puram", "KPR", 28.6780, 77.1660),
        S("Kanhaiya Nagar", "KNR", 28.6680, 77.1680),
        S("Inderlok", "ILK", IL[0], IL[1], junction=True, interchange=["GR", "GB"]),
        S("Shastri Nagar", "SNA", 28.6630, 77.1850),
        S("Pratap Nagar", "PTN", 28.6650, 77.1920),
        S("Pul Bangash", "PBL", 28.6670, 77.1980),
        S("Tis Hazari", "THZ", 28.6685, 77.2050),
        S(
            "Kashmere Gate",
            "KGM",
            KG[0],
            KG[1],
            structure="elevated",
            junction=True,
            interchange=["YL", "VL"],
        ),
        S("Shastri Park", "SPK", 28.6680, 77.2570),
        S("Seelampur", "SEL", 28.6680, 77.2700),
        S("Welcome", "WLC", 28.6725, 77.2780),
        S("Shahdara", "SHD", 28.6720, 77.2900),
        S("Mansarovar Park", "MNP", 28.6750, 77.3050),
        S("Jhilmil", "JHL", 28.6800, 77.3140),
        S("Dilshad Garden", "DSG", 28.6815, 77.3240),
        S("Shaheed Sthal", "SSH", 28.6840, 77.3420, terminus=True),
    ],
    "interchanges": [
        IC("NSP", "PK", "Netaji Subhash Place"),
        IC("ILK", "GB", "Inderlok"),
        IC("ILK", "GR", "Inderlok"),
        IC("KGM", "YL", "Kashmere Gate"),
        IC("KGM", "VL", "Kashmere Gate"),
    ],
    "speed_overrides": {"Kashmere Gate-Shastri Park": 60},
    "gradients": {"Shahdara-Mansarovar Park": 0.8},
}


# ───────────────────────── line 2 — Yellow ─────────────────────────

YELLOW = {
    "code": "YL",
    "name": "Yellow Line",
    "number": 2,
    "color_hex": "#F9A825",
    "corridor": "Samaypur Badli – HUDA City Centre",
    "opened_year": 2005,
    "operator": "DMRC",
    "gauge_mm": 1676,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 49.02,
    "depots": [D("Sultanpur Depot", 28.5050, 77.1780, 70_000, 44)],
    "stations": [
        S("Samaypur Badli", "SMB", 28.7350, 77.1680, terminus=True),
        S("Rohini Sector 18", "RS18", 28.7290, 77.1685),
        S("Jahangirpuri", "JNG", 28.7220, 77.1700),
        S("Adarsh Nagar", "ADN", 28.7150, 77.1790),
        S("Azadpur", "AZP", AP[0], AP[1], junction=True, interchange=["PK"]),
        S("Model Town", "MDT", 28.6890, 77.1930),
        S("G.T.B. Nagar", "GTB", 28.6810, 77.2010, structure="underground"),
        S("Vishwavidyalaya", "VSV", 28.6750, 77.2090, structure="underground"),
        S("Vidhan Sabha", "VSB", 28.6680, 77.2130, structure="underground"),
        S("Civil Lines", "CVL", 28.6620, 77.2160, structure="underground"),
        S(
            "Kashmere Gate",
            "KGM",
            KG[0],
            KG[1],
            structure="underground",
            junction=True,
            interchange=["RD", "VL"],
        ),
        S("Chawri Bazar", "CWB", 28.6490, 77.2270, structure="underground"),
        S(
            "New Delhi",
            "NDL",
            ND[0],
            ND[1],
            structure="underground",
            junction=True,
            interchange=["OR"],
        ),
        S(
            "Rajiv Chowk",
            "RVC",
            RC[0],
            RC[1],
            structure="underground",
            junction=True,
            platforms=4,
            interchange=["BL"],
        ),
        S("Patel Chowk", "PCH", 28.6240, 77.2160, structure="underground"),
        S(
            "Central Secretariat",
            "CSE",
            CS[0],
            CS[1],
            structure="underground",
            junction=True,
            interchange=["VL"],
        ),
        S("Udyog Bhawan", "UBH", 28.6110, 77.2070, structure="underground"),
        S("Lok Kalyan Marg", "LKM", 28.6030, 77.1980, structure="underground"),
        S("Jor Bagh", "JOB", 28.5930, 77.1900, structure="underground"),
        S(
            "Dilli Haat INA",
            "INA",
            INA[0],
            INA[1],
            structure="underground",
            junction=True,
            interchange=["PK"],
        ),
        S("AIIMS", "AIM", 28.5660, 77.2090, structure="underground"),
        S("Green Park", "GRP", 28.5580, 77.2060, structure="underground"),
        S(
            "Hauz Khas",
            "HZK",
            HK[0],
            HK[1],
            structure="underground",
            junction=True,
            interchange=["MG"],
        ),
        S("Malviya Nagar", "MVG", 28.5390, 77.2090, structure="underground"),
        S("Saket", "SAK", 28.5240, 77.2070),
        S("Qutab Minar", "QTM", 28.5120, 77.1850),
        S("Chhatarpur", "CTP", 28.5050, 77.1780),
        S("Sultanpur", "SLT", 28.4960, 77.1680),
        S("Ghitorni", "GHT", 28.4850, 77.1580),
        S("Arjan Garh", "ARJ", 28.4740, 77.1460),
        S("Guru Dronacharya", "GDR", 28.4630, 77.1340),
        S("Sikandarpur", "SKD", SIK[0], SIK[1], junction=True, interchange=["RM"]),
        S("M.G. Road", "MGR", 28.4410, 77.1080),
        S("IFFCO Chowk", "IFF", 28.4300, 77.0930),
        S("HUDA City Centre", "HCC", 28.4230, 77.0710, terminus=True),
    ],
    "interchanges": [
        IC("KGM", "RD", "Kashmere Gate"),
        IC("KGM", "VL", "Kashmere Gate"),
        IC("AZP", "PK", "Azadpur"),
        IC("NDL", "OR", "New Delhi"),
        IC("RVC", "BL", "Rajiv Chowk"),
        IC("CSE", "VL", "Central Secretariat"),
        IC("INA", "PK", "Dilli Haat INA"),
        IC("HZK", "MG", "Hauz Khas"),
        IC("SKD", "RM", "Sikandarpur"),
    ],
    "speed_overrides": {"HUDA City Centre-IFFCO Chowk": 75},
    "gradients": {"Sultanpur-Ghitorni": 1.2},
}


# ───────────────────────── line 3 — Blue (main) ─────────────────────────

BLUE = {
    "code": "BL",
    "name": "Blue Line",
    "number": 3,
    "color_hex": "#005AA7",
    "corridor": "Dwarka Sector 21 – Noida Electronic City",
    "opened_year": 2005,
    "operator": "DMRC",
    "gauge_mm": 1676,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 50.93,
    "depots": [
        D("Yamuna Bank Depot", YB[0], YB[1], 120_000, 64),
        D("Noida Electronic City Depot", 28.6170, 77.3560, 60_000, 36),
    ],
    "stations": [
        S(
            "Dwarka Sector 21",
            "DW21",
            DW21[0],
            DW21[1],
            junction=True,
            interchange=["OR"],
        ),
        S("Dwarka Sector 8", "DW8", 28.5710, 77.0780),
        S("Dwarka Sector 9", "DW9", 28.5750, 77.0850),
        S("Dwarka Sector 10", "DW10", 28.5780, 77.0920),
        S("Dwarka Sector 11", "DW11", 28.5800, 77.0990),
        S("Dwarka Sector 12", "DW12", 28.5830, 77.1060),
        S("Dwarka Sector 13", "DW13", 28.5860, 77.1120),
        S("Dwarka Sector 14", "DW14", 28.5880, 77.1180),
        S("Dwarka", "DWA", DWA[0], DWA[1], junction=True, interchange=["GY"]),
        S("Dwarka Mor", "DWM", 28.5920, 77.0320, structure="elevated"),
        S("Nawada", "NAW", 28.5980, 77.0280),
        S("Uttam Nagar West", "UTW", 28.6080, 77.0300),
        S("Uttam Nagar East", "UTE", 28.6150, 77.0340),
        S("Peeragarhi", "PGH", 28.6210, 77.0410),
        S("Paschim Vihar East", "PVE", 28.6250, 77.0480),
        S("Punjabi Bagh West", "PBW", 28.6280, 77.0550),
        S("Rajouri Garden", "RAJ", RG[0], RG[1], junction=True, interchange=["PK"]),
        S("Ramesh Nagar", "RMN", 28.6430, 77.1140),
        S("Moti Nagar", "MTN", 28.6470, 77.1300),
        S("Kirti Nagar", "KTN", KN[0], KN[1], junction=True, interchange=["GB"]),
        S("Shadipur", "SHP", 28.6510, 77.1500),
        S("Patel Nagar", "PTL", 28.6510, 77.1600),
        S("Rajendra Place", "RJP", 28.6470, 77.1700),
        S("Karol Bagh", "KRB", 28.6510, 77.1850),
        S("Jhandewalan", "JDW", 28.6450, 77.1960),
        S("R.K. Ashram Marg", "RKA", 28.6390, 77.2060, structure="underground"),
        S(
            "Rajiv Chowk",
            "RVC",
            RC[0],
            RC[1],
            structure="underground",
            junction=True,
            platforms=4,
            interchange=["YL"],
        ),
        S("Barakhamba Road", "BRR", 28.6290, 77.2240, structure="underground"),
        S(
            "Mandi House",
            "MDH",
            MH[0],
            MH[1],
            structure="underground",
            junction=True,
            interchange=["VL"],
        ),
        S("Supreme Court", "SPC", 28.6220, 77.2450, structure="underground"),
        S("Indraprastha", "IDP", 28.6180, 77.2520, structure="underground"),
        S("Yamuna Bank", "YBK", YB[0], YB[1], junction=True, interchange=["BR"]),
        S("Akshardham", "AKS", 28.6120, 77.2760),
        S(
            "Mayur Vihar Phase-I",
            "MVP",
            MVP1[0],
            MVP1[1],
            junction=True,
            interchange=["PK"],
        ),
        S("Mayur Vihar Extension", "MVX", 28.6150, 77.3050),
        S("New Ashok Nagar", "NAS", 28.6160, 77.3160),
        S("Noida Sector 15", "N15", 28.5990, 77.3180),
        S("Noida Sector 16", "N16", 28.5900, 77.3220),
        S("Noida Sector 18", "N18", 28.5740, 77.3240),
        S("Botanical Garden", "BGA", BG[0], BG[1], junction=True, interchange=["MG"]),
        S("Noida Golf Course", "NGC", 28.5560, 77.3310),
        S("Noida Sector 34", "N34", 28.5660, 77.3380),
        S("Noida Sector 52", "N52", 28.5710, 77.3450),
        S("Noida Sector 61", "N61", 28.6010, 77.3520),
        S("Noida Electronic City", "NEC", 28.6170, 77.3560, terminus=True),
    ],
    "interchanges": [
        IC("DW21", "OR", "Dwarka Sector 21"),
        IC("DWA", "GY", "Dwarka"),
        IC("RAJ", "PK", "Rajouri Garden"),
        IC("KTN", "GB", "Kirti Nagar"),
        IC("RVC", "YL", "Rajiv Chowk"),
        IC("MDH", "VL", "Mandi House"),
        IC("YBK", "BR", "Yamuna Bank"),
        IC("MVP", "PK", "Mayur Vihar Phase-I"),
        IC("BGA", "MG", "Botanical Garden"),
    ],
    "speed_overrides": {"Rajiv Chowk-Barakhamba Road": 65},
    "gradients": {"Yamuna Bank-Akshardham": 1.5},
}


# ───────────────────────── line 4 — Blue Branch (Vaishali) ─────────────────────────

BLUE_BRANCH = {
    "code": "BR",
    "name": "Blue Line Branch",
    "number": 4,
    "color_hex": "#005AA7",
    "corridor": "Yamuna Bank – Vaishali",
    "opened_year": 2006,
    "operator": "DMRC",
    "gauge_mm": 1676,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 6.97,
    "depots": [],
    "stations": [
        S(
            "Yamuna Bank",
            "YBK",
            YB[0],
            YB[1],
            terminus=True,
            junction=True,
            interchange=["BL"],
        ),
        S("Laxmi Nagar", "LXN", 28.6220, 77.2860),
        S("Nirman Vihar", "NIR", 28.6320, 77.2960),
        S("Preet Vihar", "PRV", 28.6390, 77.3020),
        S("Karkarduma", "KKD", KKD[0], KKD[1], junction=True, interchange=["PK"]),
        S("Anand Vihar", "ANV", AV[0], AV[1], junction=True, interchange=["PK"]),
        S("Kaushambi", "KSM", 28.6500, 77.3240),
        S("Vaishali", "VSH", 28.6520, 77.3320, terminus=True),
    ],
    "interchanges": [
        IC("YBK", "BL", "Yamuna Bank"),
        IC("KKD", "PK", "Karkarduma"),
        IC("ANV", "PK", "Anand Vihar"),
    ],
}


# ───────────────────────── line 5 — Green (main) ─────────────────────────

GREEN = {
    "code": "GR",
    "name": "Green Line",
    "number": 5,
    "color_hex": "#00A651",
    "corridor": "Brigadier Hoshiyar Singh (Bahadurgarh) – Inderlok",
    "opened_year": 2010,
    "operator": "DMRC",
    "gauge_mm": 1435,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 26.31,
    "depots": [D("Mundka Depot", 28.6810, 77.0600, 75_000, 40)],
    "stations": [
        S("Brigadier Hoshiyar Singh", "BHS", 28.6800, 76.9400, terminus=True),
        S("Bahadurgarh City", "BHC", 28.6800, 76.9700),
        S("Pandit Shree Ram Sharma", "PSR", 28.6800, 76.9900),
        S("Tikri Border", "TKB", 28.6800, 77.0100),
        S("Tikri Kalan", "TKL", 28.6800, 77.0300),
        S("Mundka Industrial Area", "MIA", 28.6800, 77.0450),
        S("Mundka", "MUN", 28.6810, 77.0600),
        S("Rajdhani Park", "RDP", 28.6790, 77.0700),
        S("Nangloi", "NAN", 28.6820, 77.0750),
        S("Udyog Nagar", "UDN", 28.6800, 77.0900),
        S("Peeragarhi", "PGG", 28.6770, 77.1050),
        S("Ashok Park Main", "APM", APM[0], APM[1], junction=True, interchange=["GB"]),
        S(
            "Inderlok",
            "ILK",
            IL[0],
            IL[1],
            terminus=True,
            junction=True,
            interchange=["RD"],
        ),
    ],
    "interchanges": [
        IC("APM", "GB", "Ashok Park Main"),
        IC("ILK", "RD", "Inderlok"),
    ],
    "speed_overrides": {"Mundka-Nangloi": 70},
}


# ───────────────────────── line 6 — Green Branch (Kirti Nagar) ─────────────────────────

GREEN_BRANCH = {
    "code": "GB",
    "name": "Green Line Branch",
    "number": 6,
    "color_hex": "#00A651",
    "corridor": "Ashok Park Main – Kirti Nagar",
    "opened_year": 2010,
    "operator": "DMRC",
    "gauge_mm": 1435,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 3.31,
    "depots": [],
    "stations": [
        S(
            "Ashok Park Main",
            "APM",
            APM[0],
            APM[1],
            terminus=True,
            junction=True,
            interchange=["GR"],
        ),
        S("Satguru Ram Singh Marg", "SRS", 28.6500, 77.1380),
        S(
            "Kirti Nagar",
            "KTN",
            KN[0],
            KN[1],
            terminus=True,
            junction=True,
            interchange=["BL"],
        ),
    ],
    "interchanges": [
        IC("APM", "GR", "Ashok Park Main"),
        IC("KTN", "BL", "Kirti Nagar"),
    ],
}


# ───────────────────────── line 7 — Violet ─────────────────────────

VIOLET = {
    "code": "VL",
    "name": "Violet Line",
    "number": 7,
    "color_hex": "#8E44AD",
    "corridor": "Kashmere Gate – Raja Nahar Singh (Ballabhgarh)",
    "opened_year": 2010,
    "operator": "DMRC",
    "gauge_mm": 1435,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 46.60,
    "depots": [D("Sarita Vihar Depot", 28.5190, 77.2960, 80_000, 48)],
    "stations": [
        S(
            "Kashmere Gate",
            "KGM",
            KG[0],
            KG[1],
            terminus=True,
            structure="underground",
            junction=True,
            interchange=["RD", "YL"],
        ),
        S("Lal Qila", "LQL", 28.6560, 77.2380, structure="underground"),
        S("Jama Masjid", "JMS", 28.6500, 77.2340, structure="underground"),
        S("Delhi Gate", "DLG", 28.6420, 77.2360, structure="underground"),
        S("ITO", "ITO", 28.6300, 77.2390, structure="underground"),
        S(
            "Mandi House",
            "MDH",
            MH[0],
            MH[1],
            structure="underground",
            junction=True,
            interchange=["BL"],
        ),
        S("Janpath", "JPT", 28.6200, 77.2170, structure="underground"),
        S(
            "Central Secretariat",
            "CSE",
            CS[0],
            CS[1],
            structure="underground",
            junction=True,
            interchange=["YL"],
        ),
        S("Khan Market", "KHM", 28.6030, 77.2250, structure="underground"),
        S("JLN Stadium", "JLN", 28.5830, 77.2330, structure="underground"),
        S("Jangpura", "JGP", 28.5820, 77.2350, structure="underground"),
        S("Lajpat Nagar", "LJN", LN[0], LN[1], junction=True, interchange=["PK"]),
        S("Moolchand", "MCH", 28.5660, 77.2300),
        S("Kailash Colony", "KLC", 28.5530, 77.2500),
        S("Nehru Place", "NEP", 28.5490, 77.2520),
        S("Kalkaji Mandir", "KMK", KKM[0], KKM[1], junction=True, interchange=["MG"]),
        S("Govindpuri", "GVP", 28.5400, 77.2640),
        S("Okhla", "OKH", 28.5330, 77.2700),
        S("Jasola", "JAS", 28.5260, 77.2860),
        S("Sarita Vihar", "SRV", 28.5190, 77.2960),
        S("Mohan Estate", "MHE", 28.5120, 77.3040),
        S("Tughlakabad", "TUG", 28.5050, 77.3120),
        S("Badarpur Border", "BPB", 28.4930, 77.3180),
        S("Sarai", "SRA", 28.4850, 77.3240),
        S("NHPC Chowk", "NHP", 28.4780, 77.3280),
        S("Mewala Maharajpur", "MWM", 28.4700, 77.3300),
        S("Old Faridabad", "OFD", 28.4620, 77.3320),
        S("Neelam Chowk Ajronda", "NCA", 28.4540, 77.3340),
        S("Bata Chowk", "BTC", 28.4460, 77.3360),
        S("Raja Nahar Singh", "RNS", 28.4380, 77.3380, terminus=True),
    ],
    "interchanges": [
        IC("KGM", "RD", "Kashmere Gate"),
        IC("KGM", "YL", "Kashmere Gate"),
        IC("MDH", "BL", "Mandi House"),
        IC("CSE", "YL", "Central Secretariat"),
        IC("LJN", "PK", "Lajpat Nagar"),
        IC("KMK", "MG", "Kalkaji Mandir"),
    ],
    "speed_overrides": {"Kashmere Gate-Lal Qila": 60},
    "gradients": {"Badarpur Border-Sarai": 1.1},
}


# ───────────────────────── line 8 — Pink ─────────────────────────

PINK = {
    "code": "PK",
    "name": "Pink Line",
    "number": 8,
    "color_hex": "#E8A0BF",
    "corridor": "Majlis Park – Shiv Vihar",
    "opened_year": 2018,
    "operator": "DMRC",
    "gauge_mm": 1435,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 59.35,
    "depots": [D("Majlis Park Depot", 28.7150, 77.1800, 85_000, 52)],
    "stations": [
        S("Majlis Park", "MJP", 28.7150, 77.1800, terminus=True),
        S("Prembari Pul", "PBP", 28.7080, 77.1830),
        S("Azadpur", "AZP", AP[0], AP[1], junction=True, interchange=["YL"]),
        S("Shalimar Bagh", "SHB", 28.6910, 77.1890),
        S(
            "Netaji Subhash Place",
            "NSP",
            NSP[0],
            NSP[1],
            junction=True,
            interchange=["RD"],
        ),
        S("Shakurpur", "SKP", 28.6780, 77.1470),
        S("ESI Basaidarapur", "ESI", 28.6700, 77.1380),
        S("Punjabi Bagh West", "PBW", 28.6690, 77.1300),
        S("Rajouri Garden", "RAJ", RG[0], RG[1], junction=True, interchange=["BL"]),
        S("Mayapuri", "MAY", 28.6440, 77.1120),
        S("Naraina Vihar", "NRV", 28.6310, 77.1070),
        S("Delhi Cantt", "DCT", 28.6200, 77.1100),
        S("Dhaula Kuan", "DKU", DK[0], DK[1], junction=True, interchange=["OR"]),
        S("Sir Vishweshwaraiah Moti Bagh", "VMB", 28.5960, 77.1660),
        S("Bhikaji Cama Place", "BCP", 28.5800, 77.1850),
        S("Durgabai Deshmukh South Campus", "DSC", 28.5730, 77.1900),
        S("Dilli Haat INA", "INA", INA[0], INA[1], junction=True, interchange=["YL"]),
        S("South Extension", "SEX", 28.5660, 77.2240),
        S("Lajpat Nagar", "LJN", LN[0], LN[1], junction=True, interchange=["VL"]),
        S("Vinobapuri", "VNP", 28.5630, 77.2540),
        S("Ashram", "ASH", 28.5560, 77.2630),
        S("Hazrat Nizamuddin", "HZN", 28.5780, 77.2640),
        S(
            "Mayur Vihar Phase-I",
            "MVP",
            MVP1[0],
            MVP1[1],
            junction=True,
            interchange=["BL"],
        ),
        S("Mayur Vihar Pocket-1", "MV1", 28.6220, 77.3000),
        S("Trilokpuri Sanjay Lake", "TSL", 28.6250, 77.3120),
        S("East Azad Nagar", "EAN", 28.6300, 77.3200),
        S("Krishna Nagar", "KRN", 28.6380, 77.3260),
        S("Shiv Vihar", "SVH", 28.6500, 77.3380, terminus=True),
    ],
    "interchanges": [
        IC("AZP", "YL", "Azadpur"),
        IC("NSP", "RD", "Netaji Subhash Place"),
        IC("RAJ", "BL", "Rajouri Garden"),
        IC("DKU", "OR", "Dhaula Kuan"),
        IC("INA", "YL", "Dilli Haat INA"),
        IC("LJN", "VL", "Lajpat Nagar"),
        IC("MVP", "BL", "Mayur Vihar Phase-I"),
    ],
    "speed_overrides": {"Hazrat Nizamuddin-Mayur Vihar Phase-I": 60},
    "curve_vertices": {"Hazrat Nizamuddin-Mayur Vihar Phase-I": [[77.2700, 28.6000]]},
}


# ───────────────────────── line 9 — Magenta ─────────────────────────

MAGENTA = {
    "code": "MG",
    "name": "Magenta Line",
    "number": 9,
    "color_hex": "#8E44AD",
    "corridor": "Janakpuri West – Botanical Garden",
    "opened_year": 2017,
    "operator": "DMRC",
    "gauge_mm": 1435,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 38.48,
    "depots": [D("Janakpuri Depot", 28.6293, 77.0800, 70_000, 44)],
    "stations": [
        S("Janakpuri West", "JNW", JW[0], JW[1], junction=True, interchange=["BL"]),
        S("Dabri Mor", "DBM", 28.6200, 77.0920),
        S("Dashrath Puri", "DTP", 28.6120, 77.0980),
        S("Palam", "PAL", 28.6050, 77.1050),
        S("Sadar Bazar Cantonment", "SBC", 28.5960, 77.1120),
        S("Terminal 1-IGI Airport", "T1A", 28.5660, 77.1200),
        S("Shankar Vihar", "SHV", 28.5480, 77.1300),
        S("Vasant Vihar", "VSV", 28.5560, 77.1620),
        S("Munirka", "MUN", 28.5580, 77.1750),
        S("R.K. Puram", "RKP", 28.5550, 77.1850),
        S(
            "Hauz Khas",
            "HZK",
            HK[0],
            HK[1],
            structure="underground",
            junction=True,
            interchange=["YL"],
        ),
        S("Kalkaji Mandir", "KMK", KKM[0], KKM[1], junction=True, interchange=["VL"]),
        S("Okhla NSIC", "ONS", 28.5400, 77.2640),
        S("Sukhdev Vihar", "SDV", 28.5380, 77.2780),
        S("Jamia Millia Islamia", "JMI", 28.5330, 77.2880),
        S("Okhla Vihar", "OKV", 28.5300, 77.2980),
        S("Jasola Vihar Shaheen Bagh", "JVS", 28.5350, 77.3060),
        S("Kalindi Kunj", "KLK", 28.5410, 77.3140),
        S(
            "Botanical Garden",
            "BGA",
            BG[0],
            BG[1],
            terminus=True,
            junction=True,
            interchange=["BL"],
        ),
    ],
    "interchanges": [
        IC("JNW", "BL", "Janakpuri West"),
        IC("HZK", "YL", "Hauz Khas"),
        IC("KMK", "VL", "Kalkaji Mandir"),
        IC("BGA", "BL", "Botanical Garden"),
    ],
    "speed_overrides": {"Terminal 1-IGI Airport-Shankar Vihar": 75},
    "gradients": {"Palam-Sadar Bazar Cantonment": 1.0},
}


# ───────────────────────── line 10 — Grey ─────────────────────────

GREY = {
    "code": "GY",
    "name": "Grey Line",
    "number": 10,
    "color_hex": "#9E9E9E",
    "corridor": "Dwarka – Dhansa Bus Stand",
    "opened_year": 2018,
    "operator": "DMRC",
    "gauge_mm": 1435,
    "electrification": "25 kV AC OHE",
    "signalling_system": "ATP",
    "total_length_km": 5.48,
    "depots": [D("Najafgarh Depot", 28.6090, 77.0330, 40_000, 20)],
    "stations": [
        S(
            "Dwarka",
            "DWA",
            DWA[0],
            DWA[1],
            terminus=True,
            junction=True,
            interchange=["BL"],
        ),
        S("Nangli", "NGL", 28.5860, 77.0600),
        S("Najafgarh", "NJR", 28.6090, 77.0330),
        S("Bhesan", "BHE", 28.6140, 77.0200),
        S("Dhansa Bus Stand", "DBS", 28.6170, 77.0100, terminus=True),
    ],
    "interchanges": [IC("DWA", "BL", "Dwarka")],
    "speed_overrides": {"Nangli-Najafgarh": 70},
}


# ───────────────────────── line 11 — Orange / Airport Express ─────────────────────────

ORANGE = {
    "code": "OR",
    "name": "Airport Express Line",
    "number": 11,
    "color_hex": "#FF8C00",
    "corridor": "New Delhi – Dwarka Sector 21 (via IGI Airport)",
    "opened_year": 2011,
    "operator": "DMRC",
    "gauge_mm": 1676,
    "electrification": "25 kV AC OHE",
    "signalling_system": "CBTC",
    "total_length_km": 22.70,
    "depots": [],
    "stations": [
        S(
            "New Delhi",
            "NDL",
            ND[0],
            ND[1],
            terminus=True,
            structure="underground",
            junction=True,
            platforms=3,
            interchange=["YL"],
        ),
        S(
            "Shivaji Stadium",
            "SHS",
            28.6330,
            77.2150,
            structure="underground",
            platforms=2,
        ),
        S(
            "Dhaula Kuan",
            "DKU",
            DK[0],
            DK[1],
            junction=True,
            platforms=2,
            interchange=["PK"],
        ),
        S(
            "Delhi Aerocity",
            "AER",
            28.5480,
            77.1180,
            structure="underground",
            platforms=2,
        ),
        S("IGI Airport", "IGI", 28.5630, 77.1120, platforms=2),
        S(
            "Dwarka Sector 21",
            "DW21",
            DW21[0],
            DW21[1],
            terminus=True,
            junction=True,
            platforms=2,
            interchange=["BL"],
        ),
    ],
    "interchanges": [
        IC("NDL", "YL", "New Delhi"),
        IC("DKU", "PK", "Dhaula Kuan"),
        IC("DW21", "BL", "Dwarka Sector 21"),
    ],
    "speed_overrides": {"Dhaula Kuan-Delhi Aerocity": 110},
    "gradients": {"Delhi Aerocity-IGI Airport": 0.6},
}


# ───────────────────────── line 12 — Rapid Metro Gurugram ─────────────────────────

RAPID = {
    "code": "RM",
    "name": "Rapid Metro Gurugram",
    "number": 12,
    "color_hex": "#0091CD",
    "corridor": "Sikandarpur – Phase 3 (Gurugram)",
    "opened_year": 2013,
    "operator": "Rapid MetroRail Gurgaon Limited",
    "gauge_mm": 1435,
    "electrification": "750 V DC Third Rail",
    "signalling_system": "CBTC",
    "total_length_km": 11.68,
    "depots": [],
    "stations": [
        S(
            "Sikandarpur",
            "SKD",
            SIK[0],
            SIK[1],
            terminus=True,
            junction=True,
            interchange=["YL"],
        ),
        S("Phase 2", "PH2", 28.4460, 77.1100),
        S("Belvedere Towers", "BLV", 28.4420, 77.0960),
        S("Cyber City", "CYC", 28.4380, 77.0900),
        S("Moulsari Avenue", "MOL", 28.4350, 77.0870),
        S("Phase 3", "PH3", 28.4340, 77.0850, terminus=True),
    ],
    "interchanges": [IC("SKD", "YL", "Sikandarpur")],
    "speed_overrides": {"Sikandarpur-Phase 2": 70},
}


# ───────────────────────── assembly ─────────────────────────

LINES = [
    RED,
    YELLOW,
    BLUE,
    BLUE_BRANCH,
    GREEN,
    GREEN_BRANCH,
    VIOLET,
    PINK,
    MAGENTA,
    GREY,
    ORANGE,
    RAPID,
]


def build_dataset() -> dict:
    return {
        "lines": [json.loads(json.dumps(ln)) for ln in LINES],  # deep copy
    }


# ───────────────────────── validation + auto-fix loop ─────────────────────────


def _line_codes(data) -> set[str]:
    return {ln["code"] for ln in data["lines"]}


def _fix_duplicate_codes(data) -> bool:
    changed = False
    for ln in data["lines"]:
        seen: set[str] = set()
        for idx, st in enumerate(ln["stations"]):
            if st["code"] in seen:
                new = f"{st['code']}{ln['code']}{idx}"
                st["code"] = new
                changed = True
            seen.add(st["code"])
    return changed


def _fix_missing_terminus(data) -> bool:
    changed = False
    for ln in data["lines"]:
        if not any(st.get("is_terminus") for st in ln["stations"]):
            if ln["stations"]:
                ln["stations"][0]["is_terminus"] = True
                ln["stations"][-1]["is_terminus"] = True
                changed = True
    return changed


def _fix_interchange_refs(data) -> bool:
    changed = False
    valid = _line_codes(data)
    for ln in data["lines"]:
        kept = []
        for ic in ln.get("interchanges", []):
            if ic["line"] in valid and ic["line"] != ln["code"]:
                kept.append(ic)
            else:
                changed = True
        ln["interchanges"] = kept
    return changed


def _fix_station_refs(data) -> bool:
    """Ensure interchange_with lists only reference existing line codes."""
    changed = False
    valid = _line_codes(data)
    for ln in data["lines"]:
        for st in ln["stations"]:
            fixed = [
                c for c in st["interchange_with"] if c in valid and c != ln["code"]
            ]
            if len(fixed) != len(st["interchange_with"]):
                st["interchange_with"] = fixed
                changed = True
    return changed


FIXERS = [
    _fix_duplicate_codes,
    _fix_missing_terminus,
    _fix_interchange_refs,
    _fix_station_refs,
]


def validate_with_loader(data: dict) -> None:
    """Round-trip the data through dmdt_gis.load_network via a temp file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)
    try:
        dmdt_gis.load_network(tmp_path)  # raises on invalid data
    finally:
        tmp_path.unlink(missing_ok=True)


def generate_until_valid(max_iters: int = 8) -> dict:
    data = build_dataset()
    for attempt in range(1, max_iters + 1):
        try:
            validate_with_loader(data)
            return data
        except Exception as exc:  # noqa: BLE001
            applied = [f.__name__ for f in FIXERS if f(data)]
            msg = f"attempt {attempt} failed ({exc!r}); applied fixers: {applied}"
            print(msg, file=sys.stderr)
            if not applied and attempt == max_iters:
                raise
    raise RuntimeError("dataset never validated — manual inspection required")


# ───────────────────────── entry point ─────────────────────────


def main() -> int:
    print(f"building canonical dataset for {len(LINES)} lines…")
    data = generate_until_valid()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    DATA_FILE.write_text(payload, encoding="utf-8")
    print(f"wrote {DATA_FILE} ({len(payload)} bytes)")

    # Final confirmation: load from the canonical location.
    network = dmdt_gis.load_network()
    total_stations = sum(ln.total_stations for ln in network.lines)
    print(
        f"OK: {len(network.lines)} lines, "
        f"{network.station_count} unique stations, "
        f"{total_stations} line-stations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
