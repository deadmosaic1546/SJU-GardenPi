from flask import Flask, render_template, redirect
from dotenv import dotenv_values
import os

from flaskr.auth import auth_bp, close_auth_db
from flaskr.db_pull import plot_bp, get_plot_db


bed_data = [
	"dummy data that makes it 1-indexed",
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

def create_app():
	app = Flask(__name__, instance_relative_config=True)
	
	env_vars = dotenv_values()

	app.config.from_mapping(
        SECRET_KEY=env_vars["SECRET_KEY"],
        PLOT_DB=env_vars["PLOT_DB_PATH"],
		AUTH_DB=env_vars["AUTH_DB_PATH"],
	)

	# ensure the instance folder exists
	os.makedirs(app.instance_path, exist_ok=True)
	
	app.register_blueprint(auth_bp, url_prefix="/auth")
	app.teardown_appcontext(close_auth_db)

	app.register_blueprint(plot_bp, url_prefix="/api")

	@app.route('/')
	def index():
		return render_template("index.html", bed=bed_data)

	@app.route('/display/<int:plot_id>', methods=['GET'])
	def display(plot_id: int):
		plotdb = get_plot_db()

		if not plotdb.checkIfPlotIDExists(plot_id):
			return redirect("/")

		return render_template("data_display.html", plot=plot_id)

	return app



