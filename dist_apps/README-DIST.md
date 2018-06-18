Basic Compiling Through CMake (Distributed and Heterogeneous Galois)
================================================================================

The dependencies for distributed Galois are exactly the same as shared-memory
Galois except that it requires an MPI library (e.g. mpich2) to be on the 
system as well.

To build distributed/heterogeneous Galois, certain CMake flags must be 
specified.

For distributed Galois:

`cmake ${GALOIS_ROOT} -DENABLE_DIST_GALOIS=1`

For heterogeneous Galois:

`cmake ${GALOIS_ROOT} -DENABLE_HETERO_GALOIS=1`

Note that distributed Galois requires CUDA 8.0 and above.

Of course, you can combine the flags as well:

`cmake ${GALOIS_ROOT} -DENABLE_DIST_GALOIS=1 -DENABLE_HETERO_GALOIS=1`

Compiling with distributed Galois will add the 'dist_apps' directory to the
build folder. Compiling with heterogeneous Galois enabled with enable
certain options in 'dist_apps'.

Compiling Provided Apps
================================================================================

Once CMake is successfully completed, you can build the provided apps by 
moving into the apps directory and running make. For example, if you wanted
to build Lonestar's bfs, you would do the following:

`cd lonestar/bfs; make`

Running Provided Apps
================================================================================

You can learn how to run compiled applications by running them with the -help
command line option:

`./bfs -help`

Most of the provided graph applications take graphs in a .gr format, which
is a Galois graph format that stores the graph in a CSR or CSC format. We 
provide a graph converter tool under 'tools/graph-convert' that can take
various graph formats and convert them to the Galois format.

==== Running Provided Apps (Distributed Apps) ====

The distributed applications have a few common command line flags that are
worth noting. More details can be found by running a distributed application
with the -help flag.

`-partition=<partitioning policy>`

Specifies the partitioning that you would like to use when splitting the graph
among multiple hosts.

`-graphTranspose`

Specifies the transpose of the provided input graph. This is used to 
create certain partitions of the graph (and is required for some of the 
partitioning policies). It also makes 

`-runs`

Number of times to run an application.

`-statFile`

Specify the file in which to output run statistics to.

`-verify`

Outputs a file with the result of running the application. For example, 
specifying this flag on a bfs application will output the shortest distances
to each node.

Running Provided Apps (Heterogeneous Apps)
================================================================================

Heterogeneous apps have additional command line parameters:

`-num_nodes=<num>`

Specifies the total number of PHYSICAL machines on the system. For example,
you could have 2 machines with 8 GPUs each for a total of 16 processes,
but you still only have 2 machines.

`-pset=<string>`

Specifies the architecture to run on on a single machine using "c" and "g". For
example, if I have 2 multi-core machines with 8 GPUs each, but I want to run with
3 cores and 3 GPUs on each machine, I would use -pset="cccggg". Therefore,
I would have a total of 12 units of execution: 6 cores and 6 GPUs.

Basic Use (Creating Your Own Applications)
================================================================================

You can run the sample applications and make your own Galois programs directly
in the build tree without installing anything. Just add a subdirectory under
lonestar, copy a CMakeLists.txt file from another application to your new
application, and add the subdirectory to the CMakeLists in lonestar.