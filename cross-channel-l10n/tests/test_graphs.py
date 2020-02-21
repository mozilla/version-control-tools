import unittest

from mozxchannel import graph

class TestOptimize(unittest.TestCase):
    def test_simple(self):
        g = graph.SparseGraph(None, [])
        g.add_parents((
            (5, {4}),
            (4, {3}),
            (3, set()),
        ))
        g.finalize()
        self.assertEqual(g.roots, [3])
        self.assertEqual(g.merges, [])

    def test_duplicate_arcs(self):
        g = graph.SparseGraph(None, [])
        g.add_parents((
            (7, {3, 6}),
            (6, {5}),
            (5, {3, 4}),
            (4, {3}),
            (3, set()),
        ))
        g.finalize(optimize=False)
        self.assertEqual(g.roots, [3])
        self.assertEqual(g.merges, [7])
        g.eliminateShortCuts()
        self.assertEqual(g.merges, [])
