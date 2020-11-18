from flask import Flask, request, jsonify

from adapter import Adapter

app = Flask(__name__)


@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())


@app.route('/', methods=['POST'])
def call_adapter():
    data = request.get_json()
    if data == '':
        data = {}
    app.logger.debug(data)
    adapter = Adapter(data)
    ret = jsonify(adapter.result)
    app.logger.debug(adapter.result)
    return ret


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='80', threaded=True)
