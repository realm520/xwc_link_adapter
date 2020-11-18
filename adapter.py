from xt_api import Api
from xwc_api import XWC


class Adapter:
    def __init__(self, input):
        self.id = input.get('id', '1')
        self.request_data = input.get('data')
        if self.validate_request_data():
            # self.set_params()
            self.create_request()
        else:
            self.result_error('No data provided')

    def validate_request_data(self):
        if self.request_data is None:
            return False
        # if self.request_data == {}:
            # return False
        return True

    def create_request(self):
        try:
            # 'https://127.0.0.1:50807/', 
            xt = Api('', '')
            data = xt.get_ticker('xt_usdt')
            self.result = data['price']
            print(self.result)
            data['result'] = 'success'
            self.result_success(data['price'])
        except Exception as e:
            self.result_error(e)

    def result_success(self, data):
        self.result = {
            'jobRunID': self.id,
            'data': data,
            'result': self.result,
            'statusCode': 200,
        }

    def result_error(self, error):
        self.result = {
            'jobRunID': self.id,
            'status': 'errored',
            'error': f'There was an error: {error}',
            'statusCode': 500,
        }
