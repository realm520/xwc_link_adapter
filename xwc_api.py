# -*- coding: utf-8 -*-

import json
import logging
import requests
import fire


# transfer_to_contract_testing swapcaller XWCCTueWEr4UADuoJHidBxTe1webiT8NTYp5Z 0.01 ETH "ETH,1000000,XWC,1000000,10000000"
# transfer_to_contract swapcaller XWCCTueWEr4UADuoJHidBxTe1webiT8NTYp5Z 1 ETH "ETH,100000000,XWC,1000000,10000000" 0.001 4150 true
# invoke_contract_offline swapcaller XWCCTueWEr4UADuoJHidBxTe1webiT8NTYp5Z "caculateExchangeAmount" "ETH,100000000,XWC"
class XWC:
    def __init__(self, url, account):
        self.baseUrl = url #"http://47.75.155.116:40123"
        self.caller = account
        self.gasPrice = "0.00000001"
        self.swapAddr = {
            "xwc_eth": "XWCCJV5jJ8acWx3AfVPUT6x1K2hXRkptZ8hGB",
            "xwc_cusd": "XWCCarrfVrHCRupUbJfasasx2Rdy4Aor8eTD9",
            "xwc_tp": "XWCCcUF3uQDHzyhAuKsZ9DtFyVBcFuousjR6w"
        }
        self.tokenAddr = {
            "tp": "XWCCUXT5Dr5EdYtoHBkCsTqSUUEpNd5uf22Db",
            "cusd": "XWCCc55NYwUDeQyy2Co5hqdFt75wWUrMu71rW"
        }

    def rpc_request(self, method, args):
        args_j = json.dumps(args)
        payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
        headers = {
                'content-type': "text/plain",
                'cache-control': "no-cache",
        }
        logging.debug(self.baseUrl)
        for i in range(5):
            try:
                logging.debug("[HTTP POST] %s" % payload)
                response = requests.request("POST", self.baseUrl, data=payload, headers=headers)
                # if method == "invoke_contract":
                #     pass
                    # print(response.text)
                rep = response.json()
                if "result" in rep:
                    return rep["result"]
            except Exception:
                logging.error("Retry: %s" % payload)
                continue


    def get_depth(self, symbol):
        resp = self.rpc_request('invoke_contract_offline',
                                [self.caller, self.swapAddr[symbol], "getInfo", ""])
        return json.loads(resp)

    def _calculate_want(self, contractAddr, spend, spendNumber, target):
        params = f"{spend},{spendNumber},{target}"
        resp = self.rpc_request('invoke_contract_offline',[
                            self.caller, contractAddr, "caculateExchangeAmount", params
                        ])
        return resp

    def approve(self, asset, swapAddr, amount):
        params = f"{swapAddr},{int(amount*10**8)}"
        resp = self.rpc_request('invoke_contract',[
            self.caller, "0.00000001", 500000, self.tokenAddr[asset], "approve", params
        ])
        return resp

    def send_order(self, symbol, price, number, direction):
        pairs = symbol.upper().split('_')
        if direction == 1:
            target = pairs[0]
            spend = pairs[1]
            spendNumber = int(price*number*100000000)
        else:
            target = pairs[1]
            spend = pairs[0]
            spendNumber = int(number*100000000)
        try:
            if spend.lower() in self.tokenAddr:
                resp = self.approve(spend.lower(), self.swapAddr[symbol], number)
                logging.debug(resp)
                resp = self.rpc_request('invoke_contract', [
                    self.caller, "0.00000001", 500000, self.swapAddr[symbol], "exchange",
                    f"{self.tokenAddr[spend.lower()]},{int(number*10**8)},{target},1,100000000"
                ])
                logging.debug(resp)
                txid = resp['trxid']
                resp = self.rpc_request('get_contract_invoke_object', [txid])
                logging.debug(resp)
                for e in resp[0]['events']:
                    if e['event_name'] == 'Exchanged':
                        resp = json.loads(e['event_arg'])
                        resp['txid'] = txid
                        break
            else:
                if target.lower() in self.tokenAddr:
                    targetR = self.tokenAddr[target.lower()]
                else:
                    targetR = target
                resp = self._calculate_want(self.swapAddr[symbol], spend, spendNumber, targetR)
                logging.debug(resp)
                targetNumber = resp
                params = f"{spend},{spendNumber},{targetR},{targetNumber},100000000"
                logging.debug(f"{spendNumber/100000000:>.8f}, {int(targetNumber)/100000000:>.8f}, {spend}, {params}")
                resp = self.rpc_request('transfer_to_contract',[
                                            self.caller, self.swapAddr[symbol], f"{spendNumber/100000000:>.8f}",
                                            spend, params, '0.00000001', '100000', 'true'
                                        ])
        except Exception as e:
            logging.error(str(e))
            resp = None
        return resp
        # return {'eth': spendNumber, 'xwc': targetNumber} if direction == 1 else {'eth': targetNumber, 'xwc': spendNumber}

    def get_contract_events(self, contract, start, count):
        try:
            resp = self.rpc_request('get_contract_events_in_range', [contract, start, count])
        except:
            pass
        return resp

    def get_block_height(self):
        blockNumber = 0
        try:
            resp = self.rpc_request('network_get_info', [])
            if resp:
                blockNumber = int(resp['current_block_height'])
        except:
            pass
        return blockNumber

    def get_block(self, blockNumber):
        try:
            resp = self.rpc_request('get_block', [blockNumber])
        except:
            pass
        return resp

    def deploy_contract(self, contract_path):
        res = self.rpc_request("register_contract",[self.caller,"0.00001",500000,contract_path])
        if res is None:
            return ''
        else:
            return res["contract_id"]

    def create_account(self, account):
        res = self.rpc_request("wallet_create_account",[account])
        return res

    def list_all_accounts(self):
        res = self.rpc_request("list_my_accounts",[])
        return [(u['name'], u['addr']) for u in res]

    def dump_private_keys(self):
        res = self.rpc_request("dump_private_keys",[])
        return res

    def deploy_dai_contracts(self, params):
        cdcId = self.deploy_contract(params['cdc']['gpc'])
        cdcProxyId = self.deploy_contract(params['cdcProxy']['gpc'])
        priceFeederId = self.deploy_contract(params['priceFeeder']['gpc'])
        stableTokenId = self.deploy_contract(params['stableToken']['gpc'])
        if cdcId == '' or cdcProxyId == '' or priceFeederId == '' or stableTokenId == '':
            print(f"Failed to deploy contract: {cdcId}, {cdcProxyId}, {priceFeederId}, {stableTokenId}")
            return
        initStableToken = self.rpc_request('invoke_contract', [
                    self.caller, "0.00001", 500000, stableTokenId, "init_token",
                    f"{params['stableToken']['name']},{params['stableToken']['symbol']},{cdcId},1000000"
                ])
        print(initStableToken)
        initPriceFeeder = self.rpc_request('invoke_contract', [
                    self.caller, "0.00001", 500000, priceFeederId, "init_config",
                    f"{params['priceFeeder']['baseAsset']},{stableTokenId},{params['priceFeeder']['initPrice']},{params['priceFeeder']['maxChangeRatio']}"
                ])
        print(initPriceFeeder)
        initCdc = self.rpc_request('invoke_contract', [
                    self.caller, "0.00001", 500000, cdcId, "init_config",
                    f"{params['priceFeeder']['baseAsset']},{params['cdc']['stabilityFee']},{params['cdc']['liquidationRatio']},{params['cdc']['liquidationPenalty']},{params['cdc']['liquidationDiscount']},{priceFeederId},{stableTokenId},{cdcProxyId}"
                ])
        print(initCdc)
        return {
            "cdc": cdcId,
            "cdcProxy": cdcProxyId,
            "priceFeeder": priceFeederId,
            "stableToken": stableTokenId
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d  %H:%M:%S %a'
                    )
    xwc = XWC("http://127.0.0.1:9999", "defi")
    fire.Fire(xwc)
    # xwc.send_order("xwc_eth", 0.3891, 877543175/10**8, 0)
