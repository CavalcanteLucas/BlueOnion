import mysql.connector
import json
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
import datetime
from haversine import haversine


app = Flask(__name__)

app.config['MYSQL_HOST'] = 'mysql'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'spacex'

mysql = MySQL(app)


def serializer(cursor):
    row_headers = [x[0] for x in cursor.description]
    results = cursor.fetchall()
    json_data = []
    for result in results:
        formatted_result = []
        for i, field in enumerate(result):
            if type(field) == datetime.datetime:
                formatted_result.append(str(result[i]))
            else:
                formatted_result.append(result[i])
        json_data.append(dict(zip(row_headers, formatted_result)))
    return json_data


@app.route('/')
def index():
    return """
    <h1>Welcome!</h1>
    <h2>Available routes</h2>
    <ul>
        <li><strong>[GET]</strong> <u>/all</u> - <em>List all routes</em></li>
        <li><strong>[GET]</strong> <u>/initdb</u> - <em>Initalize DB. Start here. Use with careful!</em>
        <li><strong>[GET]</strong> <u>/result_form</u> - <em>Form to query the answer for the 'Part 3' of the challenge</em></li>
        <li><strong>[GET]</strong> <u>/result</u> - <em>Direct route to the answer for the 'Part 3' of the challenge</em></li>
        <ul>
            <li><strong>[param]</strong> id - <em>Starlink satellite ID</em></li>
            <li><strong>[param]</strong> T(date) - <em>Date limit for last known position</em></li>
            <li><strong>[param]</strong> T(time) - <em>Time limit for last known position</em></li>
        </ul>
        <li><strong>[GET]</strong> <u>/bonus_form</u> - <em>Form to query the answer for the 'Part 4' of the challenge</em></li>
        <li><strong>[GET]</strong> <u>/bonus</u> - <em>Direct route to the answer for the 'Part 4' of the challenge</em></li>
        <ul>
            <li><strong>[param]</strong> T(date) - <em>Aproximate date to investigate</em></li>
            <li><strong>[param]</strong> T(time) - <em>Aproximate time to investigate</em></li>
            <li><strong>[param]</strong> Latitude - <em>Latitude to investigate</em></li>
            <li><strong>[param]</strong> Longitude - <em>Longitude time to investigate</em></li>
        </ul>
    </ul>
    """


@app.route('/all')
def get_all():
    cursor = mysql.connection.cursor()
    """
    Get all measurement samples from the `starLinks` table.
    """
    cursor.execute('SELECT * FROM starLinks')
    return_data = serializer(cursor)
    cursor.close()
    return jsonify(return_data)


@app.route('/result_form')
def result_form():
    return """
            <form action="/result" method="GET">
            <label>Satellite ID:<br /><input type="text" name="id" placeholder="24 hexadecimal digits ID"/></label><br />
            <label>Approximate date:<br /><input type="date" name="T-date" placeholder="mm/dd/yyyy"/></label><br />
            <label>Approximate time:<br /><input type="time" name="T-time" placeholder="H:M:S"/></label>
            <p><input type="submit" value="Give me!" /></p>
        </form>
        """


def toDate(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()


def toTime(time_string):
    return datetime.datetime.strptime(time_string, '%H:%M').time()


@app.route('/result')
def get_result():
    cursor = mysql.connection.cursor()

    starlink_id = request.args.get('id', default='', type=str)
    input_date = request.args.get(
        'T-date', default=datetime.datetime.today().date(), type=toDate
    )
    input_time = request.args.get(
        'T-time', default=datetime.datetime.now().time(), type=toTime
    )
    creation_date = datetime.datetime.combine(input_date, input_time)
    query_data = [starlink_id, creation_date]

    """
    Get the last know position of a `starLink` sample at a particular instant.
    """
    cursor.execute(
        """
        SELECT LONGITUDE, LATITUDE
        FROM starLinks
        WHERE STARLINK_ID='{}'
        AND CREATION_DATE<='{}'
        ORDER BY CREATION_DATE
        DESC LIMIT 1
        """.format(
            *query_data
        )
    )

    last_know_position = serializer(cursor)

    cursor.close()
    return jsonify(last_know_position)


@app.route('/bonus_form')
def get_bonus_form():
    return """
        <form action="/bonus" method="GET">
            <label>Approximate date:<br /><input type="date" name="T-date" placeholder="mm/dd/yyyy"/></label><br />
            <label>Approximate time:<br /><input type="time" name="T-time" placeholder="H:M:S"/></label><br />

            <label>Latitude:<br /><input type="number" name="lat" placeholder="lat"/></label><br />
            <label>Longitude:<br /><input type="number" name="long" placeholder="long"/></label>

            <p><input type="submit" value="Give me!" /></p>
        </form>
        """


@app.route('/bonus')
def get_bonus():
    cursor = mysql.connection.cursor()

    input_date = request.args.get(
        'T-date', default=datetime.datetime.today().date(), type=toDate
    )
    input_time = request.args.get(
        'T-time', default=datetime.datetime.now().time(), type=toTime
    )
    creation_date = datetime.datetime.combine(input_date, input_time)

    latitude = request.args.get('lat', default=0.0, type=float)
    longitude = request.args.get('long', default=0.0, type=float)
    input_position = (latitude, longitude)

    """
    Get the closest timestamp from a particular instant.
    """
    cursor.execute(
        """
        SELECT CREATION_DATE,
               ABS(DATEDIFF(CREATION_DATE, '{}')) AS difference
          FROM starLinks
          ORDER BY difference ASC LIMIT 1
        """.format(
            creation_date
        )
    )

    closer_creation_date = serializer(cursor)[0]['CREATION_DATE']

    """
    Get all measurements of `starLink` samples taken at a particular instant.
    """
    cursor.execute(
        "SELECT * FROM starLinks WHERE CREATION_DATE='{}'".format(
            closer_creation_date
        )
    )
    selected_data = serializer(cursor)

    min_distance = float('inf')
    closer_starlink_instance = []
    for data in selected_data:
        data_position = (
            data['LATITUDE'] or 0.0,
            data['LONGITUDE'] or 0.0,
        )
        distance = haversine(input_position, data_position)
        if distance < min_distance:
            min_distance = distance
            closer_starlink_instance = data

    cursor.close()
    return jsonify(closer_starlink_instance)


@app.route('/initdb')
def get_initdb():
    cursor = mysql.connection.cursor()

    """
    Create a `starLinks` table.
    """
    cursor.execute('DROP TABLE IF EXISTS starLinks')
    cursor.execute(
        """
    CREATE TABLE starLinks(
      ID int not null AUTO_INCREMENT,
      STARLINK_ID varchar(100) NOT NULL,
      LONGITUDE INTEGER(10),
      LATITUDE INTEGER(10),
      CREATION_DATE DATETIME NOT NULL,
      PRIMARY KEY (ID)
    )
    """
    )

    with open('./sample/starlink_sample.json', 'r') as json_data:
        starlink_sample_json = json.load(json_data)

        for item in starlink_sample_json:

            starlink_data = [
                item['id'],
                item['longitude'] or 'null',
                item['latitude'] or 'null',
                item['spaceTrack']['CREATION_DATE'],
            ]

            """
            Isert measurement sample in the `starLinks` table.
            """
            cursor.execute(
                """
                INSERT INTO starLinks(STARLINK_ID, LONGITUDE, LATITUDE, CREATION_DATE)
                VALUES("{}", {}, {}, "{}")
            """.format(
                    *starlink_data
                )
            )

    mysql.connection.commit()

    cursor.close()
    return """
    <h1>DB Initialized succesfully!</h1>
    """


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')
