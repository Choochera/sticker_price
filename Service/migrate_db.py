import os
import sys
import psycopg2
import time
import json
import serviceConstants as const
from os import listdir
from io import BytesIO
from urllib.request import Request, urlopen
from zipfile import ZipFile


def __get_db_auth() -> list[str]:
    try:
        db_username: str = os.environ[const.DB_USERNAME_KEY],
        db_password: str = os.environ[const.DB_PASSWORD_KEY]
    except KeyError:
        raise Exception("Database credentials not provided")
    return [db_username, db_password]


def __get_db_connection():
    print("Establishing database connection...")
    creds: list[str] = __get_db_auth()
    conn = psycopg2.connect(
        host=const.HOST,
        database=const.DATABASE_NAME,
        user=creds[0][0],
        password=creds[1])
    return conn


def __get_bulk_processed_cik(connection, cursor) -> list[str]:
    print("Retrieving list of processed CIK...")
    cursor.execute(const.CREATE_FACTS_TABLE_QUERY)
    cursor.execute(const.GET_PROCESSED_CIK_QUERY)
    cikList = cursor.fetchall()
    connection.commit()
    return cikList


def __drop_facts(connection, cursor) -> None:
    print("Dropping facts table from database...")
    cursor.execute(const.DROP_FACTS_TABLE_QUERY)
    connection.commit()


def __download_data() -> None:
    print("Downloading facts data from EDGAR...")
    req = Request(
        url=const.EDGAR_URL + const.DATA_ZIP_PATH,
        headers={'User-Agent': const.USER_AGENT_VALUE}
    )
    with urlopen(req) as zipresp:
        with ZipFile(BytesIO(zipresp.read())) as zfile:
            zfile.extractall(const.DATA_DIRECTORY)


def __delete_data() -> None:
    print("Deleting current facts data...")
    for file_name in listdir(const.DATA_DIRECTORY):
        if (
            file_name != const.CIK_MAP_FILENAME and
            file_name.endswith(const.JSON_EXTENSION)
        ):
            os.remove(const.DATA_DIRECTORY + '\\' + file_name)


if __name__ == '__main__':

    startTime = time.time()
    connection = __get_db_connection()
    cursor = connection.cursor()

    print("Checking repopulation flag status...")
    try:
        repopulateFlag = sys.argv[1]
        if (repopulateFlag == const.TRUE):
            repopulateFlag = True
        else:
            repopulateFlag = False
    except IndexError:
        repopulateFlag = False

    if (repopulateFlag):
        __drop_facts(connection, cursor)
        __delete_data()
        connection.commit()

    cikTupleList = __get_bulk_processed_cik(connection, cursor)
    files = [
        os.path.abspath(file) for file in os.listdir(const.DATA_DIRECTORY)
    ]
    if (len(files) < 3):
        __download_data()
        files = [
            os.path.abspath(file) for file in os.listdir(const.DATA_DIRECTORY)
        ]
        print("Inserting json data into database...")
        cikList = []
        filesToProcess = []
        for i in range(len(files)):
            cikIndex = files[i].find(const.CIK)
            files[i] = '%s\\%s\\%s' % (files[i][:cikIndex],
                                       const.DATA_DIRECTORY,
                                       files[i][cikIndex:])
            cik = files[i][-18:].replace(const.JSON_EXTENSION, const.EMPTY)
            cikTuple = (cik,)
            if (
                cikTuple not in cikTupleList and
                const.CIK_MAP not in files[i]
            ):
                cikList.append(cik)
                filesToProcess.append(files[i])

        print("Data being inserted: ")
        for i in range(len(filesToProcess)):
            print(filesToProcess[i])
            with open(filesToProcess[i]) as file:
                data = json.load(file)
                text = json.dumps(data)
                text = text.replace('\'', const.EMPTY)
                try:
                    cursor.execute(const.INSERT_DATA_QUERY % (
                        cikList[i],
                        text
                    ))
                except psycopg2.errors.UniqueViolation:
                    pass
            connection.commit()

    cursor.close()
    connection.close()

    end = time.time()

    print("""Sticker Price Database Population Complete\n
            Elapsed time: %2d minutes, %2d seconds\n"""
          % ((end - startTime)/60, (end - startTime) % 60))
