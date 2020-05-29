# refactored version of Sugarscape model. This one is designed for extensibility, modularity, and readability
import random

# function returns a generator of random values drawn from provided distribution
def randseq(distro):
    def seq(*args):
        val = distro(*args)
        while True:
            yield val
            val = distro(*args)
    return seq

class Agent:
    # static variables
    num = 0
    sugScape = None # sugarscape the agents are on

    def __init__(self):
        self.id = Agent.num
        Agent.num += 1

        self.tsync = 0.0 # last time at which the agent's last state update occurred

        self.sugar = 0
        self.vision = next(agentVisionDist)
        self.metab = next(agentMetabDist)

        self.site = None

    def getNeighborhood(self):
        sitesInSight = []
        X, Y = self.site.position()

        for i in range(self.vision + 1):
            sitesInSight.append(Agent.sugScape[(X+i) % Agent.sugScape.length][Y])
            sitesInSight.append(Agent.sugScape[(X-i) % Agent.sugScape.length][Y])
            sitesInSight.append(Agent.sugScape[X][(Y+i) % Agent.sugScape.length])
            sitesInSight.append(Agent.sugScape[X][(Y-i) % Agent.sugScape.length])

        random.shuffle(sitesInSight)
        return sitesInSight


class Site:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cap = next(siteCapDist)
        self.sugar = next(siteCapDist)

        while self.sugar > self.cap:
            self.sugar = next(siteCapDist)

        self.regen = next(siteRegenDist)
        self.agent = None

    def position(self):
        return self.x, self.y

    def empty(self):
        return self.agent == None

    def regen(self):
        self.sugar = self.cap if self.sugar + self.regen >= self.cap else self.sugar + self.regen

    def putAgent(self, agent):
        self.agent = agent
        agent.site = self
        agent.sugar += self.sugar
        self.sugar = 0

class Sugarscape:
    def __init__(self, length):
        self.length = length
        self.grid = [[Site(i,j) for j in range(length)] for i in range(length)]
        self.emptySites = set([site for row in self.grid for site in row])

    def __getitem__(self, index):
        return self.grid[index]

    def populate(self):
        for row in self.grid:
            for site in row:
                site.x = (self.grid).index(row)
                site.y = row.index(site)

                if random.random() <= agentDensity:
                    a = Agent()
                    site.putAgent(a)
                    agents.append(a)

    # print could be improved in the future
    def print(self):
        for row in self.grid:
            toPrint = []
            for site in row:
                if site.agent == None:
                    toPrint.append(" ")
                else:
                    toPrint.append(site.agent.id)
            print(toPrint)
            print("\n")

############################ FIDDLING SECTION ##################################

agentDensity = 0.50

agentVisionDist = randseq( random.randint )(1,3)
agentMetabDist = randseq( random.expovariate )(2)

siteCapDist = randseq( random.randrange )(0.0, 100.0)
siteRegenDist = randseq( random.random )()

################################# MAIN #########################################
agents = []

# # a = Agent()
# # print(a.id, " ", a.sugar, " ", a.vision, " ", a.metab, " ", a.tsync)
# s = Sugarscape(10)
# s.populate()
#
# Agent.sugScape = s
#
# # print(len(agents))
# print(s[0][0].agent.getNeighborhood())
