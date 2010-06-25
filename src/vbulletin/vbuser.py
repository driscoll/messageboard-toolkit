#!/usr/bin/python

class User:
    """User in a forum
    """
    def __init__(self, id, **args):
        self.id = id
        if "handle" in args.keys():
            self.handle = str(args["handle"])
        else:
            self.handle = ''
        if "joined" in args.keys():
            self.joined = str(args["joined"])
        else:
            self.joined = ''
        if "numposts" in args.keys():
            self.numposts = int(args["numposts"])
        else:
            self.numposts = -1
