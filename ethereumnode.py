import pandas as pd
from web3 import Web3
import logging
from eth_utils import is_address
from web3.exceptions import ContractLogicError

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

    # Configure the logging module to include the timestamp in our loggings
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    
    address_dict = {}
    for address in addresses:
        address_type = check_if_address_is_sc_or_eoa(address, w3)
        logging.info(f"{address} is a {address_type}")
        address_dict[address] = address_type
    
    return address_dict


def check_if_address_is_sc_or_eoa(address, w3):
    if is_address(address):
        address_checksum = Web3.to_checksum_address(address)
    else:
        raise ValueError(f"Invalid address format: {address}")
    
    address_checksum = Web3.to_checksum_address(address)    
    bytecode = w3.eth.get_code(address_checksum)
    
    # if the bytecode is empty, the address is an EOA
    if bytecode.hex() == "0x":
        address_type = "EOA"
    else:
        address_type = "CA"

    return address_type


def check_if_address_is_a_token(address, node_url, likehood_threshold):
    """
    Checks weather the address is a token contract or not.
    :param address: Ethereum address
    :param node_url: URL of the Ethereum node
    :param likehood_threshold: threshold to determine if the address is a token contract or not

    Tests if the address is a token contract by checking if the address has the common function signatures of ERC-20 and ERC-721(NFT) token contracts.
    """
    # Connection
    w3 = check_if_connection_is_established(node_url)

    address_checksum = Web3.to_checksum_address(address)
    # eth_getCode method to check if there is code at the address.
    code = w3.eth.get_code(address_checksum)

    if code == b'':  # No code at the address
        print("No code at the address->EOA")
        return 0
    

    # Common function signatures for token contracts ERC-20 and ERC-721(NFT)
    function_signatures = {
        'ERC20': [
            '0x18160ddd',  # totalSupply()
            '0x70a08231',  # balanceOf(address)
            '0xa9059cbb',  # transfer(address,uint256)
            '0x23b872dd',  # transferFrom(address,address,uint256)
            '0x095ea7b3',  # approve(address,uint256)
            '0xdd62ed3e',  # allowance(address,address)
        ],
        'ERC721': [
            '0x70a08231',  # balanceOf(address)
            '0x6352211e',  # ownerOf(uint256)
            '0x42842e0e',  # safeTransferFrom(address,address,uint256)
            '0x23b872dd',  # transferFrom(address,address,uint256)
            '0x095ea7b3',  # approve(address,uint256)
            '0xa22cb465',  # setApprovalForAll(address,bool)
            '0x081812fc',  # getApproved(uint256)
            '0xe985e9c5',  # isApprovedForAll(address,address)
        ]
    }
    # Minimal ABI for ERC20 tokens
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]
    ERC721_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
    ]   
    def is_erc721_token(contract_address):
        contract = w3.eth.contract(address=contract_address, abi=ERC721_ABI)
        try:
            # Try to call the ownerOf function with a random token ID
            contract.functions.ownerOf(1).call()
            return True
        except ContractLogicError:
            # If the token ID doesn't exist, it might still be an ERC721 token
            try:
                # Check if balanceOf function exists
                contract.functions.balanceOf(contract_address).call()
                return True
            except:
                return False
        except Exception:
            return False
    
    def is_erc20_token(contract):
        try:
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            print(f"Token Name: {name}")
            print(f"Token Symbol: {symbol}")
            print(f"Token Decimals: {decimals}")
            return True
        except ContractLogicError as e:
            print(f"Contract does not implement ERC20 interface: {str(e)}")
            return False
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return False


    def check_token_type(contract_address):
        if is_erc20_token(contract_address):
            print("ERC721 (NFT)")
            return 1
        elif is_erc721_token(contract_address):
            print("ERC20 fungible token")
            return 1
        else:
            print("Not a token contract")
            return 2

    token_type = check_token_type(address_checksum)
    return token_type
