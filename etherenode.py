import pandas as pd
from web3 import Web3

def check_if_connection_is_established(node_url):
    w3 = Web3(Web3.HTTPProvider(node_url))
    if w3.is_connected():
        print("Connection to Ethereum node established")
        return w3
    else:
        raise ConnectionError("Failed to connect to the Ethereum node.")


def Check_addresses_for_address_type(addresses, node_url):
    w3 = check_if_connection_is_established(node_url)
    for address in addresses:
        address_type = check_if_address_is_sc_or_eoa(address, w3)
        #TODO instead print return address_type as list?
        print(f"{address} is a {address_type}")


def check_if_address_is_sc_or_eoa(address, w3):
    address_checksum = Web3.to_checksum_address(address)    
    bytecode = w3.eth.get_code(address_checksum)
    
    if bytecode.hex() == "0x":
        address_type = "EOA"
    else:
        address_type = "CA"

    return address_type

