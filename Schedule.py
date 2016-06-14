
class Schedule():
        
    def default(self, hostList):
        import random
        host = random.choice(hostList)
        return host
        
def main():

    test = Schedule()
    host_list = ["host1", "host2"]
    print test.default(host_list)

if __name__ == "__main__":
    main()