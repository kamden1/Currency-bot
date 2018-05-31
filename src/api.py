import json
import time
import logging

import MySQLdb
import MySQLdb.cursors
import _mysql_exceptions
from flask import Flask, jsonify, request

import config
import models

app = Flask(__name__)
investments = None
investors = None


@app.route("/coins/invested")
def coins_invested():
    return jsonify({"coins": str(investments.invested_coins())})


@app.route("/coins/total")
def coins_total():
    return jsonify({"coins": str(investors.total_coins())})


@app.route("/investments/active")
def investments_active():
    return jsonify({"investments": str(investments.active())})


@app.route("/investments/total")
def investments_total():
    try:
        time_from = int(request.args.get("from"))
    except TypeError:
        time_from = 0

    try:
        time_to = int(request.args.get("to"))
    except TypeError:
        time_to = 0

    return jsonify({"investments": str(investments.total(time_from=time_from, time_to=time_to))})


@app.route("/investors/top")
@app.route("/investors/top/<string:field>")
def investors_top(field="balance"):
    try:
        page = int(request.args.get("page"))
    except TypeError:
        page = 0

    try:
        per_page = int(request.args.get("per_page"))
    except TypeError:
        per_page = 100

    if per_page > 100 or per_page < 0:
        per_page = 100
    if page < 0:
        page = 0

    return jsonify(investors.top(field, page=page, per_page=per_page))


@app.route("/investor/<string:name>")
def investor(name):
    try:
        return jsonify(investors[name].get())
    except IndexError:
        return not_found("User not found")


@app.route("/")
def index():
    data = {
        "coins": {
            "invested": json.loads(coins_invested().get_data()),
            "total": json.loads(coins_total().get_data()),
        },
        "investments": {
            "active": json.loads(investments_active().get_data()),
            "total": json.loads(investments_total().get_data()),
        },
        "investors": {
            "top": json.loads(investors_top().get_data()),
        },
    }

    return jsonify(data)


@app.errorhandler(404)
def not_found(e):
    return jsonify(error=404, text=str(e)), 404


@app.before_first_request
def db_connection():
    global investments, investors

    db = None
    while not db:
        try:
            db = MySQLdb.connect(cursorclass=MySQLdb.cursors.DictCursor, **config.dbconfig)
        except _mysql_exceptions.OperationalError:
            logging.warning("Waiting 10s for MySQL to go up...")
            time.sleep(10)

    investments = models.Investments(db)
    investors = models.Investors(db)


if __name__ == "__main__":
    app.run(host="0.0.0.0")