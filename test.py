import etherenode
import helper

config = helper.check_config_file()
port = config["port"]
protocol = config["protocol"]
host = config["host"]
input_folder_path = config["input_folder_path"]
input_contract_file_name = config["input_contract_file_name"]
node_url = protocol + host + ":" + str(port)

# test ethernode
def test_check_addresses_for_address_type():
    # Test case 1: Valid Ethereum addresses
    addresses = ["0x9758da9b4d001ed2d0df46d25069edf53750767a","0x176CA8f5676D5B916a5f65926124218C27a4c47A"]
    assert etherenode.check_addresses_for_address_type(addresses, node_url) == {'0x9758da9b4d001ed2d0df46d25069edf53750767a': 'CA', '0x176CA8f5676D5B916a5f65926124218C27a4c47A': 'EOA'}
    """
    # Test case 2: Invalid Ethereum addresses
    addresses = ['0x1234567890abcdef', '0xabcdef1234567890', '0xinvalidaddress']
    assert etherenode.check_addresses_for_address_type(addresses, node_url) == False
    """
    # Test case 3: Empty list of addresses
    addresses = []
    assert etherenode.check_addresses_for_address_type(addresses) == False

    # Test case 4: Single valid Ethereum address
    addresses = ['0x1234567890abcdef']
    assert etherenode.check_addresses_for_address_type(addresses) == True

    print("All test cases passed!")

# Run the test function
test_check_addresses_for_address_type()