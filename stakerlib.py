import platform
import os
import re
import json
import random
from slickrpc import Proxy


# fucntion to define rpc_connection
def def_credentials(chain):
    rpcport = '';
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Windows':
        ac_dir = '%s/komodo/' % os.environ['APPDATA']
    if chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
    with open(coin_config_file, 'r') as f:
        for line in f:
            l = line.rstrip()
            if re.search('rpcuser', l):
                rpcuser = l.replace('rpcuser=', '')
            elif re.search('rpcpassword', l):
                rpcpassword = l.replace('rpcpassword=', '')
            elif re.search('rpcport', l):
                rpcport = l.replace('rpcport=', '')
    if len(rpcport) == 0:
        if chain == 'KMD':
            rpcport = 7771
        else:
            print("rpcport not in conf file, exiting")
            print("check " + coin_config_file)
            exit(1)

    return (Proxy("http://%s:%s@127.0.0.1:%d" % (rpcuser, rpcpassword, int(rpcport))))


# generate address, validate address, dump private key
def genvaldump(rpc_connection):
    # get new address
    address = rpc_connection.getnewaddress()
    # validate address
    validateaddress_result = rpc_connection.validateaddress(address)
    segid = validateaddress_result['segid']
    pubkey = validateaddress_result['pubkey']
    address = validateaddress_result['address']
    # dump private key for the address
    privkey = rpc_connection.dumpprivkey(address)
    # function output
    output = [segid, pubkey, privkey, address]
    return (output)

# function to unlock ALL lockunspent UTXOs
def unlockunspent(rpc_connection):
    try:
        listlockunspent_result = rpc_connection.listlockunspent()
    except Exception as e:
        sys.exit(e)
    unlock_list = []
    for i in listlockunspent_result:
        unlock_list.append(i)
    try:
        lockunspent_result = rpc_connection.lockunspent(True, unlock_list)
    except Exception as e:
        sys.exit(e)
    return(lockunspent_result)

# function to unlock ALL lockunspent UTXOs
def unlockunspent():
    try:
        listlockunspent_result = rpc_connection.listlockunspent()
    except Exception as e:
        sys.exit(e)
    unlock_list = []
    for i in listlockunspent_result:
        unlock_list.append(i)
    try:
        lockunspent_result = rpc_connection.lockunspent(True, unlock_list)
    except Exception as e:
        sys.exit(e)
    return(lockunspent_result)
    
# iterate addresses list, construct dictionary,
# with amount as value for each address
def sendmany64(rpc_connection, amount):
    addresses_dict = {}
    with open('list.json') as key_list:
        json_data = json.load(key_list)
        for i in json_data:
            address = i[3]
            addresses_dict[address] = amount

    # make rpc call, issue transaction
    sendmany_result = rpc_connection.sendmany("", addresses_dict)
    return(sendmany_result)

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def sendmanyloop(rpc_connection, amount, utxos):
    txid_list = []
    for i in range(int(utxos)):
        sendmany64_txid = sendmany64(rpc_connection, amount)
        txid_list.append(sendmany64_txid)
        getrawtx_result = rpc_connection.getrawtransaction(sendmany64_txid, 1)
        lockunspent_list = []
        # find change output, lock all other outputs
        for vout in getrawtx_result['vout']:
            if vout['value'] != float(amount):
                change_output = vout['n']
            else:
                output_dict = {
                    "txid": sendmany64_txid,
                    "vout": vout['n']
                    }
                lockunspent_list.append(output_dict)
        lockunspent_result = rpc_connection.lockunspent(False, lockunspent_list)
    return(txid_list)

def sendmany64_TUI(chain):
    try:
        rpc_connection = def_credentials(chain)
    except Exception as e:
        print(e)
        return(0)
    balance = float(rpc_connection.getbalance())
    print('Balance: ' + str(balance))

    AMOUNT = input("Please specify the size of UTXOs: ")
    if float(AMOUNT) < float(1):
        print('Cant stake coin amounts less than 1 coin, try again.')
        return(0)
    UTXOS = input("Please specify the amount of UTXOs to send to each segid: ")
    total = float(AMOUNT) * int(UTXOS) * 64
    print('Total amount: ' + str(total))
    if total > balance:
        print('Total sending is ' + str(total-balance) + ' more than your balance. Try again.')
        segidTotal = balance / 64
        print('Total avalible per segid is: ' + str(segidTotal))
        return(0)

    sendmanyloop_result = sendmanyloop(rpc_connection, AMOUNT, UTXOS)
    # unlock all locked utxos
    unlockunspent(rpc_connection)
    for i in sendmanyloop_result:
        print(i)
    print('Success!')

