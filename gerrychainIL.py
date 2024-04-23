#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
from gerrychain import Graph, Partition, proposals, updaters, constraints, accept, MarkovChain, Election
from gerrychain.updaters import cut_edges, Tally
from gerrychain.proposals import recom
from gerrychain.accept import always_accept
from functools import partial


il_graph = Graph.from_json("IL.json")

tot_pop = sum([il_graph.nodes()[v]['TOTPOP'] for v in il_graph.nodes()])
num_dist = 17 # Number of Congressional Districts in Illinois
ideal_pop = tot_pop/num_dist
pop_tolerance = 0.02

# Define a function to determine the number of districts won by the Democratic party
def democratic_wins(partition):
    democratic_won = 0
    for district in partition.parts:
        democratic_votes = partition["G20PRED"][district]
        republican_votes = partition["G20PRER"][district]
        total_votes = democratic_votes + republican_votes
        if democratic_votes / total_votes > 0.5:
            democratic_won += 1
    return democratic_won


initial_partition = Partition(
    il_graph, # dual graph
    assignment = "CD", #initial districting plan
    updaters={
    "cut edges": cut_edges,         
    "district population": Tally("TOTPOP", alias = "district population"),
    "district HISP": Tally("HISP", alias = "district HISP"), 
    "G20PRED": Tally("G20PRED", alias="G20PRED"),
    "G20PRER": Tally("G20PRER", alias="G20PRER"),
    "democratic_won": democratic_wins,
})

print("Cut edges: ")
print(len(initial_partition["cut edges"]) )

# Define proposal and constraints
rw_proposal = partial(recom, ## how you choose a next districting plan
                      pop_col = "TOTPOP", ## What data describes population? 
                      pop_target = ideal_pop, ## What the target/ideal population is for each district 
                                             
                      epsilon = pop_tolerance,  ## how far from ideal population you can deviate
                                              
                      node_repeats = 1 ## number of times to repeat bipartition.  Can increase if you get a BipartitionWarning
                      )

population_constraint = constraints.within_percent_of_ideal_population(
    initial_partition, 
    pop_tolerance, 
    pop_key="district population")

# Creating the Markov Chain
our_random_walk = MarkovChain(
    proposal = rw_proposal, 
    constraints = [population_constraint],
    accept = always_accept, # Accept every proposed plan that meets the population constraints
    initial_state = initial_partition, 
    total_steps = 1000) 

# Lists to store data for histograms
cutedge_ensemble = []
latino_majority_ensemble = []
democratic_won_ensemble = []

# Running the Markov Chain
for part in our_random_walk:
    # Add cutedges to cutedges ensemble
    cutedge_ensemble.append(len(part["cut edges"]))

    # Calculate number of latino-majority districts 
    # Add to ensemble
    latino_majority = 0
    for i in range(num_dist):
        b_perc = part["district HISP"][i] / part["district population"][i]
        if b_perc >= 0.5:
            latino_majority = latino_majority + 1
    latino_majority_ensemble.append(latino_majority)
    
    democratic_won_ensemble.append(part["democratic_won"])


plt.figure()
plt.hist(cutedge_ensemble, align = 'left')
plt.title("Histogram of Cut Edges")
plt.show()
plt.savefig('histogram_cut_edges.png')

plt.figure()
bins = range(7)
plt.hist(latino_majority_ensemble, bins = bins, align = 'left')
plt.title("Histogram of Majority Latino Districts")
plt.show()
plt.savefig('histogram_majority_latino.png')

plt.figure()
plt.hist(democratic_won_ensemble, align = 'left')
plt.title("Histogram of Democratic-won districts")
plt.show()
plt.savefig('histogram_democratic_won.png')
