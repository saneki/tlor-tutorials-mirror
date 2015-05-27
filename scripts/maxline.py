#!/usr/bin/env python

import re
import sys

def to_lines(line, maxlen=100):
    words = re.findall(r"\S+", line)
    if(len(words) <= 2): return [line]

    count = 0
    lines = []
    contents = []
    for word in words:
        count += len(word) + 1
        if count > maxlen:
            lines.append('{0}\n'.format(' '.join(contents)))
            contents = []
            count = len(word) + 1
        contents.append(word)

    if len(contents) > 0:
        lines.append('{0}\n'.format(' '.join(contents)))

    return lines

def perform(filepath, maxlen=100):
    lines = []
    with open(filepath, 'r') as file:
        lines = file.readlines()

    for line in lines:
        if(re.match("\A[a-zA-Z0-9]", line)):
            xlines = to_lines(line, maxlen)
            for xline in xlines:
                print(xline.rstrip())
        else: print(line.rstrip())

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        perform(sys.argv[1])
    else:
        print('Filepath is required', file=sys.stderr)
