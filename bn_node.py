import file_line


class Node:
    def __init__(self, current_line: file_line):
        nodes = current_line.nodes()
        self.Parents = nodes[:-1]
        self.Node = nodes[-1]
        self.Probabilities = {}  # dictionary keyed on evidence to a prob value [(t,f,t,t)] = .34

        # if len(self.Parents) > 0:
        #     self.ProbabilityStatement = f"P({self.Node}|{','.join(self.Parents)})"
        # else:
        #     self.ProbabilityStatement = f"P({self.Node})"
        # print(f'ProbabilityStatement: {self.ProbabilityStatement}')

    def get_key(self, parts, parent_truth):
        # parts will be {'D': 'T', 'C': 'F'} of some sort
        keyed_values = {}
        for key, value in parts.items():
            keyed_values[key] = value

        key = tuple(keyed_values[p] for p in self.Parents) + (parent_truth,)  # always on the end

        return key

    def set_prob(self, prob_string):
        parts = prob_string.split()
        print(f'PARTS: {parts}')
        #  last 1 is always truth only, can hold the f as well per line
        # TODO we need to key the node to the column of TT as well
        prob = parts[-1]
        truth = parts[-2]
        false_truth = "F" if truth == "T" else "T"
        truth_key = tuple(parts[:-1])
        true_key = truth_key[:-1] + (truth,)
        false_key = truth_key[:-1] + (false_truth,)

        self.Probabilities[true_key] = float(prob)
        self.Probabilities[false_key] = 1.0 - float(prob)
        print(f'Prob: {prob} - Table: {truth_key}')

    def get_prob(self, parts, parent_truth):
        key = self.get_key(parts, parent_truth)
        prob = self.Probabilities[key]
        return prob
