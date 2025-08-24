#!/usr/bin/env python3
import subprocess, json, requests

def get_balances(wallet):
    rpc = 'https://base-rpc.publicnode.com'
    npt_contract = '0xB8c2CE84F831175136cebBFD48CE4BAb9c7a6424'
    wallet_hex = wallet.replace('0x','')
    eth_data = {'jsonrpc':'2.0','id':1,'method':'eth_getBalance','params':[wallet,'latest']}
    npt_data = {'jsonrpc':'2.0','id':2,'method':'eth_call','params':[{'to':npt_contract,'data':f'0x70a08231000000000000000000000000{wallet_hex}'},'latest']}
    try:
        eth_out = subprocess.check_output(['curl','-s','-X','POST',rpc,'-H','Content-Type: application/json','-d',json.dumps(eth_data)])
        npt_out = subprocess.check_output(['curl','-s','-X','POST',rpc,'-H','Content-Type: application/json','-d',json.dumps(npt_data)])
        eth_balance = int(json.loads(eth_out)['result'],16)/1e18
        npt_balance = int(json.loads(npt_out)['result'],16)/1e18
        return eth_balance, npt_balance
    except:
        return 0.0, 0.0

def get_eth_price_usd():
    url="https://api.coingecko.com/api/v3/simple/price"
    params={"ids":"ethereum","vs_currencies":"usd"}
    try:
        response=requests.get(url,params=params,timeout=10)
        response.raise_for_status()
        data=response.json()
        return float(data['ethereum']['usd'])
    except:
        return 0.0
