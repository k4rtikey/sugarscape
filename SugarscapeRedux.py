# refactored version of Sugarscape model. More modular, extensible, and maybe slightly more efficient than previous versions.
# future improvements: use a tuple unpacking approach instead of multiple returns approach with position() function

import random
import bisect
import functools

# function returns a generator of random values drawn from provided distribution
def randseq(distro):
    def seq(*args):
        val = distro(*args)
        while True:
            yield val
            val = distro(*args)
    return seq

calendar = []

@functools.total_ordering
class Event:
    def __init__(self, action, time, params):
        self.action = action
        self.time = time
        self.params = params

# to use insort operation we have to overload < operator
    def __lt__(self, other):
        return self.time < other.time


class Agent:
    # static variables
    num = 0

    def __init__(self):
        self.id = Agent.num
        Agent.num += 1

        self.actions = {self.move : next(intermovement), self.die : float("inf"), self.findPartner : next(interreproduce), self.giveBirth : float("inf")}

        # self.tsync = 0.0 # last time at which the agent's last state update occurred

        self.sugar = 0
        self.vision = next(agentVisionDist)
        self.metab = next(agentMetabDist)

        self.site = None
        self.partner = None
        self.gestating = False

# more general approach: start with min time next action
# find cancellation conditions with that action that are true, and choose one with min time
# check cancel conditions on those, until there are no cancel conditions for it that are true.
# that is the next event.

    def setNextEvent(self):
        nextAction = min(self.actions, key= lambda action : self.actions[action])
        params = ()

        if (self.site.regen < self.metab) and ((-self.sugar/(self.site.regen-self.metab)) <= self.actions[nextAction]):
            nextAction = self.die
            self.actions[self.die] = -self.sugar/(self.site.regen-self.metab)

        if nextAction != self.die and self.gestating:
            nextAction = self.giveBirth

        bisect.insort(calendar, Event(nextAction, self.actions[nextAction], params))



        # if nextAction == self.move:
        #     X, Y = self.site.position()
        #     if (Site.sugScape[X][Y].regen < self.metab) and ((-self.sugar/(Site.sugScape[X][Y].regen-self.metab)) <= self.actions[self.move]):
        #         nextAction = self.die
        #
        #     if self.gestating:  nextAction = self.giveBirth
        #
        # if nextAction == self.giveBirth:




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

        self.actions[self.move] += next(intermovement)
        # self.eventTimes[EType.MOVE.value] += self.getInterMovement()
        self.setNextEvent()

    def die(self):
        X, Y = self.site.position()
        chosenSite = random.choice(list(Site.sugScape.emptySites))
        chosenSite.putAgent(Agent())
        print(self.id, " has died. RIP")
        Site.sugScape[X][Y].agent = None

    def findPartner(self):
        sitesInSight = self.getNeighborhood()
        bestAgent = max([site.agent for site in sitesInSight if site.agent != self and not site.empty()], default = None, key= lambda agent : agent.sugar)
        if bestAgent != None:
            self.partner = bestAgent
            bestAgent.partner = self
            self.gestating = True
            bestAgent.gestating = True

        print(bestAgent.id, "is best agent.") if bestAgent != None else print("No agent in sight for romeo.")
        self.actions[self.giveBirth] += next(gestationperiod)
        self.actions[self.findPartner] += next(interreproduce)
        self.setNextEvent()

    def giveBirth(self):
        sitesInSight = set(self.getNeighborhood()) | set(self.partner.getNeighborhood()) # | signifies the union operator
        bestSite = max([site for site in sitesInSight if site.empty()], default = None, key = lambda site : site.sugar)

        if bestSite != None:
            bestSite.putAgent(Agent())
            bestSite.agent.sugar = (self.sugar+self.partner.sugar)/2
            self.sugar /= 2
            self.partner.sugar /= 2
            print("Welcome new baby agent at", *bestSite.position(), ".")

        else:   print("Oops, no new baby born. :(")

        self.partner.gestating = False
        self.partner.partner = None
        self.gestating = None
        self.partner = None
        self.actions[self.giveBirth] = float("inf")
        self.setNextEvent()

    def update(self):
        self.sugar += (Site.sugScape.time - self.site.tsync)*(self.site.regen - self.metab)

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
                    # agents.append(a)
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

random.seed(8657309)

agentDensity = 0.5

agentVisionDist = randseq( random.randint )(1,2)
agentMetabDist = randseq( random.randint )(4,5)
intermovement = randseq( random.expovariate )(2)
interreproduce = randseq( random.expovariate )(0.75)
gestationperiod = randseq( random.random )()

siteCapDist = randseq( random.uniform )(0.0, 3.0)
siteSugarDist = randseq( random.uniform )(0.0, 3.0)
siteRegenDist = randseq( random.random )()


################################# MAIN #########################################
# agents = []

    # a = Agent()
    # print(a.id, " ", a.sugar, " ", a.vision, " ", a.metab, " ", a.tsync)
s = Sugarscape(10)
Site.sugScape = s

s[0][0].putAgent(Agent())
s[0][1].putAgent(Agent())

s.populate()

for row in Site.sugScape:
    for site in row:
        if site.agent != None:
            site.agent.setNextEvent()

tmax = 10.0

while Site.sugScape.time < tmax and len(calendar) > 0:
    Site.sugScape.update()
    e = calendar[0]
    calendar = calendar[1:]
    e.action(*e.params)

    Site.sugScape.time = e.time



s.print()

#
# s[0][0].putAgent(Agent())
# s[0][0].agent.die()
#
# s.time = 4.0
#
#
# print("Sugar level: ", s[0][0].sugar)
#
#
# Site.sugScape = s


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
