import math
#define class and initialize
class SYM:
    def __init__(self, the, s=None, n=None):
        self.txt = s or " "
        self.at = n or 0
        self.n = 0
        self.has = {}
        self.mode = None
        self.most = 0
        self.the = the

# --UPDATE
# add()
    def add(self, x):
        if x != "?":
            self.n += 1
            self.has[x] = 1 + (self.has.get(x, 0))
            if self.has[x] > self.most:
                self.most, self.mode = self.has[x], x


# --QUERY
# mid()
    def mid(self):
        return self.mode

# div()
    def div(self, e=0):
        for v in self.has.values():
            e -= v / self.n * math.log2(v / self.n)
        return e

# small()
    def small(self):
        return 0

#like()
    def like(self, x, prior):
        try:
            # print(self.n)
            return ((self.has.get(x, 0) or 0) + self.the.m * prior) / (self.n + self.the.m)
        except ZeroDivisionError :
            print(self.has.get(x, 0))
            print(prior)
            print(self.the.m)
            print(self.n)