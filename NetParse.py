#!/usr/bin/env python3

from file_line import FileLine
from bayes_nets import BayesNet
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("TableFile", nargs="?")
    parser.add_argument("QueryFile", nargs="?")
    args = parser.parse_args()
    if args.TableFile is None or args.QueryFile is None:
        print(f'Args are invalid: {args}')
        return
    bayes_net = BayesNet()
    with open(args.TableFile, "r") as file:
        for line in file:
            fl = FileLine(line)
            bayes_net.consume_line(fl)

    query = open(args.QueryFile, "r")
    results = bayes_net.query_truth(query.readline())

    #  print(f'{bayes_net.print()}')


if __name__ == "__main__":
    main()
