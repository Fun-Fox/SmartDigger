from flask import Flask
from source.api import diagnose

app = Flask(__name__)

from dotenv import load_dotenv

load_dotenv()

diagnose(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
