import os
import subprocess
import traceback
from datetime import datetime

import pandas as pd

import gdown
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, drop_database, create_database

import models

env = os.environ.copy()
FOLDER_ID = ''

# VAIHDA TÄHÄN OMA POSTGRES-TIETOKANNAN SALASANA

DST_DB = ''
DST_DB_PORT = '5432'
DST_USER = 'postgres'
DST_PWD = ''

env["PGPASSWORD"] = DST_PWD


def _create_db(user, pwd, db, db_port):
    dst_conn_str = f"postgresql+psycopg2://{user}:{pwd}@localhost:{db_port}/{db}"
    if database_exists(dst_conn_str):
        drop_database(dst_conn_str)
    create_database(dst_conn_str)

    engine = create_engine(dst_conn_str)
    if hasattr(models, 'Base'):
        _metadata = models.Base.metadata
    elif hasattr(models, 'metadata'):
        _metadata = models.metadata
    else:
        raise Exception('metadata missing')

    _metadata.create_all(engine)


def _export_data_to_db(user, target_db, dump_dir, jobs=4):
    start = datetime.now()
    print("## yellow_trips-taulun skeema ##")
    subprocess.run(["pg_restore", "-U", user, "-d", target_db, "--section=pre-data", dump_dir], env=env, check=True)

    print("## datan vienti tietokantaan pg_restorella moniajona ##")
    subprocess.run(["pg_restore", "-U", user, "-d", target_db, "--section=data", "-j", str(jobs), dump_dir], env=env,
                   check=True)

    print("## lisätään indexit ##")
    subprocess.run(["pg_restore", "-U", user, "-d", target_db, "--section=post-data", "-j", str(jobs), dump_dir],
                   env=env,
                   check=True)

    end = datetime.now()

    print(f"## valmista! Aikaa kului {end - start} ##")


def _download_from_google_drive(destination, folder_id):
    if not os.path.exists(destination):
        os.makedirs(destination)

    print(f"Ladataan tiedot Google Driven kansiosta: {folder_id}")

    gdown.download_folder(id=folder_id, output=destination, quiet=False)

    print("\nTiedostot ladattu kansioon:")
    print(os.listdir(destination))


def _populate_boroughs():
    with psycopg2.connect(dbname=DST_DB, user=DST_USER, password=DST_PWD) as conn:
        with conn.cursor() as cur:

            cur.execute("DELETE FROM zones")
            cur.execute("DELETE FROM boroughs")
            conn.commit()

            _query = 'INSERT INTO boroughs(id, borough_name) VALUES (%s, %s)'
            _data = {1: 'Manhattan', 2: 'Brooklyn', 3: 'Queens', 4: 'Bronx', 5: 'Staten Island', 6: 'EWR', 7: 'Unknown'}
            try:
                for key, value in _data.items():
                    cur.execute(_query, (key, value))
                conn.commit()
            except Exception as e:
                conn.rollback()
                traceback.print_exc()


def _populate_payment_types():
    with psycopg2.connect(dbname=DST_DB, user=DST_USER, password=DST_PWD) as conn:
        with conn.cursor() as cur:

            cur.execute("DELETE FROM payment_types")
            conn.commit()

            _query = 'INSERT INTO payment_types(id, payment_type) VALUES (%s, %s)'
            _data = {1: 'Credit Card', 2: 'Cash', 3: 'No charge', 4: 'Dispute', 5: 'Unknown', 6: 'Voided trip',
                     0: 'Flex fare'}
            try:
                for key, value in _data.items():
                    cur.execute(_query, (key, value))
                    conn.commit()
            except Exception as e:
                conn.rollback()
                traceback.print_exc()


def _populate_vendors():
    with psycopg2.connect(dbname=DST_DB, user=DST_USER, password=DST_PWD) as conn:
        with conn.cursor() as cur:

            cur.execute("DELETE FROM vendors")
            conn.commit()

            _query = 'INSERT INTO vendors("VendorID", vendor_name) VALUES (%s, %s)'
            vendors = {1: 'Creative Mobile Technologies (CMT)', 2: 'VeriFone Inc. (VTS)', 3: 'Other/Unknown'}
            try:
                for key, value in vendors.items():
                    cur.execute(_query, (key, value))
                    conn.commit()
            except Exception as e:
                conn.rollback()
                traceback.print_exc()


