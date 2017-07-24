.. _cross_channel_graph:

===================
Sparse Commit Graph
===================

One challenge in the creation of the generated repository is correctly
ordering the incoming changesets in a commit graph. Common graphs in 
mozilla-central look like the following, with "green" nodes being the
ones affecting localization that we want to transform.

.. digraph:: full_tree

    graph [ rankdir=LR , scale=0.5 ];
    "red0" -> "green1" ;
    "red0" -> "red1" ;
    "red1" -> "merge-red1" ;
    "green1" -> "merge-red1" ;
    "merge-red1" -> "green2" ;
    "merge-red1" -> "red2" ;
    "red2" -> "merge-red2" ;
    "green2" -> "merge-red2" ;
    "merge-red2" -> "green3" ;
    "merge-red2" -> "red3" ;
    "green3" -> "merge-red3" ;
    "red3" -> "merge-red3" ;
    "merge-red3" -> "green4" ;
    "merge-red3" -> "red4" ;
    "red4" -> "merge-red4" ;
    "green4" -> "merge-red4" ;
    "merge-red4" -> "green5" ;
    "merge-red4" -> "red5" ;
    "red5" -> "green4.5" ;
    "green4.5" -> "merge-red5" ;
    "green5" -> "merge-red5" ;
    "green1" [ color=green ] ;
    "green2" [ color=green ] ;
    "green3" [ color=green ] ;
    "green4" [ color=green ] ;
    "green4.5" [ color=green ] ;
    "green5" [ color=green ] ;

What we'd expect to get would be a graph that just goes through our nodes,
in this case effectively a linear graph.

.. digraph:: target

    graph [ rankdir=LR ];
    "green1" -> "green2" ;
    "green2" -> "green3" ;
    "green3" -> "green4" ;
    "green4" -> "green5" ;
    "green4" -> "green4.5" ;

Natively, mercurial creates a graph that shows all paths from each node
to another that can be taken in the full graph, creating, in this case,
a graph that connects all nodes.

.. digraph:: mesh

    graph [ rankdir=LR ];
    "green1" -> "green2" ;
    "green1" -> "green3" ;
    "green2" -> "green3" ;
    "green3" -> "green4" ;
    "green1" -> "green4" ;
    "green2" -> "green4" ;
    "green3" -> "green5" ;
    "green1" -> "green5" ;
    "green4" -> "green5" ;
    "green2" -> "green5" ;
    "green3" -> "green4.5" ;
    "green1" -> "green4.5" ;
    "green4" -> "green4.5" ;
    "green2" -> "green4.5" ;

The code generating our target repository needs to either strip that
graph down, or create a sparse graph from scratch.
