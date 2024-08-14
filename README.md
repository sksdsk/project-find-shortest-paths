# PATH_4

**About**

This uni project is a collaborative effort involving 9 participants, focusing on software engineering and agile development processes.

**Background**

In the world of modern industry, a streamlined and optimized material transport process not only
reduces operational costs but also enhances overall productivity. Hence, a robust shortest path algorithm
could be required by plant managers to improve production efficiency. This project aims to develop a
shortest path algorithm in SQL that will return a list of shortest paths between source and destination
through a list of devices, ultimately minimizing the time taken for material transportation.

**Specifications**

The factory could be mapped out as a graph. Several types of devices are available, but only certain ones
could be selected as source or destination. Divergent device could transfer the material to multiple
destinations, and convergent device could take in materials from multiple sources.
The shortest path should connect the source and destination while minimising the cost.

**Deliverables**

The major deliverables of this project are a SQL function implementing the shortest paths algorithm, as
well as a device database that the function operates on.
The SQL script should be able to:
1. Return a list of five shortest paths for the given source and destination ordered by cost.
2. Exclude devices that are faulted or in use by another path currently running.
3. Work with divergent and convergent devices to handle transporting from one source to multiple
locations, and vice versa.
4. Reasonably scale up to larger sites with more devices.
Students should use MSSQL (recommended) or MySQL. It is recommended to use node tables and edge
tables in MSSQL to store the graph information. Sufficient documentation should be provided to assist
knowledge transfer. Further extensions such as optimising over multiple constraints are possible.
