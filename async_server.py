#!/usr/bin/python
import asyncore
import socket
import Queue
import sys

Q_fromSwitch= Queue.Queue()
Q_fromController= Queue.Queue()

class proxyListener(asyncore.dispatcher):
    def __init__(self,host,port,Q_fromSwitch,Q_fromController):
        asyncore.dispatcher.__init__(self)
        self.Q_sw=Q_fromSwitch
        self.Q_ctrl=Q_fromController
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.bind((host,port))
            self.address = self.socket.getsockname()
            self.listen(1)
            print('binding to %s', self.address)
        except:
            print ("proxy server bind unsuccesful")
            sys.exit(1)

    def handle_accept(self):
        handler=self.accept()
        print "accepted connection from ",handler
        proxyHandler(handler[0],self.Q_sw,self.Q_ctrl)
        self.handle_close()

    def handle_close(self):
        self.close()
        return

class proxyHandler(asyncore.dispatcher):
    def __init__(self,sock,Q_fromSwitch,Q_fromController):
        asyncore.dispatcher.__init__(self, sock=sock)
        return

    def writable(self):
        if (not Q_fromController.empty()):
            return True
        else:
            return False

    def readable(self):
        return True

    def handle_write(self):
        print ("in server write , trying to write")
        try:
            buf=Q_fromController.get(False)
            self.send(buf)
            print repr(buf[0])
        except:
            print("Nothing to read from controller buffer")

    def handle_read(self):
        recvd_content = self.recv(4096)
        print ("in server read , trying to read")
        if (len(recvd_content) > 0):
            print repr(recvd_content[0])
            Q_fromSwitch.put(recvd_content)

    def handle_close(self):
        self.close()

class proxyClient(asyncore.dispatcher):
    def __init__(self,host,port,Q_fromSwitch,Q_fromController):
        asyncore.dispatcher.__init__(self)
        self.recv_buffer=""
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.connect((host, port))
        except:
            print("connection to controller not succesful")
            sys.exit(1)


    def writable(self):
        if (not Q_fromSwitch.empty()):
            return True
        else:
            return False

    def readable(self):
        return True

    def handle_connect(self):
        print("Connected to Controller")

    def handle_write(self):
        print ("in client write , trying to write")
        try:
            buf= Q_fromSwitch.get(False)
            self.send(buf)
            print repr(buf[0])
        except:
            print("nothing to read from switch buffer")


    def handle_read(self):
        recvd_content = self.recv(4096)
        print ("in client read , trying to read")
        if (len(recvd_content) > 0):
            print repr(recvd_content[0])
            Q_fromController.put(recvd_content)

    def handle_close(self):
        pass


class Proxy():
    def __init__(self):
        Q_fromSwitch = Queue.Queue()
        Q_fromController = Queue.Queue()
        self.server = proxyListener('', 6643,Q_fromSwitch,Q_fromController)
        self.client=proxyClient('10.244.36.116',6633,Q_fromSwitch,Q_fromController)


if __name__=='__main__':
    proxy=Proxy()
    asyncore.loop()


