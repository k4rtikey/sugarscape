import simulus
import random
from numpy.random import Philox, Generator, SeedSequence
import pdb

def randseq(distro):
    def seq(*args):
        val = distro(*args)
        while True:
            yield val
            val = distro(*args)
    return seq

numStreams = 9
seed = 8675309
sg = SeedSequence(seed)
streams = [Generator(Philox(s)) for s in sg.spawn(numStreams)]

agentDensity = 0.9

agentVisionDist = randseq( streams[0].integers )(1,2)
agentMetabDist = randseq( streams[1].uniform )(2.0, 8.0)
intermovement = randseq( streams[2].exponential )(1)
interreproduce = randseq( streams[3].exponential )(2)
gestationperiod = randseq( streams[4].uniform )(1.0, 2.0)

siteCapDist = randseq( streams[5].uniform )(0.0, 5.0)
siteSugarDist = randseq( streams[6].uniform )(0.0, 5.0)
siteRegenDist = randseq( streams[7].uniform )(0.0,5.0)

agentDeathLag = randseq( streams[8].uniform )(0.0, 1.0)

tmax = 5

# ============================================================================ #

sim = simulus.simulator()

class Agent:
    # static variables
    num = 0

    def __init__(self):
        self.id = Agent.num
        Agent.num += 1

        self.sugar = 0
        self.vision = next(agentVisionDist)
        self.metab = next(agentMetabDist)

        self.site = None
        self.partner = None
        self.gestating = False
        self.events = {}

        self.history = {}
        self.sugarhist = []
        self.times = []
        self.tods = []
        self.dead = False


    def schedule(self, action, timeOffset):
        e = sim.sched(action, offset = timeOffset)
        self.events[e] = sim.now+timeOffset

        if action == self.die:
            for e in self.events:
                sim.cancel(e)

    def startEvents(self):
        nextMove = next(intermovement)
        nextRep = next(interreproduce)

        self.schedule(self.move, nextMove)
        self.schedule(self.findPartner, nextRep)

        tod = self.tod()+sim.now
        for e in list(self.events.keys()):
            if e.time > tod:
                sim.cancel(e)
                del self.events[e]

        if len(self.events) == 0:
            sim.sched(self.die, offset = tod-sim.now+next(agentDeathLag))

    # returns time from now at which agent will die.
    def tod(self):
        if self.site.regen > self.metab:    return float("inf")
        else:   return -self.sugar/(self.site.regen - self.metab)

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
        self.history[sim.now] = self.move
        print(self.id, "attempting to move at", sim.now)
        #########TESTING###########
        if self.sugar < 0:
            pdb.set_trace()
####################
        Site.sugScape.update()
        assert(self.site != None)
        sitesInSight = self.getNeighborhood()

        x, y = self.site.position()
        self.site.agent = None
        Site.sugScape.emptySites.append(self.site)

        assert(Site.sugScape[x][y].empty())

        emptySitesInSight = list(filter(lambda site : True if site.empty() else False, sitesInSight))



        maxSugSite = max(emptySitesInSight, default= Site.sugScape[x][y], key= lambda s : s.sugar)

        maxSugSite.putAgent(self)

        print(self.id, "moved.")

        nextMove = next(intermovement)

        print(self.id, "is supposed to die at t =", self.tod())

        if self.tod() > nextMove:
            self.schedule(self.move, nextMove)

        else:
            self.schedule(self.die, self.tod()+next(agentDeathLag))


    def die(self):
        print(self.id, "died at", sim.now)

        self.history[sim.now] = self.die

        Site.sugScape.update()
        X, Y = self.site.position()
        chosenSite = self.site
        Site.sugScape[X][Y].agent = None
        Site.sugScape.emptySites.append(chosenSite)

        if len(Site.sugScape.emptySites) > 0:
            chosenSite = random.choice(Site.sugScape.emptySites)

        chosenSite.initialize(Agent())

        for e in self.events.keys():
            sim.cancel(e)

        self.dead = True
        print(self.id, "has died. RIP.")

    def findPartner(self):
        if self.sugar < 0:
            pdb.set_trace()

        self.history[sim.now] = self.findPartner
        print(self.id, "tried finding partner.")
        nextRep = next(interreproduce)

        if self.tod() > nextRep:
            self.schedule(self.move, nextRep)

        else:
            self.schedule(self.die, self.tod()+next(agentDeathLag))

    def update(self):
        if sim.now == 0:
            print("t = 0.0 update just occured for", self.id)

        self.sugar += (sim.now - self.site.tsync)*(self.site.regen - self.metab)
        self.sugarhist.append(self.sugar)
        self.times.append(sim.now)
        self.tods.append(self.tod()+sim.now)

class Site:
    sugScape = None # sugarscape the sites belong to

    def __init__(self, x : int, y : int):
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

    def initialize(self, agent):
        self.putAgent(agent)
        agent.startEvents()

    def putAgent(self, agent):
        self.agent = agent
        agent.site = self
        agent.sugar += self.sugar
        self.sugar = 0
        Site.sugScape.emptySites.remove(self)
        self.update()

    def update(self):
        tDiff = sim.now - self.tsync

        if tDiff >= 0:
            if self.empty():    self.sugar = self.cap if self.sugar + tDiff*self.regen >= self.cap else self.sugar + tDiff*self.regen
            else:   self.agent.update()

        self.tsync = sim.now


class Sugarscape:

    def __init__(self, length= 10):
        self.time = 0.0
        self.length = length
        self.grid = [[Site(i,j) for j in range(length)] for i in range(length)]
        self.emptySites = [site for row in self.grid for site in row]

    def __getitem__(self, index):
        return self.grid[index]

    def populate(self):
        for row in self.grid:
            for site in row:
                site.x = (self.grid).index(row)
                site.y = row.index(site)

                if random.random() <= agentDensity:
                    a = Agent()
                    site.initialize(a)



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
                    toPrint.append(".")
                else:
                    toPrint.append(site.agent.id)
            print(*tuple(toPrint))
            print("\n")

# ============================================================================ #

Site.sugScape = Sugarscape(10)
Site.sugScape.populate()

sim.run(tmax)
print("num agents generated", Agent.num +1)

print("terminated at", sim.now)
