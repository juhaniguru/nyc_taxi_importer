import os
import subprocess
import traceback
from datetime import datetime

import gdown
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, drop_database, create_database

import models

env = os.environ.copy()

# VAIHDA TÄHÄN OMA POSTGRES-TIETOKANNAN SALASANA
env["PGPASSWORD"] = "salasana"


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

    # 4. Restore Phase C: Indexes & Constraints (Post-Data)
    # Builds B-Trees in one optimized pass
    print("## lisätään indexit ##")
    subprocess.run(["pg_restore", "-U", user, "-d", target_db, "--section=post-data", "-j", str(jobs), dump_dir],
                   env=env,
                   check=True)

    end = datetime.now()

    print(f"## valmista! Aikaa kului {end - start} ##")


def _download_from_google_drive(destination, folder_id):
    if not os.path.exists(destination):
        os.makedirs(destination)

    print(f"Ladataan tiedot Google Driven kansiosta: {folder_id}...")

    # Use gdown to download the folder
    gdown.download_folder(id=folder_id, output=destination, quiet=False)

    print("\nTiedostot ladattu kansioon:")
    print(os.listdir(destination))


def run():
    while True:
        _choice = input(
            "Mitä haluat tehdä (0: lopeta, 1: luo tietokanta, 2: lataa valmis datapaketti Google Drivesta, 3: vie data tietokantaan): ")

        if _choice == '0':
            break
        elif _choice == '1':
            dst_user = "postgres"
            dst_pwd = env.get("PGPASSWORD", "salasana")
            dst_db = input(f"Anna tietokannan (Postgres) nimi (oletuksena nyc_taxi): ")
            dst_db_port = input("Anna tietokannan (Postgres) portti (oletuksena 5432): ")
            if dst_db == "":
                dst_db = "nyc_taxi"
            if dst_db_port == "":
                dst_db_port = "5432"
            _create_db(dst_user, dst_pwd, dst_db, dst_db_port)
        elif _choice == '2':
            _download_from_google_drive(destination='./data', folder_id='14KXVkHTFpYOlKNB3Eh5LySHvbLfVpsmy')

        elif _choice == '3':
            user = input("Tietokannan käyttäjä (oletuksena postgres): ")
            if user == "":
                user = "postgres"
            target_db = input("Anna tietokannan nimi (oletuksena nyc_taxi): ")
            if target_db == "":
                target_db = "nyc_taxi"
            dump_dir = "./data"
            with psycopg2.connect(user=user, password=env["PGPASSWORD"], db=target_db) as conn:
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
