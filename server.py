import socket
import threading
import json
import os
import sys
import signal
import win32api
import binascii


class TCPServer:
    def __init__(self, host, port, num_threads, quarantine_dir):
        self.host = host
        self.port = port
        self.num_threads = num_threads
        self.quarantine_dir = quarantine_dir
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.shutdown_flag = threading.Event()

        if not os.path.exists(quarantine_dir):
            os.makedirs(quarantine_dir)

    def handle_client(self, client_socket):
        request = client_socket.recv(4096)
        try:
            request = json.loads(request.decode('utf-8'))
            command = list(request.keys())[0]
            params = request[command]

            if command == "CheckLocalFile":
                response = self.check_local_file(params)
            elif command == "QuarantineLocalFile":
                response = self.quarantine_local_file(params)
            else:
                response = {"error": "unknown command"}

            client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            response = {"error": str(e)}
            client_socket.send(json.dumps(response).encode('utf-8'))
        finally:
            client_socket.close()

    def check_local_file(self, params):
        file_path = params.get("file_path")
        signature = params.get("signature")
        # перевод строки в байты
        signature = binascii.unhexlify(signature)
        offsets = []
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
                # ищем первое вхождение в файле
                pos = content.find(signature)
                while pos != -1:
                    # ищем последующие вхождения в файле
                    offsets.append(str(pos)+'-' + hex(pos))
                    pos = content.find(signature, pos + 1)
            return {"offsets": offsets}
        except Exception as e:
            return {"error": str(e)}

    def quarantine_local_file(self, params):
        file_path = params.get("file_path")
        try:
            if os.path.exists(file_path):
                base_name = os.path.basename(file_path)
                quarantine_path = os.path.join(self.quarantine_dir, base_name)
                os.rename(file_path, quarantine_path)
                return {"status": "file quarantined"}
            else:
                return {"error": "file does not exist"}
        except Exception as e:
            return {"error": str(e)}

    def start(self):
        print(f"[!] Starting server on {self.host}:{self.port}")
        while not self.shutdown_flag.is_set():
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"[+] Connection from {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        self.shutdown_flag.set()
        self.server_socket.close()
        print("[!] Server stopped")


def signal_handler(sig, frame):
    print("[!] Server is shutting down...")
    server.stop()
    sys.exit(0)


def console_ctrl_handler(ctrl_type):
            if ctrl_type == 0:
                signal_handler(None, None)
                return True
            return False


# Проверка наличия параметра для запуска - количества потоков в пуле обработки запросов
def check_start_params():
    if(len(sys.argv) < 2):
        print('[-] error: not enough params: specify count of threads...')
        return -1
    elif(len(sys.argv) > 2):
        print('[-] error: too many parameters...')
        return -1
    else:
        return sys.argv[1]


if __name__ == "__main__":
    # пытаемся получить количество потоков
    try:
        num_threads = int(check_start_params())
    except Exception:
        print('[-] error: cannot convert value to integer...')
        sys.exit(-1)
    # если не передан параметр количества потоков, то завершаем работу программы
    if(num_threads <= 0):
        print('[-] error: incorrect value...')
        sys.exit(-1)
    # определение основных переменных для описания TCP-сервера
    host = "127.0.0.1"
    port = 65432
    # папка, в которой находятся файлы карантина
    quarantine_dir = "./quarantine"
    # обработчик закрытия окна
    win32api.SetConsoleCtrlHandler(console_ctrl_handler, True) 
    # инициализация класса TCPServer
    server = TCPServer(host, port, num_threads, quarantine_dir)
    # Запуск сервера
    try:
        server.start()
    except KeyboardInterrupt:
        print("[!] Server is shutting down...")
        server.stop()
        sys.exit(0)
