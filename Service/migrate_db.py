import os
import psycopg2
import time
import json
import serviceConstants as const
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
    creds: list[str] = __get_db_auth()
    conn = psycopg2.connect(
        host=const.HOST,
        database=const.DATABASE_NAME,
        user='postgres',
        password='password')
    return conn


def __get_bulk_processed_cik(connection, cursor) -> list[str]:
    cursor.execute(const.GET_PROCESSED_CIK_QUERY)
    cikList = cursor.fetchall()
    connection.commit()
    return cikList


def __download_data() -> None:
    req = Request(
        url=const.FACTS_ZIP_DOWNLOAD_URL,
        headers={'User-Agent': const.USER_AGENT_VALUE}
    )
    with urlopen(req) as zipresp:
        with ZipFile(BytesIO(zipresp.read())) as zfile:
            zfile.extractall(const.DATA_DIRECTORY)


if __name__ == '__main__':

    startTime = time.time()

    __download_data()

    connection = __get_db_connection()
    cursor = connection.cursor()

    cikTupleList = __get_bulk_processed_cik(connection, cursor)

    files = [
        os.path.abspath(file) for file in os.listdir(const.DATA_DIRECTORY)
    ]
    if (len(files) > 3):
        __download_data()
    cikList = []
    filesToProcess = []
    for i in range(len(files)):
        cikIndex = files[i].find('CIK')
        files[i] = '%s\\%s\\%s' % (files[i][:cikIndex],
                                   const.DATA_DIRECTORY,
                                   files[i][cikIndex:])
        cik = files[i][-18:].replace('.json', '')
        cikTuple = (cik,)
        if (cikTuple not in cikTupleList):
            cikList.append(cik)
            filesToProcess.append(files[i])

    for i in range(len(filesToProcess)):
        print(filesToProcess[i])
        with open(filesToProcess[i]) as file:
            data = json.load(file)
            text = json.dumps(data)
            text = text.replace('\'', '')
            cursor.execute(const.CREATE_FACTS_TABLE_QUERY)
            try:
                cursor.execute(const.INSERT_DATA_QUERY % (cikList[i], text))
            except psycopg2.errors.UniqueViolation:
                pass
    connection.commit()

    cursor.close()
    connection.close()

    end = time.time()

    print("""Sticker Price Analysis Complete\n
            Elapsed time: %2d minutes, %2d seconds\n"""
          % ((end - startTime)/60, (end - startTime) % 60))
