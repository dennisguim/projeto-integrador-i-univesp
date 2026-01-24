from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Olá, Mundo! Nossa projeto está no ar'

if __name__ == '__main__':
    app.run(debug=True)