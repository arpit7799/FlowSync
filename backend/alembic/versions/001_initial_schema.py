"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-14 11:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'intersections',
        sa.Column('id', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('location_x', sa.Float(), nullable=True),
        sa.Column('location_y', sa.Float(), nullable=True),
        sa.Column('num_lanes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('current_phase', sa.Integer(), nullable=True),
        sa.Column('current_mode', sa.String(length=20), nullable=True),
        sa.Column('current_state', sa.String(length=30), nullable=True),
        sa.Column('vehicle_count', sa.Integer(), nullable=True),
        sa.Column('queue_length', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'device_statuses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('device_id', sa.String(length=50), nullable=False),
        sa.Column('intersection_id', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('uptime_seconds', sa.Float(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )

    op.create_table(
        'simulation_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scenario', sa.String(length=30), nullable=False),
        sa.Column('controller_type', sa.String(length=30), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('vehicles_inserted', sa.Integer(), nullable=True),
        sa.Column('vehicles_arrived', sa.Integer(), nullable=True),
        sa.Column('peak_queue', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'sensor_readings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('intersection_id', sa.String(length=10), nullable=False),
        sa.Column('device_id', sa.String(length=50), nullable=False),
        sa.Column('distance_cm', sa.Float(), nullable=False),
        sa.Column('vehicle_detected', sa.Boolean(), nullable=True),
        sa.Column('vehicle_count', sa.Integer(), nullable=True),
        sa.Column('queue_length', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['intersection_id'], ['intersections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sensor_readings_intersection_id'), 'sensor_readings', ['intersection_id'], unique=False)
    op.create_index(op.f('ix_sensor_readings_timestamp'), 'sensor_readings', ['timestamp'], unique=False)

    op.create_table(
        'signal_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('intersection_id', sa.String(length=10), nullable=False),
        sa.Column('mode', sa.String(length=30), nullable=False),
        sa.Column('active_phase', sa.Integer(), nullable=True),
        sa.Column('state', sa.String(length=30), nullable=False),
        sa.Column('is_emergency', sa.Boolean(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['intersection_id'], ['intersections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signal_states_intersection_id'), 'signal_states', ['intersection_id'], unique=False)
    op.create_index(op.f('ix_signal_states_timestamp'), 'signal_states', ['timestamp'], unique=False)

    op.create_table(
        'emergency_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('vehicle_id', sa.String(length=50), nullable=False),
        sa.Column('vehicle_type', sa.String(length=30), nullable=True),
        sa.Column('junction_id', sa.String(length=10), nullable=False),
        sa.Column('incoming_edge', sa.String(length=30), nullable=True),
        sa.Column('requested_phase', sa.Integer(), nullable=True),
        sa.Column('request_time', sa.Float(), nullable=False),
        sa.Column('granted_time', sa.Float(), nullable=True),
        sa.Column('cleared_time', sa.Float(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['junction_id'], ['intersections.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    op.create_index(op.f('ix_emergency_events_junction_id'), 'emergency_events', ['junction_id'], unique=False)
    op.create_index(op.f('ix_emergency_events_status'), 'emergency_events', ['status'], unique=False)

    op.create_table(
        'benchmark_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=True),
        sa.Column('scenario', sa.String(length=30), nullable=False),
        sa.Column('mode', sa.String(length=30), nullable=False),
        sa.Column('total_vehicles', sa.Integer(), nullable=True),
        sa.Column('avg_waiting_time', sa.Float(), nullable=True),
        sa.Column('avg_time_loss', sa.Float(), nullable=True),
        sa.Column('avg_duration', sa.Float(), nullable=True),
        sa.Column('peak_queue', sa.Integer(), nullable=True),
        sa.Column('avg_queue', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['simulation_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('benchmark_metrics')
    op.drop_table('emergency_events')
    op.drop_table('signal_states')
    op.drop_table('sensor_readings')
    op.drop_table('simulation_runs')
    op.drop_table('device_statuses')
    op.drop_table('intersections')
