from typing import List

from sqlalchemy import Column, Float, ForeignKeyConstraint, Index, String, TIMESTAMP
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class Boroughs(Base):
    __tablename__ = 'boroughs'

    id = mapped_column(INTEGER(11), primary_key=True)
    borough_name = mapped_column(String(100), nullable=False)

    zones: Mapped[List['Zones']] = relationship('Zones', uselist=True, back_populates='borough')


class PaymentTypes(Base):
    __tablename__ = 'payment_types'

    id = mapped_column(INTEGER(11), primary_key=True)
    payment_type = mapped_column(String(100), nullable=False)

    yellow_trips: Mapped[List['YellowTrips']] = relationship('YellowTrips', uselist=True, back_populates='payment_types')


class RateCodes(Base):
    __tablename__ = 'rate_codes'

    RatecodeID = mapped_column(INTEGER(11), primary_key=True)
    code = mapped_column(String(100), nullable=False)

    yellow_trips: Mapped[List['YellowTrips']] = relationship('YellowTrips', uselist=True, back_populates='rate_codes')


class ServiceZones(Base):
    __tablename__ = 'service_zones'

    id = mapped_column(INTEGER(11), primary_key=True)
    service_zone_name = mapped_column(String(100), nullable=False)

    zones: Mapped[List['Zones']] = relationship('Zones', uselist=True, back_populates='service_zone')


class Vendors(Base):
    __tablename__ = 'vendors'

    VendorID = mapped_column(INTEGER(11), primary_key=True)
    vendor_name = mapped_column(String(100), nullable=False)

    yellow_trips: Mapped[List['YellowTrips']] = relationship('YellowTrips', uselist=True, back_populates='vendors')


class Zones(Base):
    __tablename__ = 'zones'
    __table_args__ = (
        ForeignKeyConstraint(['borough_id'], ['boroughs.id'], name='fk_zones_boroughs'),
        ForeignKeyConstraint(['service_zone_id'], ['service_zones.id'], name='fk_zones_service_zone1'),
        Index('fk_zones_boroughs_idx', 'borough_id'),
        Index('fk_zones_service_zone1_idx', 'service_zone_id')
    )

    LocationID = mapped_column(INTEGER(11), primary_key=True)
    zone_name = mapped_column(String(100), nullable=False)
    borough_id = mapped_column(INTEGER(11), nullable=False)
    service_zone_id = mapped_column(INTEGER(11), nullable=False)

    borough: Mapped['Boroughs'] = relationship('Boroughs', back_populates='zones')
    service_zone: Mapped['ServiceZones'] = relationship('ServiceZones', back_populates='zones')
    yellow_trips: Mapped[List['YellowTrips']] = relationship('YellowTrips', uselist=True, foreign_keys='[YellowTrips.DOLocationID]', back_populates='zones')
    yellow_trips_: Mapped[List['YellowTrips']] = relationship('YellowTrips', uselist=True, foreign_keys='[YellowTrips.PULocationID]', back_populates='zones_')


class YellowTrips(Base):
    __tablename__ = 'yellow_trips'
    __table_args__ = (
        ForeignKeyConstraint(['DOLocationID'], ['zones.LocationID'], name='fk_yellow_trips_zones2'),
        ForeignKeyConstraint(['PULocationID'], ['zones.LocationID'], name='fk_yellow_trips_zones1'),
        ForeignKeyConstraint(['RatecodeID'], ['rate_codes.RatecodeID'], name='fk_yellow_trips_rate_codes1'),
        ForeignKeyConstraint(['VendorID'], ['vendors.VendorID'], name='fk_yellow_trips_vendors1'),
        ForeignKeyConstraint(['payment_type'], ['payment_types.id'], name='fk_yellow_trips_payment_types1'),
        Index('fk_yellow_trips_payment_types1_idx', 'payment_type'),
        Index('fk_yellow_trips_rate_codes1_idx', 'RatecodeID'),
        Index('fk_yellow_trips_vendors1_idx', 'VendorID'),
        Index('fk_yellow_trips_zones1_idx', 'PULocationID'),
        Index('fk_yellow_trips_zones2_idx', 'DOLocationID')
    )

    id = mapped_column(INTEGER(11), primary_key=True)
    VendorID = mapped_column(INTEGER(11), nullable=False)
    passenger_count = mapped_column(INTEGER(11), nullable=False)
    trip_distance = mapped_column(Float, nullable=False)
    RatecodeID = mapped_column(INTEGER(11), nullable=False)
    store_and_fwd_flag = mapped_column(String(45), nullable=False)
    PULocationID = mapped_column(INTEGER(11), nullable=False)
    DOLocationID = mapped_column(INTEGER(11), nullable=False)
    payment_type = mapped_column(INTEGER(11), nullable=False)
    fare_amount = mapped_column(Float, nullable=False)
    extra = mapped_column(Float, nullable=False)
    mta_tax = mapped_column(Float, nullable=False)
    tip_amount = mapped_column(Float, nullable=False)
    tolls_amount = mapped_column(Float, nullable=False)
    improvement_surcharge = mapped_column(Float, nullable=False)
    total_amount = mapped_column(Float, nullable=False)
    congestion_surcharge = mapped_column(Float, nullable=False)
    Airport_fee = mapped_column(Float, nullable=False)
    tpep_pickup_datetime = mapped_column(TIMESTAMP)
    tpep_dropoff_datetime = mapped_column(TIMESTAMP)
    pu_year = mapped_column(INTEGER(11))
    pu_month = mapped_column(INTEGER(11))
    pu_day = mapped_column(INTEGER(11))
    pu_hour = mapped_column(INTEGER(11))
    pu_min = mapped_column(INTEGER(11))
    pu_sec = mapped_column(INTEGER(11))
    do_year = mapped_column(INTEGER(11))
    do_month = mapped_column(INTEGER(11))
    do_day = mapped_column(INTEGER(11))
    do_hour = mapped_column(INTEGER(11))
    do_min = mapped_column(INTEGER(11))
    do_sec = mapped_column(INTEGER(11))

    zones: Mapped['Zones'] = relationship('Zones', foreign_keys=[DOLocationID], back_populates='yellow_trips')
    zones_: Mapped['Zones'] = relationship('Zones', foreign_keys=[PULocationID], back_populates='yellow_trips_')
    rate_codes: Mapped['RateCodes'] = relationship('RateCodes', back_populates='yellow_trips')
    vendors: Mapped['Vendors'] = relationship('Vendors', back_populates='yellow_trips')
    payment_types: Mapped['PaymentTypes'] = relationship('PaymentTypes', back_populates='yellow_trips')
