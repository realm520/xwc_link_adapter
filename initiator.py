import requests


def triggerJob(jobId):
    url = f"http://localhost:6688/v2/specs/{jobId}/runs"
    headers = {
        'content-type': "application/json",
        'X-Chainlink-EA-AccessKey': "e68bcbe53246467a89af3714e41c344a",
        'X-Chainlink-EA-Secret': "MLuHmL9IXb20x53W6Zca1J80tWGBrl7CWxTlm9A7VxpQCGObMP+JmloCz8YgInN6"
    }
    response = requests.request("POST", url, data=None, headers=headers)
    print(response.text)


if __name__ == '__main__':
    triggerJob("ae3315b00fb444938f90110d6097a174")
