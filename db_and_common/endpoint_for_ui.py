from time import time

from flask import request, json, render_template
from flask_sqlalchemy import SQLAlchemy

import features.crime
import features.popular
import features.weather
import location_api.location_app
import trip_planner.planner
from db_and_common import app

# from db_and_common.__init__ import location
BASE_URI = 'http://127.0.0.1:5009'

db = SQLAlchemy(app)


@app.route('/ui')
def parse_and_forward():
    """Parses the parameters in query string
    and posts corresponding request(s) to /v1/location (inside location_api.location_app)"""
    i = 1
    body = {}

    start = None
    end = None
    trip = {
        "start": "",
        "others": [],
        "end": ""
    }

    while (request.args.get('Location ' + (str(i))) is not None):
        print "query string from UI: " + request.query_string
        print "Location " + (str(i)) + ": " + request.args.get('Location ' + (str(i)))
        name = "Location " + (str(i))
        body['name'] = name
        body['address'] = request.args.get(name).replace('+', ' ')
        # body_json = json.dumps(body)
        # resp = requests.post(url=BASE_URI+'/v1/locations', json=body_json)
        # resp = location_api.location_app.create(body)

        loc = location_api.location_app.persist(body=body)
        print loc.id
        loc_id = 'v1/locations/' + str(loc.id)
        if i == 1:
            trip['start'] = loc_id
        else:
            trip['others'].append(loc_id)
        trip['end'] = loc_id
        i += 1
    if trip['others'] is not None:
        trip['others'].pop()
    print trip
    trip_json = json.dumps(trip)

    # call prabhu's API
    # requests.post(BASE_URI + '/trips', json=trip_json)  # or replace with direct functin call


    best_route = []
    resp = trip_planner.planner.plan(trip_json)
    for location_str in resp['best_route_by_costs']:
        row = json.loads(location_api.location_app.queryDB(location_str.split('/')[2]).data)
        loc_dict = {
            "latitude": row['coordinate']['latitude'],
            "longitude": row['coordinate']['longitude'],
            "address": row['address']
        }
        best_route.append(loc_dict)
        print json.dumps(best_route)

    # TODO: handle no responses from APIs

    time_start = time()
    weather = features.weather.get_weathers(best_route)['descriptions']
    # dangerous_streets = features.crime.get_streets(best_route)
    # popular = features.popular.get_popular(best_route)
    print time() - time_start
    return render_template('result.html', route=best_route,
                           providers=resp['providers'],
                           route1=json.dumps(best_route),
                           weather=weather)

    # return "Hello from locationApp, Gurnoor<br/> Query: " + request.query_string + \
    #        "<br/> location 0: " + request.args.get('Location 0')
