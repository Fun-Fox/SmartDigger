import sqlite3
import re
import os
from dotenv import load_dotenv
from source.utils.log_config import setup_logger


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
                center_x INTEGER,
                center_y INTEGER,
                screenshot_id TEXT NOT NULL,
                element_id INTEGER NOT NULL
            )
        ''')

        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS template (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        skip_center_x INTEGER,
                        skip_center_y INTEGER,
                        template_id TEXT NOT NULL
                    )
                ''')

        self.conn.commit()
        self.logger = setup_logger(__name__)

    def save_template(self, template_id, skip_center_x, skip_center_y):
        self.cursor.execute('INSERT INTO template (template_id, skip_center_x, skip_center_y) VALUES (?, ?, ?)',
                            (template_id, skip_center_x, skip_center_y))
        self.conn.commit()

    def get_template_center_point(self, template_id):
        self.cursor.execute('SELECT skip_center_x,skip_center_y FROM template WHERE template_id = ?', (template_id,))
        rows = self.cursor.fetchall()
        self.logger.info(f"{template_id},模板匹配结果为: {rows}")
        if rows:
            return rows[0][0], rows[0][1]
        return None, None

    def save_bound(self, bounds, screenshot_id, element_id):
        matches = re.findall(r'\d+', bounds)
        x1, y1, x2, y2 = map(int, matches)
        # 计算中心点坐标
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        self.cursor.execute(
            'INSERT INTO elements (bounds, x1, y1, x2, y2,center_x,center_y, screenshot_id, element_id) VALUES (?,?,?, ?, ?, ?, ?, ?, ?)',
            (bounds, x1, y1, x2, y2, center_x, center_y, screenshot_id, element_id))
        self.conn.commit()

    def is_record_exist(self, bounds, screenshot_id):
        self.cursor.execute('SELECT * FROM elements WHERE bounds = ? AND screenshot_id = ?', (bounds, screenshot_id))
        return self.cursor.fetchone() is not None

    def generate_markdown(self):
        with open(os.getenv('MD_FILE_PATH'), 'w') as md_file:
            md_file.write("# Elements Bounds Data\n\n")
            md_file.write("| ID | Bounds | X1 | Y1 | X2 | Y2 | Center_X | Center_Y | ScreenShot_ID | Element_ID |\n")
            md_file.write("|----|--------|----|----|----|----|----|----|----|----|\n")
            self.cursor.execute('SELECT * FROM elements')
            rows = self.cursor.fetchall()
            for row in rows:
                md_file.write(
                    f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} | {row[8]} | {row[9]} |\n")

    def close(self):
        self.conn.close()
