from web_visualizer import app
import random
import urllib.request
import json
from flask import jsonify, request, g
from web_visualizer.classes import Router, LandingPoint, Point
from web_visualizer.database import Database
from web_visualizer import db

# Constants


IP_ADDRESSES_PATH = './web_visualizer/data/ip_addresses.sqlite3'
LANDING_POINTS_DATA = './web_visualizer/data/landing_points.json'

# Data Definitions

# Routers: Generates GeoJSON locations of _num_routers_ routers


@app.route("/routers")
def routers():
    # Randomly select ip addresses from table to represent the routers
    num_routers = request.args.get("num_routers")

    routers = router_points(num_routers)
    points = landing_points()

    store_points(routers, points)

    # Provide a jsonified version for the client to render
    return jsonify(list(map(lambda point: point.toJson(), routers+points)))

# router_points : Number -> [List-of Router]
# Uses the ip_addresses database to generate a list of Routers, of size _num_routers_


def router_points(num_routers):
    ip_addresses_db = Database(IP_ADDRESSES_PATH)
    routers = []

    # Change to insert num_routers as argument instead (to avoid database manipulation)
    for ip in ip_addresses_db.query_db('SELECT * FROM ip_addresses ORDER BY RANDOM() LIMIT ?',
                                       [num_routers]):
        routers.append(
            Router(ip=ip["ip"], latitude=ip["latitude"], longitude=ip["longitude"],
                   continent_code=ip["continent_id"]))
    return routers


# landing_points : _ -> [List-of LandingPoint]
# Uses the data on oceanic cables to generate a list of LandingPoints
def landing_points():
    # Try loading from JSON file, and test speed
    with open(LANDING_POINTS_DATA) as landing_points_file:
        landing_points_data = json.load(landing_points_file)

    landing_points = []

    for landing_point in landing_points_data["features"]:
        latitude = landing_point["geometry"]["coordinates"][1]
        longitude = landing_point["geometry"]["coordinates"][0]
        landing_points.append(LandingPoint(
            point_id=landing_point["properties"]["id"], latitude=latitude, longitude=longitude, continent_code=None))

    # Temporary solution: Just return the landing points themselves, without cable data
    return landing_points


# store_points : [List-of Router] [List-of LandingPoint] -> _
# Stores the points in sqlite3 database for later access
# EFFICIENCY: FAST
def store_points(routers, landing_points):
    if Point.query.first() != None:
        Point.query.delete()
    Point.query.delete()
    for router in routers:
        db.session.add(router)
    if LandingPoint.query.first() == None:
        for landing_point in landing_points:
            db.session.add(landing_point)
    # Commit after all insertions after finished
    db.session.commit()
