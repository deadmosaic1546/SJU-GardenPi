import socket
import os
from dotenv import dotenv_values
import sqlite3
import json
from typing import List, Any

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, jsonify
)

plot_bp = Blueprint('api', __name__, url_prefix='/api')

def get_db_port():
    # Try to get DB_PORT from environment or .env
    port = os.environ.get("DB_PORT")
    if port:
        return int(port)
    env_vars = dotenv_values()
    return int(env_vars.get("DB_PORT", 0))

# /api/live/<int:device_id> endpoint
@plot_bp.route('/live/<int:device_id>', methods=['GET'])
def live_device(device_id: int):
    db_port = get_db_port()
    if not db_port:
        return jsonify({"Failure": "Unable to reach DB"}), 500
    try:
        with socket.create_connection(("127.0.0.1", db_port), timeout=5) as sock:
            # Send the device_id as JSON: {"request": device_id}
            sock.sendall(json.dumps({"request": device_id}).encode("utf-8"))
            # Receive up to 1024 bytes (adjust as needed)
            data = sock.recv(1024)
            # Try to decode as JSON
            try:
                response = data.decode("utf-8")
                json_data = json.loads(response)
                if "Failure" in json_data:
                    return jsonify(json_data), 400
                return jsonify(json_data)
            except Exception as e:
                return jsonify({"Failure": f"Invalid JSON from device: {e}"}), 502
    except Exception as e:
        return jsonify({"Failure": "Socket error:"}), 502

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
                "SELECT Plot_ID FROM plots GROUP BY Plot_ID;"
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print("Failed to grab plot ids from db: {e}")
            return []
        
    def getDataFromPlot(self, plotID: int):
        try:
            self.cursor.execute(
                "SELECT * FROM plotData WHERE Plot_ID = ? ORDER BY time DESC LIMIT 1;",
                (int(plotID),)
            )
            rows = self.cursor.fetchall()
            if not rows:
                # no entries for this plot
                return None
            return rows[0]
        except sqlite3.Error as e:
            print(f"Failed to grab data from db: {e}")
            return None
        except Exception as e:
            print(f"Misc Error: {e}")
            return None

    def getDailyAverage(self, plotID: int):
        try:
            self.cursor.execute("""
                SELECT 
                    Plot_ID,
                    MAX(time),
                    AVG(light),
                    AVG(humidity),
                    AVG(moisture),
                    AVG(air_temp),
                    AVG(soil_temp)
                FROM plotData
                WHERE Plot_ID = ?
                  AND datetime(replace(time, 'T', ' ')) >= datetime('now', '-1 day');
            """, (int(plotID),))

            row = self.cursor.fetchone()

            return row if row else None

        except sqlite3.Error as e:
            print(f"DB Error (Daily Avg): {e}")
            return None
        except Exception as e:
            print(f"Misc Error: {e}")
            return None
        
    def getWeeklyAverage(self, plotID: int):
        try:
            self.cursor.execute("""
                SELECT 
                    plot_id, MAX(time), AVG(light), AVG(humidity), AVG(moisture), AVG(air_temp), AVG(soil_temp)
                FROM plotData
                WHERE Plot_ID = ?
                  AND datetime(replace(time, 'T', ' ')) >= datetime('now', '-7 day');
            """, (int(plotID),))

            row = self.cursor.fetchone()
            return row if row else None

        except sqlite3.Error as e:
            print(f"DB Error (Weekly Avg): {e}")
            return None
        except Exception as e:
            print(f"Misc Error: {e}")
            return None

    def getMonthlyAverage(self, plotID: int):
        try:
            self.cursor.execute("""
                SELECT 
                    plot_id, MAX(time), AVG(light), AVG(humidity), AVG(moisture), AVG(air_temp), AVG(soil_temp)
                FROM plotData
                WHERE Plot_ID = ?
                  AND datetime(replace(time, 'T', ' ')) >= datetime('now', '-30 day');
            """, (int(plotID),))

            row = self.cursor.fetchone()
            return row if row else None

        except sqlite3.Error as e:
            print(f"DB Error (Monthly Avg): {e}")
            return None
        except Exception as e:
            print(f"Misc Error: {e}")
            return None


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
        g.plot_db = PlotDB(current_app.config["CLUSTER_DB_PATH"])
    return g.plot_db

