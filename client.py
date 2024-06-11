import socket
import json
import sys

CHECK_FILE = 0
QUARANTINE_FILE = 1
ERROR = 2

def send_request(host, port, command, params):
    flag_for_check = ERROR
    request = {command: params}
    try:
        file_path = request['CheckLocalFile']['file_path']
        signature = request['CheckLocalFile']['signature']
        flag_for_check = CHECK_FILE
    except KeyError:
        pass
    try:
        file_path = request['QuarantineLocalFile']['file_path']
        flag_for_check = QUARANTINE_FILE
    except KeyError:
        pass

    print('[+] Request:')
    if(flag_for_check == CHECK_FILE):
        print(f'\tFile path: {file_path}')
        print(f'\tSignature: {signature}')
    elif(flag_for_check == QUARANTINE_FILE):
        print(f'\tFile path: {file_path}')
    else:
        print('Errors occured...exiting')
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(json.dumps(request).encode('utf-8'))
        # получаем ответ от сервера
        response = sock.recv(4096)
        response = response.decode('utf-8')
        # преобразуем в json
        response = json.loads(response)
        print('[+] Response')
        if(flag_for_check == CHECK_FILE):
            # извлекаем информацию о смещениях
            offsets_array = response["offsets"]
            # общее количество смещений
            offsets_count = len(offsets_array)
            offset_number = 0
            if(offsets_count <= 0):
                print(f'\tSignature not found... exiting')
                return
            print(f'\tOffsets list (total {offsets_count}):')
            print('\t№\tOffset(int)\tOffset(hex)')
            for offset in offsets_array:
                offset_number += 1
                # получаем hex и int представление смещений
                offset_int, offset_hex = offset.split('-')
                print(f'\t[{offset_number}] \t{offset_int} \t\t{offset_hex}')
        elif(flag_for_check == QUARANTINE_FILE):
            try:
                quarantine_status = response['status']
            except KeyError:
                quarantine_status = "errors occured while processing request...exiting"
            print(f'\tStatus: {quarantine_status}')
        else:
            print('\terrors occured while processing request...exiting')


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: client.py <command> <value1>=<param1> <value2>=<param2> ...")
        sys.exit(1)

    host = "127.0.0.1"
    port = 65432
    command = sys.argv[1]
    params = {}
    for param in sys.argv[2:]:
        key, value = param.split('=')
        params[key] = value

    send_request(host, port, command, params)
