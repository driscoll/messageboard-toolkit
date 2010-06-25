#!/usr/bin/python

class Forum:
    """vBulletin Forum
    """
    def __init__(self, name):
        self.name = name
        self.thread = {}
        self.user = {}

