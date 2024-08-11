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


def check_if_address_is_erc20_token(address, node_url):
    # Connection
    w3 = check_if_connection_is_established(node_url)

    # eth_getCode method to check if there is code at the address.
    code = w3.eth.get_code(address)

    if code == b'':  # No code at the address
        return "EOC"
    
    # Define the ERC-20 function signatures
    erc20_functions = [
        '0x18160ddd',  # totalSupply()
        '0x70a08231',  # balanceOf(address)
        '0xa9059cbb',  # transfer(address,uint256)
        '0x095ea7b3',  # approve(address,uint256)
        '0x23b872dd'   # transferFrom(address,address,uint256)
    ]

    for func in erc20_functions:
        result = w3.eth.call({'to': address, 'data': func})
        if result == b'':  # If the function does not exist
            return False

    return "Token Address"

