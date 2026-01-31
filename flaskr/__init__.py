from flask import Flask, render_template

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template("index.html", bed=bed_data)
