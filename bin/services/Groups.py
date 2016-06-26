from classes.SimpleService import SimpleService

class Groups (SimpleService):
    """Container that consist in storing a set of tagged elements"""
    def __init__ (self, redis = None, namespace = "", *args, **kwargs):
        self._redis = redis
        self.namespace = namespace
        self._singletons = {}
        self._sets = {}
        self._redisVars = set()
        self._taglist = ["*"]

    def __str__(self):
        buf = ""
        prefix = ""
        if self._singletons:
            buf += "Singletons: " + str(self._singletons)
            prefix = ", "
        if self._sets:
            buf += prefix + "Sets: " + str(self._sets)
            prefix = ", "
        if self._redisVars:
            buf += prefix + "RedisVars: " + str(self._redisVars) 
        return buf

    def __del__ (self) :
        for k in self._redisVars:
            self._redis.delete(self._redName(k))

    def _tagNum (self, tag):
        """All tags are represented by a binary mask."""
        return 1 << self._taglist.index(tag)

    def _redName (self,num):
        """The names of the variable, given a tag"""
        return self.namespace+"_"+str(num)

    def _checkRedis (self, tn):
        l = len(self._sets[tn])
        if l > 64 and self._redis:
            self._redis.sadd(self._redName(tn), self._sets[tn])
            self._redisVars.add (tn)
            del self._sets[tn]

    def _insertAll (self, atoms, tn):
        if len (atoms) == 1:
            (val,) = atoms
            self._insert (val, tn)
        elif tn in self._redisVars :
            self._redis.sadd(self._redName(tn), atom)
        elif tn in self._sets :
            self._sets[tn] |= set(atoms)
            self._checkRedis(tn)
        else:
            self._sets[tn] = set(atoms)
            self._checkRedis(tn)

    def _insert (self, atom, tn):
        if tn in self._redisVars:
            self._redis.sadd(self._redName(tn), atom)
        elif tn in self._sets:
            self._sets[tn].add(atom)
            self._checkRedis(tn)
        elif tn in self._singletons :
            s = set((self._singletons[tn], atom,)) 
            self._insertAll(s, tn)
            del self._singletons[tn]
        else :
            self._singletons[tn] = atom

    def _redrem (self, atoms, tn):
        self._redis.srem(self._redName(tn), atoms)
        rn = self._redName(tn)
        c = self._redis.scard(rn)
        if c < 64:
            if c > 1:
                self._sets[tn] = set (self._redis.smembers (rn))
            elif c == 1:
                self._singletons[tn] = self._redis.spop(rn)
            self._redis.delete(rn)

    def _rem (self, atoms, tn):
        if not tn in self._sets:
            return
        self._sets[tn] -= atoms
        l = len(self._sets[tn])
        if l <= 1:
            if l == 1: 
                self._singletons[tn] = self._sets[tn].pop()
            del self._sets[tn]

    def add (self, atoms, tags = ''):
        tn = 1
        for tag in tags.split(' '):
            if tag not in self._taglist:
                self._newTag(tag)
            tn |= self._tagNum(tag)
        self._insertAll (atoms, tn)

    def remove (self, atoms):
        satoms = set(pks)
        for k in self._redisVars:
            _redrem(atoms, k)
        for k in list(self._sets.keys()):
            _rem(atoms, k)
        for k in list(self._singletons.keys()):
            if k in self._singletons[k] in satoms :
                del self._singletons[k]

    def _newTag (self, tag):
        for i in range(len(self._taglist)):
            if self._taglist[i] == None:
                self._taglist[i] = tag
                return
        self._taglist.append(tag)

    def action_tag(self, atoms, tag):
        if tag not in self._taglist :
            self._newTag (tag)
        newTagged = set(atoms) 
        tn = self._tagNum(tag)

        for k,v in list(self._singletons.items()) :
            if tn & k:
                continue
            if v in newTagged :
                self._insert(v, k|tn)
                del self._singletons[k] 

        for k,v in list(self._sets.items()) :
            if tn & k:
                continue
            s = v & newTagged
            if not s:
                continue
            self._insertAll (s, tn|k)
            self._rem (s, k)

        for k in self._redisVars :
            if tn & k:
                continue
            s = self.redis.sinter(self._redisName(k),newTagged)
            if not s:
                continue
            self._insertAll (s, tn|k)
            self._redrem (s, k)

    def action_untag(self, atoms, tag):
        """Untag all 'keys' from 'tag'"""
        if tag == "*":
            return
        oldTagged = set(atoms)
        tn = self._tagNum(tag)
        for k,v in list(self._singletons.items()) :
            if not tn & k:
                continue
            if v in oldTagged :
                self._insert(v, k-tn)
                del self._singletons[k] 

        for k,v in list(self._sets.items()) :
            if not tn & k:
                continue
            s = v & oldTagged
            if not s:
                continue
            self._insertAll (s, k-tn)
            self._rem (s, k)

        for k in self._redisVars :
            if not tn & k:
                continue
            s = self.redis.sinter(self._redisName(k),oldTagged)
            if not s:
                continue
            self._insertAll (s, k-tn)
            self._redrem (s, k)

    def action_delTag (self, tag):
        if tag == "*":
            return
        tn = self._tagNum(tag)
        self._singletons = { k&(~tn): v for k, v in self._singletons.items() }
        self._sets = { k&(~tn): v for k, v in self._sets.items() }
        for k in self._redisVars :
            if k & tn :
                self._redis.rename(self._redName(tn), self._redName(k&(~tn)))
                self._redisVars.remove(k)
                self._redisVars.add(k&(~tn))
        self._taglist[self._taglist.index(tag)] = None

    def action_select (self, expression):
        expression = expression.split(' ')
        incMask = [] 
        for operand in expression :
            if operand[0] in ('&', '-', '!',):
                tn = self._tagNum(operand[1:])
                if operand[0] == "&":
                    for m in incMask :
                        m[0] |= tn
                elif operand[0] == "-":
                    for m in incMask :
                        m[1] |= tn
                elif operand[0] == "!":
                    incMask.append([0, tn,])
            else:
                tn = self._tagNum(operand)
                incMask.append([tn, 0,])
    
        accumulator = set()
        for mask in incMask:
            for t, e in self._singletons.items():
                if mask[0] & t == mask[0] and not t & mask[1] :
                    accumulator.add (e)
            for t, e in self._sets.items():
                if mask[0] & t == mask[0] and not t & mask[1] :
                        accumulator |= e 
            for t in self._redisVars:
                if mask[0] & t == mask[0] and not t & mask[1] :
                    accumulator |= set (self._redis.smembers (self._redName(t)))
        return accumulator

