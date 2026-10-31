from file_line import FileLine
import networkx as nx
from itertools import combinations, product
from bn_node import Node

VALIDATE = True


class BayesNet:
    def __init__(self):
        self.truth_tables = {}  # dict keyed on node to the tt for each node
        self.graph = nx.DiGraph()
        self.Working_Node = None

    def consume_line(self, line: FileLine):
        current_line = line
        if current_line.is_end_of_object():
            # reset everything
            self.Working_Node = None
        elif current_line:
            if current_line.is_node_line():
                node = Node(current_line)
                self.Working_Node = node
                self.truth_tables[node.Node] = node
                self.graph.add_node(node.Node, weight=1)  # todo weights? might not need them
                for parent in node.Parents:
                    self.graph.add_edge(parent, node.Node, weight=1)
                #  print(f'Node: - {node.Node}, Parents: = {node.Parents}')

            else:
                # we are not new obj line, we are not a node line,
                #  we are the tt line w prob
                self.Working_Node.set_prob(current_line.raw_line)

    def query_truth(self, query):
        #  print(f'Querying: {query}')
        asking, knowledge = self.parse_query(query)
        #  print(f'Asking: {asking}, Knowledge: {knowledge}')


        # we know what we need to know build only the nodes we care about so we can calc our dist
        relevant_nodes = set(asking.keys() | knowledge.keys())

        for node in list(relevant_nodes):
            relevant_nodes.update(nx.ancestors(self.graph, node))

        hidden = relevant_nodes - set(asking.keys()) - set(knowledge.keys())

        relevant_graph = self.graph.subgraph(relevant_nodes).copy()

        d_sep_results = {}
        ev = set(knowledge.keys())
        for node_a, node_b in combinations(asking.keys(), 2):  # check query against query
            d_sep_results[(node_a, node_b)] = self.d_sep(
                node_a, node_b, ev
            )
            # print(f'D-sep results: {d_sep_results} for combination {node_a} and {node_b}')
            if VALIDATE:
                expected = nx.is_d_separator(self.graph, {node_a}, {node_b}, set(knowledge.keys()))
                # print(f'networkx is_d_separator results: {expected}')

        for node in asking.keys():  # Now query against evidence - check ev, and hidden for completeness
            for e in ev:
                d_sep_results[(node, e)] = self.d_sep(
                    node, e, ev - set(e)
                )
            for h in hidden:
                d_sep_results[(node, h)] = self.d_sep(
                    node, h, ev
                )

        totals = {}
        query_nodes = list(asking)
        # outer is the query variables, inner will be hidden across with evidence
        # calc prob at each iteration, sum over the hidden values, and cache on the outer row
        # NOTE: used product because that doesnt violate the spirit of the assignment, it just simplifies combinations
        for outer_values in product(["T", "F"], repeat=len(query_nodes)):
            query_assignment = dict(zip(query_nodes, outer_values))
            row_total = 0.0
            for inner_values in product(["T", "F"], repeat=len(hidden)):
                hidden_assignment = dict(zip(hidden, inner_values))

                assignment = query_assignment | hidden_assignment | knowledge
                joint = 1.0

                for node in relevant_nodes:
                    joint *= self.truth_tables[node].get_prob(assignment, assignment.get(node))  # collect probs

                row_total += joint  # sum over these

            totals[outer_values] = row_total  # save it

            # sum all the rows
        evidence_probability = sum(totals.values())

        # row matching the requested query values
        requested_key = tuple(asking[node] for node in query_nodes)

        #  final math to calc prob keyed on query vars
        #  print(f'Response to key: {requested_key}')
        prob = totals[requested_key] / evidence_probability  #  normalize
        print(f'Probability of {query} = {prob}')
        if len(d_sep_results) > 0:
            print(f'D-sep: {d_sep_results}')
        else:
            print(f'No D-sep')
        return prob

        # P(X|e) = alpha P(X, e) = alpha SIGy P(X, e, y) ## where e is evidence(observed values) y is unobserved
        # P(cause|effect) = P(effect|cause)P(cause) / P(effect)
        # P(X, Y|Z) = P(X|Z)P(Y|Z)
        # P(D=T, E=T | A=F, C=T) = P(D=T|A=F,C=T)P(E=T|A=F,C=T) << Book pg 419.... y={B, F} e={A, C}, X = {D, E}
        # P(D=T|A=F,C=T) = SUM b P(B)P(A=F)P(D=T|A=F,B) * SUM b P(B)P(C=T)P(E=T|B,C=T)
        # sum b,f P(B)P(A=F)P(C=T)P(D=T|A=F,B)P(E=T|B,C=T) ????does f even matter here?

    def parse_query(self, query):
        # need to put these into what we are asking for, and what we know
        # but drop the P() first
        data = query[query.index("(") + 1:query.rindex(")")]
        if "|" in data:
            query_part, knowledge_part = data.split("|", 1)
        else:
            query_part = data
            knowledge_part = None

        asking = {}
        knowledge = {}
        for qp in query_part.split(","):
            parts = qp.strip().split('=')
            asking[parts[0].strip()] = parts[1].strip()  # [D] = T

        if knowledge_part is not None:
            for kp in knowledge_part.split(","):
                parts = kp.strip().split('=')
                knowledge[parts[0].strip()] = parts[1].strip()  # [D] = T
        return asking, knowledge

    def d_sep(self, node_a, node_b, evidence):
        # create undirected graph to do dsep
        # working_graph = nx.Graph(self.graph)
        # we will need to do a few things before calculating d-sep or removing evidence nodes.
        # colliders need their parents to have a connection so removing evidence does not cause an unnatural d sep

        relevant = {node_a, node_b} | set(evidence)
        for node in list(relevant):
            relevant.update(nx.ancestors(self.graph, node))  # add all parents because they will matter

        # get back just the relevant nodes and their ancestors into a graph to use
        ancestral_graph = self.graph.subgraph(relevant).copy()
        # create parent bonds to ensure correct collider behavior after evidence removal and checking for paths
        working_graph = self.handle_colliders(ancestral_graph)

        # remove all evidence to check if we are block between our nodes
        working_graph.remove_nodes_from(evidence)

        # if we have no path then we are d-sep because we are blocked on all paths
        dsep = not nx.has_path(working_graph, node_a, node_b)

        if not dsep:
            # get path info
            print(f'{node_a} and {node_b} are NOT d-sep given: {evidence}')
            print(f'Path: {nx.shortest_path(working_graph, node_a, node_b)}')
        else:
            print(f'{node_a} and {node_b} are d-sep given: {evidence}')
        return dsep
        # # now if we remove all evidence and still have a path we are NOT d sep and do not have conditional independednc
        # working_graph.remove_nodes_from(evidence)
        #
        # # if we can get from a to b then we are not dsep
        # if node_a in working_graph and node_b in working_graph and nx.has_path(working_graph, node_a, node_b):
        #     return False
        # return True

    def handle_colliders(self, graph):
        u_g = nx.Graph(graph)  # Make edges undirected

        for node in graph.nodes:
            parents = list(graph.predecessors(node))

            for i, p1 in enumerate(parents):
                for p2 in parents[i + 1:]:
                    # ok we have 2 parents, so add an edge that way the collider operates correctly
                    # after we remove evidence by still providing a path even if child evidence is removed
                    u_g.add_edge(p1, p2)

        return u_g

    def print(self):
        print(f'Truth tables: {self.truth_tables}')
        print(f'Nodes: {list(self.graph.nodes)}')
        print(f'Edges: {list(self.graph.edges)}')
