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
        self.libvirt_uri = "qemu:///system"
        
    def handle_read(self):
        data, addr = self.recvfrom(2048)
        print 'request from: ', addr
        check_result = self.check_services()
        if data == "polling request":
            if check_result == "":
                self.sendto("OK", addr)
            else:
                check_result = "error:" + check_result
                self.sendto(check_result, addr)
    
    def check_services(self):
        import libvirt
        import subprocess
        message = ""
        #check libvirt
        conn = libvirt.open(self.libvirt_uri)
        if conn == None:
            message = "libvirt;"
        conn.close()
        #check nova-compute
        output = subprocess.check_output(['ps', '-A'])
        if "nova-compute" not in output:
            message += "nova;"
        #check qemu-kvm    
        output = subprocess.check_output(['service', 'qemu-kvm', 'status'])
        if "start/running" not in output:
            message += "qemukvm;"
        
        return message
        
        
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
