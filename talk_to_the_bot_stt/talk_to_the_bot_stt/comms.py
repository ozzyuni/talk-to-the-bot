#!/usr/bin/env python
import select
import socket
class Server:
    """ A simple TCP server application for receiving message blocks of a specified length. 
        Includes verification that the entire message was received.
    """

    def __init__(self, port: int, logging=False, logger_function=None):
        """Set connection parameters and bind a port for listening
            Args:
                port | number of the TCP port the server will listen on
                logging | include printouts for quick debugging
        """
        self.hostname = socket.gethostbyname('0.0.0.0')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.guest_socket = None
        self.logging = logging

        if logger_function is not None:
            self.logger = logger_function
        else:
            self.logger = print

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.hostname, port))
        self.socket.listen(5)
    
    def receive_tcp(self, msg_len, timeout=False, timeout_in_seconds=3.0):
        success = True
        data = b'None'

        if self.logging:
            self.logger("MSG_LEN: " + str(msg_len))

        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            chunk = self.guest_socket.recv(min(msg_len - bytes_recd, 2048))
            if chunk == b'':
                if self.logging:
                    self.logger("Socket connection broken")
                success = False
                break
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        
        if success:
            data = b''.join(chunks)

        if self.logging:
            self.logger("MSG: " + str(data))

        return data, success

    def respond(self, data: bytes):
        success = False

        if self.send_tcp(len(data).to_bytes(4096, byteorder='little'), 4096):
            success = self.send_tcp(data, len(data))

        self.guest_socket.close()

        return success


    def send_tcp(self, msg, msg_len):
        success = True

        totalsent = 0
        while totalsent < msg_len:
            sent = self.guest_socket.send(msg[totalsent:])
            if sent == 0:
                if self.logging:
                    self.logger("Socket connection broken")
                success = False
                break
            totalsent = totalsent + sent

        return success


    def receive(self, timeout=False, timeout_in_seconds=3.0):
        """Receive data from the bound port
            Args:
                timeout | if set, the server will stop listening after a specified time
                timeout_in_seconds=3.0 | sets the number of seconds the server will wait before timeout
            Returns:
                data | the content of the message (bytes)
                success | True if verification was successful, False otherwise
        """
        success = True
        data = b'None'

        if timeout:
            self.socket.settimeout(timeout_in_seconds)

        try:
            (self.guest_socket, addr) = self.socket.accept()
        except socket.timeout:
            if self.logging:
                self.logger("Socket timeout")
            success = False
            return data, success

        msg_len_data, success = self.receive_tcp(4096, timeout, timeout_in_seconds)
        
        if success:
            data, success = self.receive_tcp(int.from_bytes(msg_len_data, 'little'), timeout, timeout_in_seconds)

        return data, success

class Client:
    """ A simple TCP client application for sending message blocks of a specified length """
    def __init__(self, ip: str, port: int, timeout=False, timeout_in_seconds=3.0, logging=False, logger_function=None):
        """Set connection parameters
            Args:
                ip | ip address of the server the client should connect to
                port | number of the TCP port the server will listen on
                block_size=512 | size of the message block to be sent (in bytes), make sure this is long enough
        """

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.logging = logging

        if logger_function is not None:
            self.logger = logger_function
        else:
            self.logger = print
    
    def send(self, data: bytes, timeout=False, timeout_in_seconds=3.0):

        success = False
        resp = b'None'

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if timeout:
            self.socket.settimeout(timeout_in_seconds)

        try:
            self.socket.connect((self.ip, self.port))
        except ConnectionRefusedError:
            if self.logging:
                self.logger("Connection refused")
            return resp, success

        if self.send_tcp(len(data).to_bytes(4096, byteorder='little'), 4096):
            if(self.send_tcp(data, len(data))):
                msg_len_data, success = self.receive_tcp(4096, timeout, timeout_in_seconds)

                if success:
                    resp, success = self.receive_tcp(int.from_bytes(msg_len_data, 'little'), timeout, timeout_in_seconds)

        self.socket.close()


        return resp, success
    
    def send_tcp(self, msg, msg_len):
        success = True

        if self.logging:
            self.logger("MSG_LEN: " + str(msg_len))
            self.logger("MSG: " + str(msg))

        totalsent = 0
        while totalsent < msg_len:
            sent = self.socket.send(msg[totalsent:])
            if sent == 0:
                if self.logging:
                    self.logger("socket connection broken")
                success = False
                break
            totalsent = totalsent + sent

        return success

    def receive_tcp(self, msg_len, timeout=False, timeout_in_seconds=3.0):
        success = True
        data = b'None'

        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            chunk = self.socket.recv(min(msg_len - bytes_recd, 2048))
            if chunk == b'':
                if self.logging:
                    self.logger("Socket connection broken")
                success = False
                break
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        
        if success:
            data = b''.join(chunks)

        return data, success