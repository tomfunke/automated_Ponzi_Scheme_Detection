# Ethereum Smart Contract Ponzi Scheme Detector
This project uses process mining techniques to check if the ethereum blockchain application data is a Ponzi scheme

## prerequisites
Ethereum Archive Node with a Geth-based client
tabular transaction trace data from the extractor


## Installation
1. install Graphviz using package managers like Homebrew. Its needed for visualizing complex relationships 
2. Clone the repository:
```console
git clone [this project]
```

3. install requirements.txt:
```console
pip install -r requirements.txt
```


## Configuration
### Ethereum Node
port
protocol
host

### Input files
The output from the extractor is the input for the script.

1. Path to log folder as input_folder_path
2. Name of the contract as input_contract_file_name
