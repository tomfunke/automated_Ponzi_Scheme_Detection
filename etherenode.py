import pandas as pd
from web3 import Web3
import logging

def check_if_connection_is_established(node_url):
    # w3 is instance of Web3 class to connect to the Ethereum node
    # returns w3 if connection is established
    w3 = Web3(Web3.HTTPProvider(node_url))
    if w3.is_connected():
        print("Connection to Ethereum node established")
        return w3
    else:
        raise ConnectionError("Failed to connect to the Ethereum node.")


def check_addresses_for_address_type(addresses, node_url):
    """
    to check if addresses are a smart contract or an externally owned account (EOA)
    :param addresses: list of Ethereum addresses
    :param node_url: URL of the Ethereum node
    
    """
    # after connection is established, you can use the w3 instance to interact with the Ethereum blockchain
    w3 = check_if_connection_is_established(node_url)

    # Configure the logging module to include the timestamp
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    
    address_dict = {}
    for address in addresses:
        address_type = check_if_address_is_sc_or_eoa(address, w3)
        logging.info(f"{address} is a {address_type}")
        address_dict[address] = address_type
    
    return address_dict


def check_if_address_is_sc_or_eoa(address, w3):
    address_checksum = Web3.to_checksum_address(address)    
    bytecode = w3.eth.get_code(address_checksum)
    
    # if the bytecode is empty, the address is an EOA
    if bytecode.hex() == "0x":
        address_type = "EOA"
    else:
        address_type = "CA"

    return address_type

