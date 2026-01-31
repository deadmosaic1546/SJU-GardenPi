import sqlite3
from typing import List, Any

class dataStorage:
    def __init__(self, path) -> None:
        print(path)
        self.path = path

        try:
            self.conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
            self.cursor = self.conn.cursor()

        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}\nExiting...")
            exit(1)
    
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
                (entry)
            )
            output.append(self.cursor.fetchall())
        
        return output
