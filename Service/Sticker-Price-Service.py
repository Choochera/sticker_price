from flask import Flask, jsonify, request
import os
import psycopg2
import serviceConstants as const

app = Flask(__name__)


def get_db_auth() -> list[str]:
    try:
        db_username: str = os.environ[const.DB_USERNAME_KEY],
        db_password: str = os.environ[const.DB_PASSWORD_KEY]
    except KeyError:
        return [const.DEFAULT_DB_USERNAME,
                const.DEFAULT_DB_PASSWORD]
    return [db_username, db_password]


def get_db_connection():
    creds: list[str] = get_db_auth()
    conn = psycopg2.connect(
        host=const.HOST,
        database=const.DATABASE_NAME,
        user=creds[0][0],
        password=creds[1])
    return conn


@app.route('/getFacts/<cik>')
def getFacts(cik: str):
    cursor = connection.cursor()
    cursor.execute(const.GET_DATA_QUERY % cik)
    facts = cursor.fetchall()
    cursor.close()
    return jsonify(facts)


@app.route('/getBulkFacts', methods=[const.POST])
def getBulkFacts():
    connection = get_db_connection()
    cursor = connection.cursor()
    if (request.method == const.POST):
        cikList: list[str] = request.json[const.CIK_LIST]
        query_string: str = const.GET_DATA_QUERY % cikList[0]
        i = 1
        while i in range(len(cikList)):
            query_string = query_string + const.APPEND_CIK_QUERY % cikList[i]
            i += 1
    cursor.execute(query_string)
    facts = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(facts)


if __name__ == '__main__':
    connection = get_db_connection()
    app.run(threaded=True)
    connection.close()
