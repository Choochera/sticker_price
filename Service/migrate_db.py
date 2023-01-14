import os
import psycopg2
import time
import json
from io import BytesIO
from urllib.request import Request, urlopen
from zipfile import ZipFile

def __get_db_auth() -> list[str]:
    try:
        db_username: str = os.environ["db_username"],
        db_password: str = os.environ["db_password"]
    except KeyError:
        raise Exception("Database credentials not provided")
    return [db_username, db_password]

def __get_db_connection():
    creds: list[str] = __get_db_auth()
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user='postgres',
        password='password')
    return conn

def __get_bulk_processed_cik(connection, cursor) -> list[str]:
    cursor.execute("""
            SELECT cik from facts""")
    cikList = cursor.fetchall()
    connection.commit()
    return cikList

def __download_data() -> None:
    req = Request(
        url='https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip', 
         headers={'User-Agent': 'XYZ/3.0'}
    )
    with urlopen(req) as zipresp:
        with ZipFile(BytesIO(zipresp.read())) as zfile:
            zfile.extractall('Data')

if __name__ == '__main__':

    startTime = time.time()

    __download_data()
    
    connection = __get_db_connection()
    cursor = connection.cursor()

    cikTupleList = __get_bulk_processed_cik(connection, cursor)
    
    files = [os.path.abspath(file) for file in os.listdir('Data')]
    if (len(files) > 3):
        __download_data()
    cikList = []
    filesToProcess = []
    for i in range(len(files)):
        cikIndex = files[i].find('CIK')
        files[i] = files[i][:cikIndex] + '\\Data\\' + files[i][cikIndex:]
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
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                cik varchar(13) not null primary key,
                data jsonb
            );""")
            insert_sql = """
                INSERT INTO facts (cik, data)
                values('%s', (select * from to_jsonb('%s'::JSONB)))
            """
            try:
                cursor.execute(insert_sql % (cikList[i], text))
            except psycopg2.errors.UniqueViolation:
                pass
    connection.commit()

    cursor.close()
    connection.close()

    end = time.time()
    
    print("""Database Migration Complete\n
             Elapsed time: %2d minutes, %2d seconds\n"""
             % ((end - startTime)/60, (end - startTime)%60)
        )