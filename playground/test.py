#!/usr/bin/python

if __name__ == "__main__":
    # push the strings
    strings = [
        "manufacturer",
        "model",
        "description",
        "version",
        "http://www.mystico.org",
        "1"]
    print len(strings)
    for i in range(2, len(strings)):
        print i, strings[i]
