# PyTCPSignatureChecker
 TCP server and client for checking file's signature

## How to use
* pip install -r requirements.txt
* py server.py <num_of_threads>
* py client.py CheckLocalFile file_path="path to file" signature="signature on hex"
* py client.py QuarantineLocalFile file_path="path to file"
  
## Examples:
py client.py CheckLocalFile file_path="test555.docx" signature="504B03" \
py client.py QuarantineLocalFile file_path="test666.txt"

## Notes:
* default quarantine directory - "./quarantine"
* default port - 65432