import sqlite3
import re
import os
from dotenv import load_dotenv

load_dotenv()

__all__ = ['Recorder']

class Recorder:
    def __init__(self):
        self.conn = sqlite3.connect(os.getenv('DB_PATH'))
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bounds TEXT NOT NULL,
                x1 INTEGER,
                y1 INTEGER,
                x2 INTEGER,
                y2 INTEGER,
                screenshot_id TEXT NOT NULL,
                element_id INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def save_to_db(self, bounds, screenshot_id, element_id):
        matches = re.findall(r'\d+', bounds)
        x1, y1, x2, y2 = map(int, matches)
        self.cursor.execute('INSERT INTO elements (bounds, x1, y1, x2, y2, screenshot_id, element_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                            (bounds, x1, y1, x2, y2, screenshot_id, element_id))
        self.conn.commit()

    def is_record_exist(self, bounds, screenshot_id):

        self.cursor.execute('SELECT * FROM elements WHERE bounds = ? AND screenshot_id = ?', (bounds, screenshot_id))
        return self.cursor.fetchone() is not None

    def generate_markdown(self):
        with open(os.getenv('MD_FILE_PATH'), 'w') as md_file:
            md_file.write("# Elements Bounds Data\n\n")
            md_file.write("| ID | Bounds | X1 | Y1 | X2 | Y2 | ScreenShot_ID | Element_ID |\n")
            md_file.write("|----|--------|----|----|----|----|----|----|\n")
            self.cursor.execute('SELECT * FROM elements')
            rows = self.cursor.fetchall()
            for row in rows:
                md_file.write(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} |\n")

    def close(self):
        self.conn.close()