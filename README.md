# Blue Onion Labs Take Home Test

## Instructions

- After cloning the project, run the project locally by going into its directory and running the command:

```shell
docker-compose up --build
```

- In order to see all the available routes, open the browser, and access the URL:

```shell
https://localhost:5000/
```

- Access the following route to intialize the DB before using the application:

```shell
https://localhost:5000/initdb
```

## Answers

### Main task (Part 3)

The following query fetches for the last position of a satellite, given an id `{id}` and a time `{T}`.

```sql
SELECT LONGITUDE, LATITUDE
  FROM starLinks
  WHERE STARLINK_ID='{id}'
  AND CREATION_DATE<='{T}'
  ORDER BY CREATION_DATE
  DESC LIMIT 1;
```

That query means: get all data of a particular satellite with a given `{id}`, then filter the results for only those records that happened before a given `{T}`. Finally, sort that result from the most recent to the oldest, and get only the first occurence. The answer will be the `LONGITUDE` and `LATITUDE` attributes of this very instance.

#### Examples

##### Method 1

Access the route:

```txt
/result_form
```

and fill up the form with the required information.

##### Method 2

Alternativelly, access the following route, passing the `{id}`, `{T-date}` and `{T-time}`:

```txt
/result?id={id}&T-date={T-date}&T-time={T-time}
```

The instant `{T}` will be a combination of `{T-date}` and `{T-time}`, where `T-date` is in the format `YYYY-MM-AA`, and `T-time` is in the format `HH%3AMM`. For instance, the response for the input

```txt
id = 5eed7714096e59000698565c
T-date = 2021-01-26
T-time = 13%3A00
```

should give:

```json
[
  {
    "LATITUDE": -40,
    "LONGITUDE": 152
  }
]
```

### Bonus task (Part 4)

The solution for this problem is done in 3 steps.

First, we need to get the set of measurements taken at the closest time, given a time `{T}`.

```sql
SELECT CREATION_DATE,
       ABS(DATEDIFF(CREATION_DATE, '{T}')) AS difference
  FROM starLinks
  ORDER BY difference
  ASC LIMIT 1
```

That query means: take the absolute value of the difference between the time a sample was taken and the given `{T}`. Sort the result from the least to the hightest, and return the first occurence.

Now, in the second step, we use that result as an input `{C}` to a second query

```sql
SELECT * FROM starLinks WHERE CREATION_DATE='{C}'
```

which will get all measurement samples taken at a particular instant `{C}`.

Finally, in the third step, iterate over this set of measurements and calculate the _haversine_ distance between each instance's coordiates and a given point `{P}`.

#### Examples

##### Method 1

Access the route:

```txt
/bonus_form
```

and fill up the form with the required information.

##### Method 2

Alternatively, access the following route, passing the `{T-date}`, `{T-time}`, `{lat}`, `{long}`:

```txt
http://localhost:5000/bonus?T-date={T-date}&T-time={T-time}&lat={lat}&long={long}
```

The instant `{T}` will be a combination of `{T-date}` and `{T-time}`, where `T-date` is in the format `YYYY-MM-AA`, and `T-time` is in the format `HH%3AMM`. In a similar way, the potision `{C}` will be a combination of `{lat}` and `{long}` to represent the latitude and logitude values, respectively. For instance, the response for the input

```txt
T-date = 2021-01-26
T-time = 13%3A00
lat = 80
long = 80
```

should give:

```json
{
  "CREATION_DATE": "2021-01-26 02:30:00",
  "ID": 177,
  "LATITUDE": 53,
  "LONGITUDE": 12,
  "STARLINK_ID": "5eed7714096e5900069856bd"
}
```

#### Notes on the Bonus Task

1. Both queries could be combined into a single query statement. But I was starting to spend too much time on that. So I decided to split it up.

2. There is a possibiliy that this algorightm is not always accurate. That's because it is assumed that all satellites instances have their position recorded. Thus every timestamp would contain the position of each satellite. However, from the observed data, this is not the case. For an improved response, another solution might require us to know the position of every satellite instance at a given time. For doing that we should consider their speeds and trajectory directions (we could ignore decaying speed as a start).
