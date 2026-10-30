#!/usr/bin/env python3

from file_line import FileLine
from bayes_nets import BayesNet

FILENAME = 'Tb1.txt'
QUERY_FILENAME = 'TB1Query2.txt'


def main():
    bayes_net = BayesNet()
    with open(FILENAME, "r") as file:
        for line in file:
            fl = FileLine(line)
            bayes_net.consume_line(fl)

    query = open(QUERY_FILENAME, "r")
    results = bayes_net.query_truth(query.readline())
    print(f'Results {results}')
    print(f'{bayes_net.print()}')


if __name__ == "__main__":
    main()
