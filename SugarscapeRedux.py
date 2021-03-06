# refactored version of Sugarscape model. More modular(?), extensible(??), and maybe slightly more efficient(???) than previous versions.
# future improvements: use a tuple unpacking approach instead of multiple returns approach with position() function
# doesn't delete self after dying. Could be because you assign it to a variable to track it, which doesn't leave it with 0 pointers to it.
# sugar level at time of death is reeeeeally close to 0 but not actually 0 even though the time of death is right. Seems to be right at other, non-death times.
# setNextEvent() stops occurring pretty soon.
# put in assert statements to debug
# you didn't(?) cancel events already scheduled that took place within the gestation period, FIND WAYS TO CANCEL THEM. PRIORITY!!!!!!!
# set() causes weird errors because of randomization


import random
import bisect
import functools
import pdb

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
        # self.nextEvent = None
# more general approach: start with min time next action
# find cancellation conditions with that action that are true, and choose one with min time
# check cancel conditions on those, until there are no cancel conditions for it that are true.
# that is the next event.

    def setNextEvent(self):
        nextAction = min(self.actions, key= lambda action : self.actions[action])
        params = ()
        # time at which sugar goes to 0 satisfies: agent's init sugar + t*(site's regen rate - self.metabolism) = cur sugar = 0s
        if (self.site.regen < self.metab) and ((-self.sugar/(self.site.regen-self.metab)) <= self.actions[nextAction]):
            nextAction = self.die
            if self.gestating:
                for e in calendar:
                    if e.time > Site.sugScape.time and e.action == self.giveBirth or e.action == self.partner.giveBirth:
                        calendar.remove(e)

            self.actions[self.die] = -(self.sugar/(self.site.regen-self.metab))+Site.sugScape.time

        if nextAction != self.die and self.gestating:
            nextAction = self.giveBirth # weeeeeird behavior, if you put this after the for loop (not even inside) then it throws an error
            # cancel all events scheduled for gestation!!
            for e in calendar:
                if e.action == self.partner.giveBirth:
                    calendar.remove(e)



        bisect.insort(calendar, Event(nextAction, self.actions[nextAction], params))
        # mino = min(self.actions, key= lambda action : self.actions[action])
        # if self.actions[mino] < 0:    print(mino, self.actions[mino], "HOOOOOOOO")


        # if nextAction == self.move:
        #     X, Y = self.site.position()
        #     if (Site.sugScape[X][Y].regen < self.metab) and ((-self.sugar/(Site.sugScape[X][Y].regen-self.metab)) <= self.actions[self.move]):
        #         nextAction = self.die
        #
        #     if self.gestating:  nextAction = self.giveBirth
        #
        # if nextAction == self.giveBirth:


    def cancelEvents(self):
        for e in calendar:
            if e.time > Site.sugScape.time and e.time < self.actions[self.giveBirth]:
                if e.action in self.actions and e.action != self.die or e.action in self.partner.actions and e.action != self.partner.die:
                    calendar.remove(e)

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

        self.site.agent = None
        Site.sugScape.emptySites.append(self.site)

        maxSugSite = max(emptySitesInSight, default= self.site, key= lambda s : s.sugar)

        maxSugSite.putAgent(self)


        # self.sugar -= self.metab should this be included?
        print(self.id, " moved.")

        self.actions[self.move] += next(intermovement)
        # self.eventTimes[EType.MOVE.value] += self.getInterMovement()
        self.setNextEvent()

    def die(self):
        X, Y = self.site.position()
        chosenSite = self.site
        Site.sugScape[X][Y].agent = None
        Site.sugScape.emptySites.append(chosenSite)

        if len(Site.sugScape.emptySites) > 0:
            chosenSite = random.choice(Site.sugScape.emptySites)

        chosenSite.putAgent(Agent())
        print(self.id, " has died. RIP")


    def findPartner(self):
        sitesInSight = self.getNeighborhood()
        # THIS LINE DOESN'T PREVENT BEST AGENT TO BE A NON-GESTATING AGENT. FIX THIS TOO
        filledSitesInSight = list(filter(lambda site : True if not site.empty() else False, sitesInSight))
        availableAgentSites = list(filter(lambda site : True if (not site.agent.gestating and site.agent != self) else False, filledSitesInSight))
        bestAgentSite = max(availableAgentSites, default = None, key= lambda agent : agent.sugar)
        bestAgent = None
        if bestAgentSite != None:   bestAgent = bestAgentSite.agent

        if bestAgent != None:
            self.partner = bestAgent
            bestAgent.partner = self
            self.gestating = True
            bestAgent.gestating = True
            self.actions[self.giveBirth] = Site.sugScape.time + next(gestationperiod)
            self.cancelEvents()

        print(bestAgent.id, "is best agent for", self.id) if bestAgent != None else print("No partner in sight for", self.id)

        self.actions[self.findPartner] += next(interreproduce)
        self.setNextEvent()

    def giveBirth(self):
        print("Parent", self.id, "is giving birth.")
        sitesInSight = self.getNeighborhood()
        sitesInSight.extend(self.partner.getNeighborhood())

        bestSite = max([site for site in sitesInSight if site.empty()], default = None, key = lambda site : site.sugar)

        if bestSite != None:
            bestSite.putAgent(Agent())
            bestSite.agent.sugar = (self.sugar+self.partner.sugar)/2
            self.sugar /= 2
            self.partner.sugar /= 2
            print("Parents", self.id, self.partner.id, "welcome new baby new baby agent at", *bestSite.position(), ".")

        #else:   print("Oops, no new baby born. :(")
        # cancel partner births
        for e in calendar:
            if e.action == self.partner.giveBirth:
                calendar.remove(e)

        self.partner.gestating = False
        self.partner.partner = None # THIS LINE IS PROBABLY CAUSING PROBLEMS
        self.gestating = False
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
        Site.sugScape.emptySites.remove(self)

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
                    site.putAgent(a)
                    # agents.append(a)

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

############################ FIDDLING SECTION ##################################

random.seed(8657309)

agentDensity = 0.5

agentVisionDist = randseq( random.randint )(1,2)
agentMetabDist = randseq( random.uniform )(10.0,11.0)
intermovement = randseq( random.expovariate )(2)
interreproduce = randseq( random.expovariate )(2)
gestationperiod = randseq( random.uniform )(0.0, 1.0)

siteCapDist = randseq( random.uniform )(0.0, 1.0)
siteSugarDist = randseq( random.uniform )(0.0, 3.0)
siteRegenDist = randseq( random.random )()

tmax = 15
################################# MAIN #########################################

s = Sugarscape(10)
Site.sugScape = s

a = Agent()


s.populate()

for row in Site.sugScape:
    for site in row:
        if site.agent != None:
            site.agent.setNextEvent()



for row in Site.sugScape:
    for site in row:
        if site.agent != None and site.agent.id == 10:
            a = site.agent

while Site.sugScape.time < tmax and len(calendar) > 0:
    e = calendar[0]
    Site.sugScape.time = e.time
    Site.sugScape.update()
    calendar.remove(e)
    e.action(*e.params)
