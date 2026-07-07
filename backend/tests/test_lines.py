from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Requires PostgreSQL with PostGIS")
async def test_list_lines():
    pass


@pytest.mark.skip(reason="Requires PostgreSQL with PostGIS")
async def test_get_line_not_found():
    pass
