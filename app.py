from factory import create_app

app = create_app()
DEBUG_MODE = False

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE)