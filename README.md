# Saturate code - an application for optimization problems linked with social network analysis

## Brief description and purpose
Implementation of saturate code and optimization routines.

A foundational and exhaustive code bank, includes various network related optimization routines that can be used for a class of combinatorial optimization problems, using social networks as an application case. It builds on the theoretical foundations highlighted in the linked papers. The idea is akin to set coverage, how to cover a given set with uncertainities and resource constraints. Please see the papers for mathematical details and insights. The code bank is to aid and provide insights into implementation and practical use cases that can leverage the theoretical foundations. 

Several different optimization routines are combined with computational scale-up methods that might help to run these optimization related programs more smoothly. Further a novel multithreaded approach is augmented to further boost computational processes and runtime. 

I hope this can help those who wish to implement these algorithmic routines/adapt it for their own experiments. 
 
 ## Relevant papers include: 
 1. Krause, A., McMahan, H. B., Guestrin, C., & Gupta, A. (2008). Robust Submodular Observation Selection. Journal of Machine Learning Research, 9(12).
 2. He, X., & Kempe, D. (2018). Stability and robustness in influence maximization. ACM Transactions on Knowledge Discovery from Data (TKDD), 12(6), 1-34.
 3. Goyal, A., Lu, W., & Lakshmanan, L. V. (2011, March). Celf++ optimizing the greedy algorithm for influence maximization in social networks. In Proceedings of the 20th international conference companion on World wide web (pp. 47-48).
 
## Software requirements:
Most should be available under anaconda standard releases.
1. networkx (for social network processing)
2. scipy 
3. numpy
4. matplotlib (for visualizations if needbe)
5. threading (parallizing for computational efficiency)
5. gurobipy (for running optimization pipelines)
(follow the instructions here for further details on gurobi: https://www.gurobi.com/documentation/9.5/quickstart_mac/cs_anaconda_and_grb_conda_.html)
 
## Contribution details and acknowledgement

Copyright @ Subhasree Sengupta 

Contact: subhass@g.clemson.edu & susengup@syr.edu

Citation, acknowledgement needed of this github code bank if it is used/modified. 

### This project is licensed under the terms of the MIT license.

### Please use the following DOI for citation purposes: [![DOI](https://zenodo.org/badge/634052812.svg)](https://zenodo.org/badge/latestdoi/634052812)
 
 
