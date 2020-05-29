# refactored version of Sugarscape model. More modular, extensible, and maybe slightly more efficient than previous versions.
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

    def __init__(self):
        self.id = Agent.num
        Agent.num += 1

        # self.tsync = 0.0 # last time at which the agent's last state update occurred

        self.sugar = 0
        self.vision = next(agentVisionDist)
        self.metab = next(agentMetabDist)

        self.site = None

    def getNeighborhood(self):
        sitesInSight = []
        X, Y = self.site.position()

        for i in range(self.vision + 1):
            sitesInSight.append(Site.sugScape[(X+i) % Site.sugScape.length][Y])
            sitesInSight.append(Site.sugScape[(X-i) % Site.sugScape.length][Y])
            sitesInSight.append(Site.sugScape[X][(Y+i) % Site.sugScape.length])
            sitesInSight.append(Site.sugScape[X][(Y-i) % Site.sugScape.length])

        random.shuffle(sitesInSight)
        return sitesInSight


    def move(self):
        sitesInSight = self.getNeighborhood()
        emptySitesInSight = list(filter(lambda site : True if site.empty() else False, sitesInSight))

        x, y = self.site.position()
        Site.sugScape[x][y].agent = None
        Site.sugScape.emptySites.add(self.site)

        maxSugSite = max(emptySitesInSight, default= Site.sugScape[x][y], key= lambda s : s.sugar)

        maxSugSite.putAgent(self)
        # self.sugar -= self.metab should this be included?
        print(self.id, " moved.")

        # self.eventTimes[EType.MOVE.value] += self.getInterMovement()
        # self.setNextEvent()


    def update(self):
        self.sugar += (Site.sugScape.time - self.site.tsync)*(self.site.regen - self.metab)

class Site:
    sugScape = None # sugarscape the sites belong to

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cap = next(siteCapDist)
        self.sugar = next(siteSugarDist)

        while self.sugar > self.cap:
            self.sugar = next(siteSugarDist)

        self.regen = next(siteRegenDist)
        self.agent = None
        self.tsync = 0.0

    def position(self):
        return self.x, self.y

    def empty(self):
        return self.agent == None

    # not needed any longer
    # def regen(self):
    #     self.sugar = self.cap if self.sugar + self.regen >= self.cap else self.sugar + self.regen

    def putAgent(self, agent):
        self.agent = agent
        agent.site = self
        agent.sugar += self.sugar
        self.sugar = 0

    def update(self):
        tDiff = Site.sugScape.time - self.tsync

        if tDiff > 0:
            if self.empty():    self.sugar = self.cap if self.sugar + tDiff*self.regen >= self.cap else self.sugar + tDiff*self.regen
            else:   self.agent.update()

        self.tsync = Site.sugScape.time

class Sugarscape:

    def __init__(self, length= 10):
        self.time = 0.0
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
                    self.emptySites.discard(site)

    def update(self):
        for row in self.grid:
            for site in row:
                site.update()

    # print could be improved in the future, to include a lambda function to determine what's printed
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

random.seed(8675309)

agentDensity = 0.6

agentVisionDist = randseq( random.randint )(1,3)
agentMetabDist = randseq( random.expovariate )(2)
intermovement = randseq( random.expovariate )(2)


siteCapDist = randseq( random.uniform )(0.0, 100.0)
siteSugarDist = randseq( random.uniform )(0.0, 100.0)
siteRegenDist = randseq( random.random )()













################################# MAIN #########################################
agents = []

    # a = Agent()
    # print(a.id, " ", a.sugar, " ", a.vision, " ", a.metab, " ", a.tsync)
s = Sugarscape(10)
s.populate()

Site.sugScape = s


# s[0][0].putAgent(Agent())
#     # print(len(agents))
#
# s.print()
#
# a = s[0][0].agent
#
# print("\n \n \n")
#
# while Site.sugScape.time < 10.0:
#     a.move()
#     for row in Site.sugScape:
#         for site in row:
#             site.update()
#
#     Site.sugScape.time += 2
#
# s.print()