@plot_bp.route('/all', methods=['GET'])
def pullData():
    return json.dumps(get_plot_db().getDataFromAllPlots())

@plot_bp.route('/ids', methods=['GET'])
def pullIDs():
    # existing endpoint returns raw tuples; keep for compatibility
    return json.dumps(get_plot_db().getPlotIDs())

@plot_bp.route('/list', methods=['GET'])
def listIDs():
    # return a simple JSON array of integers representing all plot IDs
    ids = get_plot_db().getPlotIDs()
    flat = [item[0] for item in ids]
    print(flat)
    return jsonify(flat)  # use jsonify for proper content-type

@plot_bp.route('/pull/<int:plot_id>', methods=['GET'])
def pullPlotData(plot_id: int):
    db = get_plot_db()

    if not db.checkIfPlotIDExists(plot_id):
        # plot not registered at all
        return jsonify({"error": "plot not found"}), 404

    row = db.getDataFromPlot(plot_id)
    if row is None:
        # registered but no data entries
        return jsonify({"error": "no data for plot"}), 404

    return jsonify({
        "plot_id": plot_id,
        "time": row[1],
        "light": row[2] if not row[2] else round(row[2], 2),
        "humidity": row[3] if not row[3] else round(row[3], 2),
        "moisture": row[4] if not row[4] else round(row[4], 2),
        "air_temp": row[5] if not row[5] else round(row[5], 2),
        "soil_temp": row[6] if not row[6] else round(row[6], 2)
    })

@plot_bp.route('/average/daily/<int:plot_id>', methods=['GET'])
def pullDailyAverage(plot_id: int):
    db = get_plot_db()

    if not db.checkIfPlotIDExists(plot_id):
        # plot not registered at all
        return jsonify({"error": "plot not found"}), 404
    
    row = db.getDailyAverage(plot_id)
    if row is None:
        # registered but no data entries
        return jsonify({"error": "no data for plot"}), 404
    
    return jsonify({
        "plot_id": plot_id,
        "time": row[1],
        "light": row[2] if not row[2] else round(row[2], 2),
        "humidity": row[3] if not row[3] else round(row[3], 2),
        "moisture": row[4] if not row[4] else round(row[4], 2),
        "air_temp": row[5] if not row[5] else round(row[5], 2),
        "soil_temp": row[6] if not row[6] else round(row[6], 2)
    })

@plot_bp.route('/average/weekly/<int:plot_id>', methods=['GET'])
def pullWeeklyAverage(plot_id: int):
    db = get_plot_db()

    if not db.checkIfPlotIDExists(plot_id):
        # plot not registered at all
        return jsonify({"error": "plot not found"}), 404
    
    row = db.getWeeklyAverage(plot_id)
    if row is None:
        # registered but no data entries
        return jsonify({"error": "no data for plot"}), 404
    

    return jsonify({
        "plot_id": plot_id,
        "time": row[1],
        "light": row[2] if not row[2] else round(row[2], 2),
        "humidity": row[3] if not row[3] else round(row[3], 2),
        "moisture": row[4] if not row[4] else round(row[4], 2),
        "air_temp": row[5] if not row[5] else round(row[5], 2),
        "soil_temp": row[6] if not row[6] else round(row[6], 2)
    })

@plot_bp.route('/average/monthly/<int:plot_id>', methods=['GET'])
def pullMonthlyAverage(plot_id: int):
    db = get_plot_db()

    if not db.checkIfPlotIDExists(plot_id):
        # plot not registered at all
        return jsonify({"error": "plot not found"}), 404
    
    row = db.getMonthlyAverage(plot_id)
    if row is None:
        # registered but no data entries
        return jsonify({"error": "no data for plot"}), 404
    
    return jsonify({
        "plot_id": plot_id,
        "time": row[1],
        "light": row[2] if not row[2] else round(row[2], 2),
        "humidity": row[3] if not row[3] else round(row[3], 2),
        "moisture": row[4] if not row[4] else round(row[4], 2),
        "air_temp": row[5] if not row[5] else round(row[5], 2),
        "soil_temp": row[6] if not row[6] else round(row[6], 2)
    })
