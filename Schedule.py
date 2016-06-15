
class Schedule():
        
    def default(self, hostList, failednode = ""):
        import random
        if failednode != "":
            hostList.remove(failednode)
        host = random.choice(hostList)
        return host
        
def main():

    test = Schedule()
    host_list = ["host1", "host2"]
    print test.default(host_list, "host2")

if __name__ == "__main__":
    main()