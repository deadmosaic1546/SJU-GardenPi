import sqlite3
import json
from typing import List, Any

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, jsonify
)

plot_bp = Blueprint('api', __name__, url_prefix='/api')

class PlotDB:
    def __init__(self, db_loc: str) -> None:
        print(db_loc)
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
            print(f"Error connecting to plot database: {e}\nExiting...")
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
                (int(plotID),)
            )
            return self.cursor.fetchall()[0]
        except sqlite3.Error as e:
            print("Failed to grab data from db: {e}")
            return []
        except e:
            print("Misc Error: {e}")
            return []

    # Outputs a list of lists. The inner lists contain the most recent data from the db
    def pullRecentDataEntry(self, plotID=-1) -> List[Any] :
        if plotID == -1:
            # Get all Plot IDs
            self.cursor.execute(
                "SELECT Plot_ID FROM plotData GROUP BY Plot_ID;"
            )
            entries = self.cursor.fetchall()
        else:
            entries = [(plotID,)]

        output = []

        for entry in entries:
            self.cursor.execute(
                "SELECT * FROM plotData WHERE Plot_ID = ? ORDER BY time DESC LIMIT 1;",
                (entry,)
            )
            output.append(self.cursor.fetchall())
        
        return output
    
    def checkIfPlotIDExists(self, plotID) -> bool:
        if plotID < 0:
            return False
        
        self.cursor.execute(
            "SELECT COUNT(*) FROM plots WHERE Plot_ID = ?;",
            (plotID,)
        )
        
        return int(self.cursor.fetchone()[0]) >= 1
        
def get_plot_db():
    if "plot_db" not in g:
        g.plot_db = PlotDB(current_app.config["PLOT_DB"])
    return g.plot_db

@plot_bp.route('/all', methods=['GET'])
def pullData():
    return json.dumps(get_plot_db().getDataFromAllPlots())

@plot_bp.route('/ids', methods=['GET'])
def pullIDs():
    return json.dumps(get_plot_db().getPlotIDs())

@plot_bp.route('/pull/<int:plot_id>', methods=['GET'])
def pullPlotData(plot_id: int):
    db = get_plot_db()

    if db.checkIfPlotIDExists(plot_id):
        row = db.getDataFromPlot(plot_id)

        return jsonify({
            "plot_id": row[0],
            "time": row[1],
            "light": row[2],
            "humidity": row[3],
            "moisture": row[4],
            "air_temp": row[5],
            "soil_temp": row[6]
        }) 

    return json.dumps({})