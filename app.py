from flask import Flask

DEBUG_MODE = True

app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome to Samurai Claus Secret Santa! Normies!"

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE)