def _populate_rate_codes():
    with psycopg2.connect(dbname=DST_DB, user=DST_USER, password=DST_PWD) as conn:
        with conn.cursor() as cur:

            cur.execute("DELETE FROM rate_codes")

            conn.commit()

            _query = 'INSERT INTO rate_codes("RatecodeID", code) VALUES (%s, %s)'
            _data = {1: 'Standard Rate', 2: 'JFK', 3: 'Newark', 4: 'Nassau or Westchester', 5: 'Negotiated fare',
                     6: 'Group ride', 99: 'Unknown/Faulty'}
            try:
                for key, value in _data.items():
                    cur.execute(_query, (key, value))
                conn.commit()
            except Exception as e:
                print("#####################################virhe", e)
                conn.rollback()
                traceback.print_exc()


def _populate_service_zones():
    # {1: 'Yellow Zone', 2: 'Boro Zone', 3: 'Airports', 4: 'EWR', 5: 'N/A'}
    with psycopg2.connect(dbname=DST_DB, user=DST_USER, password=DST_PWD) as conn:
        with conn.cursor() as cur:

            cur.execute("DELETE FROM zones")
            cur.execute("DELETE FROM service_zones")

            conn.commit()

            _query = 'INSERT INTO service_zones(id, service_zone_name) VALUES (%s, %s)'
            _data = {1: 'Yellow Zone', 2: 'Boro Zone', 3: 'Airports', 4: 'EWR', 5: 'N/A'}
            try:
                for key, value in _data.items():
                    cur.execute(_query, (key, value))
                conn.commit()
            except Exception as e:
                conn.rollback()
                traceback.print_exc()


def _populate_zones():
    df = pd.read_csv('taxi_zone_lookup.csv', keep_default_na=False)
    df.columns = ['LocationID', 'borough_id', 'zone_name', 'service_zone_id']
    borough_map = {
        'Manhattan': 1, 'Brooklyn': 2, 'Queens': 3, 'Bronx': 4,
        'Staten Island': 5, 'EWR': 6, 'Unknown': 7, 'N/A': 7
    }

    df['borough_id'] = df['borough_id'].map(borough_map).fillna(7).astype(int)

    service_map = {
        'Yellow Zone': 1, 'Boro Zone': 2, 'Airports': 3, 'EWR': 4, 'Unknown': 5, 'N/A': 5
    }

    df['service_zone_id'] = df['service_zone_id'].map(service_map).fillna(5).astype(int)
    # df.columns = ['LocationID', 'borough_id', 'zone_name', 'service_zone_id']
    _query = 'INSERT INTO zones("LocationID", borough_id, zone_name, service_zone_id) VALUES (%s, %s, %s, %s)'
    with psycopg2.connect(dbname=DST_DB, user=DST_USER, password=DST_PWD) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM zones")
            conn.commit()
            try:
                for _index, row in df.iterrows():
                    # (1, {'LocationID': 1, ''borough_id': 2})
                    cur.execute(_query, (row['LocationID'], row['borough_id'], row['zone_name'],
                                         row['service_zone_id']))
                conn.commit()
            except Exception as e:
                conn.rollback()
                traceback.print_exc()


def run():
    while True:
        _choice = input(
            "Mitä haluat tehdä (\n0: lopeta, \n1: luo tietokanta, \n2: lataa valmis datapaketti Google Drivesta, \n3: vendorit, \n4: payment_typet, \n5: borought, \n6: service_zonet, \n7: rate_codet, \n8: zonet, \n9: yellow_trips): ")

        if _choice == '0':
            break
        elif _choice == '1':
            dst_user = DST_USER
            dst_pwd = DST_PWD
            dst_db = DST_DB
            dst_db_port = DST_DB_PORT

            _create_db(dst_user, dst_pwd, dst_db, dst_db_port)

        elif _choice == '2':
            _download_from_google_drive(destination='./data', folder_id=FOLDER_ID)
        elif _choice == '3':

            _populate_vendors()
        elif _choice == '4':
            _populate_payment_types()
        elif _choice == '5':
            _populate_boroughs()

        elif _choice == '6':
            _populate_service_zones()

        elif _choice == "7":
            _populate_rate_codes()
        elif _choice == "8":
            _populate_zones()

        elif _choice == '9':
            user = DST_USER

            target_db = DST_DB

            dump_dir = "./data"
            with psycopg2.connect(user=user, password=env["PGPASSWORD"], database=target_db) as conn:
                with conn.cursor() as cur:
                    try:
                        cur.execute("DROP TABLE yellow_trips")
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        traceback.print_exc()
            _export_data_to_db(user, target_db, dump_dir)


if __name__ == '__main__':
    run()
