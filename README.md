# Pipit

[![Build Status](https://github.com/hpcgroup/pipit/actions/workflows/unit-tests.yaml/badge.svg)](https://github.com/hpcgroup/pipit/actions)
[![docs](https://readthedocs.org/projects/pipit/badge/?version=latest)](https://pipit.readthedocs.io/en/latest/?badge=latest)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python-based library for analyzing execution traces from parallel programs.

# Getting Started
To install pipit, first install the dependencies in [requirements.txt](./requirements.txt) with `pip install -r requirements.txt`. You'll also need to have jupyter installed if you want to use the vis. After all the dependencies are installed, you can install pipit with `pip install -e <pipit_root>` or `conda develop <pipit_root>`
___
# Calculating Lateness
[The Lateness Paper](https://www.cs.umd.edu/~bhatele/pubs/pdf/2016/tpds2016.pdf)
## Before Starting with what the paper does
- [ ] Finding and linking all MPI_Send and MPI_Recv calls
## Mandatory Phase Partitioning
- [ ] Make a new DataFrame with the following columns
  - [ ] `process`, `receive_from`, `send_to`, `time`
- [ ] Iterate through all the `MPI_Send` calls, and for each call do:
  - [ ] add the send to the new dataframe
  - [ ] add the corresponding receive to the new dataframe
- [ ] Sort the DataFrame by `time`
- [ ] From this DataFrame we can make a graph
  - [ ] All processes will have a `start` root node
  - [ ] Every other node will be corresponding to a row in the DataFrame

**Now we'll be at the stage of Figure 2a**

## Leap Partitions
## Definitions
* **graph distance from source** defined recursively:
  * *0* if root
  * *max(parents.distance)* o.w.
* **Leap**
  * all partitions with the same graph distance from source
* **Complete (Leap)**
  * contains operations from all processes
* **will_expand**
  * if this expands the set of processes participating in the current leap
* **incoming leap distance** 
  * the minimum of the first operation entry time for each of its processes and the operation exit time of their previous operation in the partition’s previous-leap neighbors
* **outgoing leap distance**
  * the minimum of the last operation exit time for each of its processes and the operation entry time of the next operation in the partition’s next-leap neighbors
### Questions
* In figure 4, are the stride boundaries leaps? Are we positioning based on leaps or partitions?
* For each leap, are merging the partition's inside it together?
* Why do we want to complete the leaps? Isn't having incomplete an indication of lateness?



___
### Contributing

Pipit is an open source project. We welcome contributions via pull requests,
and questions, feature requests, or bug reports via issues.

### License

Pipit is distributed under the terms of the MIT License.

All contributions must be made under the the MIT license. Copyrights in the
Pipit project are retained by contributors.  No copyright assignment is
required to contribute to Pipit.

See [LICENSE](https://github.com/pssg-int/trace-analysis/blob/develop/LICENSE)
for details.

SPDX-License-Identifier: MIT
