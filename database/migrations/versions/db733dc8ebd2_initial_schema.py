"""initial schema

Revision ID: db733dc8ebd2
Revises:
Create Date: 2026-07-07 14:55:27.190092
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


revision: str = 'db733dc8ebd2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('lines',
        sa.Column('code', sa.String(length=5), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('color_hex', sa.String(length=7), nullable=False),
        sa.Column('corridor', sa.String(length=300), nullable=False),
        sa.Column('opened_year', sa.Integer(), nullable=False),
        sa.Column('operator', sa.String(length=100), nullable=False),
        sa.Column('gauge_mm', sa.Integer(), nullable=False),
        sa.Column('electrification', sa.String(length=100), nullable=False),
        sa.Column('signalling_system', sa.String(length=50), nullable=False),
        sa.Column('total_length_km', sa.Float(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('number'),
    )
    op.create_index(op.f('ix_lines_code'), 'lines', ['code'], unique=True)

    op.create_table('train_classes',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('max_speed_kmh', sa.Float(), nullable=False),
        sa.Column('acceleration_ms2', sa.Float(), nullable=False),
        sa.Column('deceleration_ms2', sa.Float(), nullable=False),
        sa.Column('length_m', sa.Float(), nullable=False),
        sa.Column('capacity_seated', sa.Integer(), nullable=False),
        sa.Column('capacity_standing', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table('depots',
        sa.Column('line_code', sa.String(length=5), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('area_m2', sa.Float(), nullable=False),
        sa.Column('capacity_stabling', sa.Integer(), nullable=False),
        sa.Column('coordinate_confidence', sa.String(length=10), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['line_code'], ['lines.code'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_depots_line_code'), 'depots', ['line_code'], unique=False)

    op.create_table('stations',
        sa.Column('line_code', sa.String(length=5), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2), nullable=False),
        sa.Column('structure', sa.String(length=20), nullable=False),
        sa.Column('platforms', sa.Integer(), nullable=False),
        sa.Column('opened_year', sa.Integer(), nullable=False),
        sa.Column('is_terminus', sa.Boolean(), nullable=False),
        sa.Column('has_junction', sa.Boolean(), nullable=False),
        sa.Column('coordinate_confidence', sa.String(length=10), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['line_code'], ['lines.code'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_stations_code'), 'stations', ['code'], unique=False)
    op.create_index(op.f('ix_stations_line_code'), 'stations', ['line_code'], unique=False)

    op.create_table('crossovers',
        sa.Column('line_code', sa.String(length=5), nullable=False),
        sa.Column('station_id', sa.UUID(), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='LINESTRING', srid=4326, dimension=2), nullable=False),
        sa.Column('heading_deg', sa.Float(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['line_code'], ['lines.code'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_crossovers_line_code'), 'crossovers', ['line_code'], unique=False)
    op.create_index(op.f('ix_crossovers_station_id'), 'crossovers', ['station_id'], unique=False)

    op.create_table('junctions',
        sa.Column('station_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2), nullable=False),
        sa.Column('is_interchange', sa.Boolean(), nullable=False),
        sa.Column('is_turnout', sa.Boolean(), nullable=False),
        sa.Column('lines', sa.String(length=200), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_junctions_station_id'), 'junctions', ['station_id'], unique=False)

    op.create_table('platforms',
        sa.Column('station_id', sa.UUID(), nullable=False),
        sa.Column('platform_number', sa.Integer(), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, dimension=2), nullable=False),
        sa.Column('heading_deg', sa.Float(), nullable=False),
        sa.Column('length_m', sa.Float(), nullable=False),
        sa.Column('width_m', sa.Float(), nullable=False),
        sa.Column('is_edge_platform', sa.Boolean(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_platforms_station_id'), 'platforms', ['station_id'], unique=False)

    op.create_table('sidings',
        sa.Column('depot_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='LINESTRING', srid=4326, dimension=2), nullable=False),
        sa.Column('length_m', sa.Float(), nullable=False),
        sa.Column('capacity_trains', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['depot_id'], ['depots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sidings_depot_id'), 'sidings', ['depot_id'], unique=False)

    op.create_table('track_segments',
        sa.Column('line_code', sa.String(length=5), nullable=False),
        sa.Column('from_station_id', sa.UUID(), nullable=False),
        sa.Column('to_station_id', sa.UUID(), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('segment_index', sa.Integer(), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='LINESTRING', srid=4326, dimension=2), nullable=False),
        sa.Column('length_m', sa.Float(), nullable=False),
        sa.Column('heading_in_deg', sa.Float(), nullable=False),
        sa.Column('heading_out_deg', sa.Float(), nullable=False),
        sa.Column('max_curve_radius_m', sa.Float(), nullable=True),
        sa.Column('speed_limit_kmh', sa.Float(), nullable=False),
        sa.Column('gradient_pct', sa.Float(), nullable=True),
        sa.Column('is_curve', sa.Boolean(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['from_station_id'], ['stations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['line_code'], ['lines.code'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_station_id'], ['stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_track_segments_from_station_id'), 'track_segments', ['from_station_id'], unique=False)
    op.create_index(op.f('ix_track_segments_line_code'), 'track_segments', ['line_code'], unique=False)
    op.create_index(op.f('ix_track_segments_to_station_id'), 'track_segments', ['to_station_id'], unique=False)

    op.create_table('switches',
        sa.Column('line_code', sa.String(length=5), nullable=False),
        sa.Column('junction_id', sa.UUID(), nullable=False),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2), nullable=False),
        sa.Column('switch_label', sa.String(length=20), nullable=False),
        sa.Column('heading_deg', sa.Float(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['junction_id'], ['junctions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['line_code'], ['lines.code'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_switches_junction_id'), 'switches', ['junction_id'], unique=False)
    op.create_index(op.f('ix_switches_line_code'), 'switches', ['line_code'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_switches_line_code'), table_name='switches')
    op.drop_index(op.f('ix_switches_junction_id'), table_name='switches')
    op.drop_table('switches')
    op.drop_index(op.f('ix_track_segments_to_station_id'), table_name='track_segments')
    op.drop_index(op.f('ix_track_segments_line_code'), table_name='track_segments')
    op.drop_index(op.f('ix_track_segments_from_station_id'), table_name='track_segments')
    op.drop_table('track_segments')
    op.drop_index(op.f('ix_sidings_depot_id'), table_name='sidings')
    op.drop_table('sidings')
    op.drop_index(op.f('ix_platforms_station_id'), table_name='platforms')
    op.drop_table('platforms')
    op.drop_index(op.f('ix_junctions_station_id'), table_name='junctions')
    op.drop_table('junctions')
    op.drop_index(op.f('ix_crossovers_station_id'), table_name='crossovers')
    op.drop_index(op.f('ix_crossovers_line_code'), table_name='crossovers')
    op.drop_table('crossovers')
    op.drop_index(op.f('ix_stations_line_code'), table_name='stations')
    op.drop_index(op.f('ix_stations_code'), table_name='stations')
    op.drop_table('stations')
    op.drop_index(op.f('ix_depots_line_code'), table_name='depots')
    op.drop_table('depots')
    op.drop_table('train_classes')
    op.drop_index(op.f('ix_lines_code'), table_name='lines')
    op.drop_table('lines')
