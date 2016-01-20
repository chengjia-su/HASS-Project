
class Schedule():
        
    def default(self, hostList):
        import random
        host = random.choice(hostList)
        return host