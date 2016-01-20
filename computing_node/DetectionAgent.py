import socket
import asyncore
import socket
import sys
import ConfigParser

class DetectionAgent():
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read('hass_node.conf')
        self.port = int(config.get("polling","listen_port"))
        
    def startListen(self):
        print "create listen thread"
        server = PollingHandler('', self.port)
        asyncore.loop()
    

class PollingHandler(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_reuse_addr()
        self.bind((host, port))
        
    def handle_read(self):
        data, addr = self.recvfrom(2048)
        print 'request from: ', addr
        if data == "polling request":
            self.sendto("ACK", addr)
            
def main():
    
    test = DetectionAgent()
    test.startListen()
    try:
        while True:
         pass
    except:
        sys.exit(1)
    
if __name__ == "__main__":
    main()
