import sqlite3
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)

plot_bp = Blueprint('api', __name__, url_prefix='/api')

class PlotDB:
    def __init__(self, db_loc: str) -> None:
        self.db_path = db_loc

        try:
            self.conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
            self.cursor = self.conn.cursor()

            # Enable WAL mode (persistent)
            self.cursor.execute("PRAGMA journal_mode=WAL;")
            
            self.cursor.execute("PRAGMA synchronous=NORMAL;")
            self.cursor.execute("PRAGMA foreign_keys=ON;")

            self.conn.execute("PRAGMA busy_timeout=30000;")  # 30 seconds

        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}\nExiting...")
            exit(1)

    def getDataFromAllPlots(self):
        try:
            self.cursor.execute(
                "SELECT * FROM plotData;"
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print("Failed to grab data from db: {e}")
            return []
    
    def getPlotIDs(self):
        try:
            self.cursor.execute(
                "SELECT Plot_ID FROM plotData GROUP BY Plot_ID;"
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print("Failed to grab plot ids from db: {e}")
            return []
        
    def getDataFromPlot(self, plotID: int):
        try:
            self.cursor.execute(
                "SELECT * FROM plotData WHERE Plot_ID = ?;",
                (int(plotID))
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print("Failed to grab data from db: {e}")
            return []
        except e:
            print("Misc Error: {e}")
            return []
        
plot_db = PlotDB(current_app.config["PLOT_DB"])

@plot_bp.route('/all')
def pullData():
    return json.dumps(plot_db.getDataFromAllPlots())