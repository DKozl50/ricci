import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import ot


def _fix_graph(gr):
    """Add weights to nodes and edges, if none detected."""
    # add weights to edges if none are present
    if not nx.get_edge_attributes(gr, 'weight'):
        for e in gr.edges:
            gr.edges[e]['weight'] = 1

    # add weights to nodes if none are present
    if not nx.get_node_attributes(gr, 'weight'):
        for v in gr.nodes:
            gr.nodes[v]['weight'] = 1


def _forman_edge(gr, edge):
    """Calculate Forman-Ricci curvature for one exact edge."""
    v1, v2 = edge
    # important weights
    we = gr.edges[edge]['weight']
    wv1 = gr.nodes[v1]['weight']
    wv2 = gr.nodes[v2]['weight']
    
    f = (wv1+wv2) / we
    for ev1 in gr.neighbors(v1):
        if ev1 != v2:
            f -= wv1 / np.sqrt(we*gr.edges[v1, ev1]['weight'])
    for ev2 in gr.neighbors(v2):
        if ev2 != v1:
            f -= wv2 / np.sqrt(we*gr.edges[v2, ev2]['weight'])
    f *= we
    return f


def _create_mu(vertex, gr, idleness):
    """Calculate mu; used in Ollivier calculations."""
    neighborlist = list(gr.neighbors(vertex))
    spread = (1-idleness) / len(neighborlist)
    mu = [spread if v in neighborlist else 0 for v in gr.nodes()]
    mu[vertex] = idleness
    return mu


def draw_graph(gr, attr='weight'):
    """Draw graph showing edge attribute ('weight' by default). Returns plt"""
    pos = nx.drawing.layout.kamada_kawai_layout(gr)
    nx.draw(gr, pos, with_labels=True)
    elabels = nx.get_edge_attributes(gr, attr)
    # convert floats to a readable format
    elabels = {(v1, v2): str(round(val, 5)) for (v1, v2), val in elabels.items()} 
    nx.draw_networkx_edge_labels(gr, pos, 
                                 edge_labels=elabels)
    return plt


def forman(gr, fix=True):
    """Add 'forman' attribute to graph edges and fill it with Forman-Ricci curvature."""
    if fix:
        _fix_graph(gr)

    for e in gr.edges():
        gr.edges[e]['forman'] = _forman_edge(gr, e)


def ollivier(gr, idleness=0, fix=True):
    """Add 'ollivier' attribute to graph edges and fill it with Ollivier-Ricci curvature."""
    if fix:
        _fix_graph(gr)

    floyd_warshall = nx.algorithms.shortest_paths.dense.floyd_warshall_numpy(gr)
    for e in gr.edges():
        v1, v2 = e
        mu1 = _create_mu(v1, gr, idleness)
        mu2 = _create_mu(v2, gr, idleness)
        wd = ot.emd2(mu1, mu2, floyd_warshall)
        gr.edges[e]['ollivier'] = 1 - wd/gr.edges[e]['weight']
