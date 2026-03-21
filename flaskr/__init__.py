from flask import Flask, render_template, redirect
from dotenv import dotenv_values
import os

from flaskr.auth import auth_bp, close_auth_db
from flaskr.db_pull import plot_bp, get_plot_db


bed_data = [
	{ "temperature" : 20, "humidity": 50}, #this is used for the dummy data changes, and to make bed one at index one
	{
		"temperature": -5,
		"humidity": 0
	},
	{
		"temperature": 5,
		"humidity": 10
	},
	{
		"temperature": 15,
		"humidity": 20
	},
	{
		"temperature": 25,
		"humidity": 30
	}
	]


import random #ONLY used for this right now
def dummy_data_change():
	overall_temp = bed_data[0]["temperature"]
	overall_humidity = bed_data[0]["humidity"]
	for bed in bed_data:
		bed["temperature"] = overall_temp + random.randint(-10,10)/4
		bed["humidity"] = overall_humidity + random.randint(-10,10)/4

import os
from flask import Flask

def create_app() -> Flask:
	app = Flask(
		__name__,
		instance_relative_config=False,
		static_folder="static",
		template_folder="templates",
	)
	# Core config from environment
	app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
	app.config["AUTH_DB_PATH"] = os.environ.get(
		"GARDEN_AUTH_DB",
		"/var/lib/garden-web/auth.db"
    )
	app.config["CLUSTER_DB_PATH"] = os.environ.get(
		"GARDEN_CLUSTER_DB",
		"/var/lib/garden/plot.db"
	)

	os.makedirs(app.instance_path, exist_ok=True)
	
	app.register_blueprint(auth_bp, url_prefix="/auth")
	app.teardown_appcontext(close_auth_db)

	app.register_blueprint(plot_bp, url_prefix="/api")

	@app.route('/')
	def index():
		dummy_data_change()
		return render_template("index.html", bed=bed_data)

	@app.route('/display/<int:plot_id>', methods=['GET'])
	def display(plot_id: int):
		plotdb = get_plot_db()

		if not plotdb.checkIfPlotIDExists(plot_id):
			return redirect("/")

		return render_template("data_display.html", plot=plot_id)

	return app