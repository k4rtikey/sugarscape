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
seed = 8745309
sg = SeedSequence(seed)
random.seed(seed)
streams = [Generator(Philox(s)) for s in sg.spawn(numStreams)]

agentDensity = 0.2

agentVisionDist = randseq( streams[0].integers )(1,3)
agentMetabDist = randseq( streams[1].uniform )(2.0, 3.0)
intermovement = randseq( streams[2].exponential )(1)
interreproduce = randseq( streams[3].exponential )(1)
gestationperiod = randseq( streams[4].uniform )(1.0, 2.0)

siteCapDist = randseq( streams[5].uniform )(0.0, 5.0)
siteSugarDist = randseq( streams[6].uniform )(0.0, 5.0)
siteRegenDist = randseq( streams[7].uniform )(0.0,5.0)

agentDeathLag = randseq( streams[8].uniform )(0.0, 1.0)

tmax = 12.5

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
        self.events = []

        self.history = []
        self.sugarhist = []
        self.times = []
        self.tods = []
        self.log = []
        self.cancelled = []
############# FOR TESTING ONLY ###################
    def pevents(self):
        for e in self.events:
            print(e.func, e.time)

    def pcancelled(self):
        for e in self.cancelled:
            print(e.func, e.time)
##################################################

    def schedule(self, action, timeOffset):
        # if self.id == 93:
        #     pdb.set_trace()

        if action == self.die:
            for e in self.events:
                if e.time >= self.tod()+sim.now:
                    sim.cancel(e)
                    self.cancelled.append(e)

        e = sim.sched(action, offset = timeOffset)
        self.events.append(e)

    def startEvents(self):
        Site.sugScape.update()

        nextMove = next(intermovement)
        nextRep = next(interreproduce)

        self.schedule(self.move, nextMove)
        self.schedule(self.findPartner, nextRep)

        if self.tod()+sim.now != float("inf"):
            self.schedule(self.die, self.tod()+next(agentDeathLag))

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
        self.history.append(self.move)
        print(self.id, "attempting to move at", sim.now)
        #########TESTING###########
        # if self.sugar < 0:
        #     pdb.set_trace()
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

        logEntry = "tod is " + str(self.tod()+ sim.now) + " and time of nextMove is " + str(nextMove+sim.now)

        if self.tod() > nextMove:
            self.schedule(self.move, nextMove)
            logEntry += " chose to move."
        else:
            self.schedule(self.die, self.tod()+next(agentDeathLag))
            logEntry += " chose to die."

        self.log.append(logEntry)


    def die(self):
        self.history.append(self.die)

        Site.sugScape.update()
        X, Y = self.site.position()
        chosenSite = self.site
        Site.sugScape[X][Y].agent = None
        Site.sugScape.emptySites.append(chosenSite)

        if len(Site.sugScape.emptySites) > 0:
            chosenSite = random.choice(Site.sugScape.emptySites)

        chosenSite.initialize(Agent())
        for e in self.events:
            if e.time > sim.now:
                sim.cancel(e)
                self.cancelled.append(e)

        print(self.id, "has died. RIP.")
        del self # this line miiiight cause problems

    def findPartner(self):
        if self.sugar < 0:
            print("negative sugar prblm")
            pdb.set_trace()

        self.history.append(self.findPartner)

        print(self.id, "attempting to find partner.")

        ##########testingonly##########
        falsePartner = None
        ##########################
        if self.partner != None:
            falsePartner = self.partner
            print("already got a partner prblm")
            pdb.set_trace()

        # assert(self.partner == None)

        Site.sugScape.update()
        sitesInSight = self.getNeighborhood()
        # THIS LINE DOESN'T PREVENT BEST AGENT TO BE A NON-GESTATING AGENT. FIX THIS TOO
        filledSitesInSight = list(filter(lambda site : True if not site.empty() else False, sitesInSight))
        availableAgentSites = list(filter(lambda site : True if (site.agent.partner == None and site.agent != self) else False, filledSitesInSight))

        for s in availableAgentSites:
            assert(s.agent.gestating == False and s.agent.partner == None)

        bestAgent = None
        term = 0
        if len(availableAgentSites) > 0 and not self.gestating:
            gestPeriod = next(gestationperiod)
            # check if self will survive the term
            if self.tod() > gestPeriod:

                healthyAgentsSites = list(filter(lambda site: True if site.agent.tod() > gestPeriod else False, availableAgentSites))
                bestAgentSite = max(healthyAgentsSites, default = None, key= lambda site : site.agent.sugar)

                if bestAgentSite != None:   bestAgent = bestAgentSite.agent

                if bestAgent != None:
                    term = gestPeriod
                    self.partner = bestAgent
                    self.partner.partner = self
                    self.gestating = True
                    self.partner.gestating = True
                    self.schedule(self.giveBirth, term)
                    # pdb.set_trace()
                    for e in self.events:
                        if e.time > sim.now and e.time <= sim.now + term and e.func != self.giveBirth and e.func != self.partner.giveBirth:
                            if e.time - sim.now < self.tod():
                                sim.resched(e, until = e.time + term)
                            else:
                                if e.func != self.die:
                                    sim.cancel(e)
                                self.schedule(self.die, self.tod())

                    for e in self.partner.events:
                        if e.time > sim.now and e.time <= sim.now+ term and (e.func != self.giveBirth and e.func != self.partner.giveBirth):
                            if e.time - sim.now < self.tod():
                                sim.resched(e, until = e.time + term)
                            else:
                                sim.cancel(e)
                                self.schedule(self.die, self.tod())


        print(bestAgent.id, "is best agent for", self.id) if bestAgent != None else print("No partner in sight for", self.id)


        nextRep = next(interreproduce)

        logEntry = "tod is " + str(self.tod()+ sim.now) + " and nextRep + term is " + str(nextRep+term+sim.now)

        # if self.sugar < 0.05:
        #     pdb.set_trace()

        if self.tod() > nextRep+term:
            self.schedule(self.findPartner, nextRep+term)
            logEntry += " chose to find partner"
        else:
            self.schedule(self.die, self.tod()+next(agentDeathLag))
            logEntry += " chose to die."

        self.log.append(logEntry)

    def giveBirth(self):
        Site.sugScape.update()
        self.history.append(self.giveBirth)
        print("Parent", self.id, "is giving birth with partner", self.partner.id)
        sitesInSight = self.getNeighborhood()
        sitesInSight.extend(self.partner.getNeighborhood())

        bestSite = max([site for site in sitesInSight if site.empty()], default = None, key = lambda site : site.sugar)

        if bestSite != None:
            bestSite.initialize(Agent())
            bestSite.agent.sugar = (self.sugar+self.partner.sugar)/2
            self.sugar /= 2
            self.partner.sugar /= 2
            print("Parents", self.id, self.partner.id, "welcome new baby new baby agent at", *bestSite.position(), ".")
            # check if death has been preponed because of sugar split for self and partner
            if self.tod() != float("inf"):
                self.schedule(self.die, self.tod()+next(agentDeathLag))

            if self.partner.tod() != float("inf"):
                self.partner.schedule(self.partner.die, self.partner.tod()+next(agentDeathLag))

        else:
            print("Oops, no new baby born for parents", self.id, self.partner.id, ":(")
            if self.tod() != float("inf"):
                self.schedule(self.die, self.tod()+next(agentDeathLag))

            if self.partner.tod() != float("inf"):
                self.partner.schedule(self.partner.die, self.partner.tod()+next(agentDeathLag))

        # print("checking out what happens during birth")
        # pdb.set_trace()


        self.partner.gestating = False
        self.partner.partner = None # THIS LINE IS PROBABLY CAUSING PROBLEMS
        self.gestating = False
        self.partner = None


    def update(self):
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
