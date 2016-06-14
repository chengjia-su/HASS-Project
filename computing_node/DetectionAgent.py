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
    
    def check_services(self, test=False):
        import libvirt
        import subprocess
        message = ""
        #check libvirt
        conn = libvirt.open(self.libvirt_uri)
        if conn == None:
            message = "libvirt;"
            subprocess(['service', 'libvirt-bin', 'restart'])
            if test==True:
                print "Test libvirt fail."
        else:
            if test==True:
                print "Test libvirt success."
        conn.close()
        #check nova-compute
        output = subprocess.check_output(['ps', '-A'])
        if "nova-compute" not in output:
            message += "nova;"
            subprocess(['service', 'nova-compute', 'restart'])
            if test==True:
                print "Test nova-compute fail."
        else:
            if test==True:
                print "Test nova-compute success."
        #check qemu-kvm    
        output = subprocess.check_output(['service', 'qemu-kvm', 'status'])
        if "start/running" not in output:
            message += "qemukvm;"
            subprocess(['service', 'qemu-kvm', 'restart'])
            if test==True:
                print "Test qemu-kvm fail."
        else:
            if test==True:
                print "Test qemu-kvm success."
                
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