# function to do sendmany64 UTXOS times, locking all UTXOs except change
def RNDsendmanyloop(rpc_connection, amounts):
    txid_list = []
    for amount in amounts:
        sendmany64_txid = sendmany64(rpc_connection, amount)
        txid_list.append(sendmany64_txid)
        getrawtx_result = rpc_connection.getrawtransaction(sendmany64_txid, 1)
        lockunspent_list = []
        # find change output, lock all other outputs
        for vout in getrawtx_result['vout']:
            if vout['value'] != float(amount):
                change_output = vout['n']
            else:
                output_dict = {
                    "txid": sendmany64_txid,
                    "vout": vout['n']
                    }
                lockunspent_list.append(output_dict)
        lockunspent_result = rpc_connection.lockunspent(False, lockunspent_list)
    return(txid_list)

def RNDsendmany_TUI(chain):
    try:
        rpc_connection = def_credentials(chain)
    except Exception as e:
        print(e)
        return(0)

    try:
        balance = float(rpc_connection.getbalance())
    except Exception as e:
        print(e)
        return(0)

    print('Balance: ' + str(balance))

    while True:
        UTXOS = int(input("Please specify the amount of UTXOs to send to each segid: "))
        if UTXOS < 3:
            print('Must have more than 3 utxos per segid, try again.')
            continue
        TUTXOS = UTXOS * 64
        print('Total number of UTXOs: ' + str(TUTXOS))
        average = float(balance) / int(TUTXOS)
        print('Average utxo size: ' + str(average))
        variance = float(input('Enter percentage of variance: '))
        minsize = round(float(average) * (1-(variance/100)),2)
        if minsize < 1:
            print('Cant stake coin amounts less than 1 coin, try again.')
            continue
        maxsize = round(average + float(average) * (variance/100),2)
        print('Min size: ' + str(minsize))
        print('Max size: ' + str(maxsize))
        ret = input('Are you happy with these? ').lower()
        if ret.startswith('y'):
            break

    total = 0
    totalamnt = 0
    AMOUNTS = []
    finished = False

    while finished == False:
        for i in range(UTXOS):
            amnt = round(random.uniform(minsize,maxsize),2)
            totalamnt += amnt * 64
            AMOUNTS.append(amnt)
            if totalamnt > balance-0.1:
                totalamnt = 0
                AMOUNTS.clear()
                break
        if totalamnt > balance-2:
            finished = True

    sendmanyloop_result = RNDsendmanyloop(rpc_connection, AMOUNTS)
    # unlock all locked utxos
    unlockunspent(rpc_connection)
    for i in sendmanyloop_result:
        print(i)
    print('Success!')

def genaddresses(chain):
    if os.path.isfile("list.json"):
        print('Already have list.json, move it if you would like to '
              'generate another set.You can use importlist.py script to import'
              ' the already existing list.py to a given chain.')
        return(0)

    # create rpc_connection
    try:
        rpc_connection = def_credentials(chain)
    except Exception as e:
        print(e)
        return(0)
    
    # fill a list of sigids with matching segid address data
    segids = {}
    while len(segids.keys()) < 64:
        genvaldump_result = genvaldump(rpc_connection)
        segid = genvaldump_result[0]
        if segid in segids:
            pass
        else:
            segids[segid] = genvaldump_result

    # convert dictionary to array
    segids_array = []
    for position in range(64):
        segids_array.append(segids[position])

    # save output to list.py
    print('Success! list.json created. '
          'THIS FILE CONTAINS PRIVATE KEYS. KEEP IT SAFE.')
    f = open("list.json", "w+")
    f.write(json.dumps(segids_array))


# import list.json to chain
def import_list(chain):
    if not os.path.isfile("list.json"):
        print('No list.json file present. Use genaddresses.py script to generate one.')
        return(0)

    rpc_connection = def_credentials(chain)

    with open('list.json') as key_list:
        json_data = json.load(key_list)
        for i in json_data:
            print(i[3])
            rpc_connection.importprivkey(i[2])
    print('Success!')