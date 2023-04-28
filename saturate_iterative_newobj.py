#Iterative scenario generation - integrated with saturate.
#rewriting the objective function to match Phebe's definition of scenario
#initial imports
import numpy as np
import gurobipy as gp
#import matplotlib.pyplot as plt
from copy import deepcopy
import random 
import math
import csv
import queue as q
import time as t

total_nodes = 100 # changeable
k = 25 #budget of how many invitees per round
alpha = 0.3 #participation rate
num_noshows = int(alpha*k) #changeable
total_sets = 5 #initial number of sets to be generated
NUM_TOTAL_SETS = 5
num_iterations = 10
num_training_sessions = 4
total_scenarios = 15
beta = .3 #beta is the % for new set generation
num_noshows = int((1-alpha)*k)

start = t.time()

adj = {}

key_list = []

file = open("sim_graph_100_med.txt","r")

all_lines = file.readlines()

for line in all_lines:
	line= line.replace("\n","")
	data = line.split(":")
	node = int(data[0])
	ngh = [int(x) for x in data[1].split(",")]
	adj[node] = ngh
for e in adj.keys():
	key_list.append(e)
	
'''
	budget is basically ceil(ak) size of no shows
	adj is used to find the neighbours of the node that can cover it
	key_list = adj.keys() list of nodes to be covered in this round
	cur_set = defender's current choice of invitees 
'''	

def adv_oracle(budget,adj,key_list, cur_set):
	m = gp.Model('Moniter selection no time dependency')
	
	# #binary variable for each of the nodes in the network
	# #x_i = {1 , if i is a monitor otherwise 0}
	
	x = []
	for i in range(0, len(cur_set)):
		x.append(m.addVar(vtype = gp.GRB.BINARY, name = 'x_' + str(i)))
		
	#coverage
	y = []
	for i in range(0,len(key_list)):
		y.append(m.addVar(vtype = gp.GRB.BINARY, name = 'y_' + str(i)))
		
		
	m.update()

	
	#add budget constraint - total no. of monitors <= alphaK #alpha participation rate
	
	m.addConstr(gp.quicksum(x)>=budget)

	#coverage constraint
	for i in range(0,len(key_list)):
		if key_list[i] in adj:
			n = adj[key_list[i]]
			#find if the current node has some neighbours that are in cur_set
			common_ngh = list(set(n).intersection(set(cur_set)))
			x_list = []
			if len(common_ngh) > 0:
				for value in common_ngh:
					x_list.append(x[cur_set.index(value)]) #find the corresponding decision variable
					m.addConstr(y[i] >= x[cur_set.index(value)])
				#m.addConstr(y[i] <= gp.quicksum(x_list))
			else:
				y[i] == 0 # the node is not currently covered
		
	m.setObjective(gp.quicksum(y), gp.GRB.MINIMIZE)
	
	m.optimize()
	
	monitors = []
	covered_nodes = []
	sum_covered = 0
	for v in m.getVars():
		if v.varName[0] == 'x':
			if v.x == 1:
				v_data = v.varName.split("_")
				monitor_index = int(v_data[1])
				monitors.append(cur_set[monitor_index])
		if v.varName[0] == 'y':
			if v.x == 1:
				sum_covered +=1
				v_data = v.varName.split("_")
				covered_index = int(v_data[1])
				covered_nodes.append(key_list[covered_index])
				
				
	return [monitors,sum_covered,covered_nodes]

#generate some initial scenarios

def create_invitees_list(possible_adj):
	invitees = []
	for e in possible_adj:
		ngh = possible_adj[e]
		for n in ngh: 
				if n not in invitees: # if it has already not been added
					invitees.append(n)
	
		
	return invitees

#generate random NUM_TOTAL_SETS scenarios
#A scenario is dict {'key' = node, value = '1 if it comes 0 otherwise'}

def generate_scenarios(cur_adj,cur_keylist,total_sets,invitee_length):
	invitees = create_invitees_list(cur_adj)
	scenarios = []
	counter = 0
	while counter < total_sets:
		cur_scenario = {}
		shows = random.sample(invitees,int(alpha*invitee_length))
		for e in invitees:
			if e in shows:
				cur_scenario[e] = 1
			else:
				cur_scenario[e] = 0
		scenarios.append(cur_scenario)
		counter+=1
	return scenarios
	
# #print(ini_scenarios)
# invitees = create_invitees_list(adj)

# res = def_oracle(20,invitees,adj,key_list,ini_scenarios)

def create_new_scenario(cur_invitees,shows):
	new_scenario = {}
	for e in cur_invitees:
		if e in shows:
			new_scenario[e] = 1
		else:
			new_scenario[e] = 0
	return new_scenario

#---------------------------Helpers for saturate-----------------------------------------------#
# given a node we want to calculate how many nodes it covers
def calc_coverage(adj,node):
	count = 0
	for e in adj:
		ngh = adj[e]
		if node in ngh:
			count+=1
	return count
#write the definition of the submodular function
#input a current set of monitors and an uncertainty set
#also takes in an adj since for extending to multi stage we need to make it variable
# precovered is data not decision variable
#return: f(monitored/no_shows) 
#scenario is a set <ele:0,ele1:1,...> where 1 means the node is in attendance, 0 means otherwise
def objective(adj_cur,seed_set,scenario,pre_covered):
	sum = 0
	already_covered = []
	for s in seed_set:
		if scenario[s] == 1: # if s comes
			for e in adj_cur:
				if e not in pre_covered:
					if not(already_covered) or e not in already_covered:
						if s in adj_cur[e]:
							sum+=1
							already_covered.append(e)
	return sum
						 
	

#print(objective([0,9,44,26,3,2],adjacency_lists[2]))

#write the definition of the truncated submodular function
def trunc_obj(adj_cur,seed_set,c,sets,pre_covered):
	#print('in trunc_obj, current seedset',seed_set)
	sum = 0
	for uncertainty_set in sets:
		objval = objective(adj_cur,seed_set,uncertainty_set,pre_covered)
		st = c
		if objval < c:
			st = objval
		sum+=st
	return sum/(len(sets))
	
def GPC(invitees_list_cur,adj_cur,sets,c,pre_covered):
	a = []
	obj_val = trunc_obj(adj_cur,a,c,sets,pre_covered)
	myqueue = q.PriorityQueue()
	max_delta = -1
	max_node = -1
	max_flag = 1
	exit_flag = 0
	while obj_val < c and not(exit_flag): #and comp_val > 0:
		new_list = deepcopy(a)
		if len(new_list) < len(invitees_list_cur): #check that there are elements possible to be added
			
			if max_flag == 1: #this is the 1st pass
				print('First pass results')
				for e in invitees_list_cur:
					if e not in new_list:
						new_list.append(e)
						marginal_value = -(trunc_obj(adj_cur,new_list,c,sets,pre_covered)-obj_val) #negate since its a min-heap
						myqueue.put((marginal_value,e))
						new_list.remove(e)
				max_flag = 0
				
				#print('--------After the 1st pass the resulting order is-------------')
				#print(myqueue.queue)
				top_node = myqueue.get()
				max_node = top_node[1]	#the top is the maximum,second element is our node
				max_delta = -top_node[0]
			else:
				#print('in the celf optimization part')
				# if this is not the 1st pass
				#get the marginal of the current top element
				cur_top = myqueue.get()
				#print('current top element:',cur_top)
				#recalculate the marginal of it
				new_list.append(cur_top[1])
				marginal_value = -(trunc_obj(adj_cur,new_list,c,sets,pre_covered)-obj_val) #negate since its a min-heap
				new_list.remove(cur_top[1])
				next_top = myqueue.get()
				#print('next top is:',next_top)
				#print('next value marginal', next_top[0])
				#print('cur top marginal',marginal_value)
				#check if the next element has a greater (negated) marginal values
				if next_top[0] > marginal_value:
					print('not to recompute, current readdition is',cur_top[1])
					max_node = cur_top[1]
					max_delta = -cur_top[0]
				else:
					#print('need to recompute the entire heap')
					#recompute all the marginals and reheapify
					rem_elements = list(set(invitees_list_cur).difference(set(new_list)))
					myqueue.queue.clear()
					print(rem_elements)
					for e in rem_elements:
						if e not in new_list:
							new_list.append(e)
							marginal_value = -(trunc_obj(adj_cur,new_list,c,sets,pre_covered)-obj_val) #negate since its a min-heap
							myqueue.put((marginal_value,e))
							new_list.remove(e)
					#print('printing heap')
					#print(myqueue.queue)
					max_node = myqueue.get()[1]	#the top is the maximum,second element is our node
					max_delta = -cur_top[0]
			if max_delta > 0: #there is actually a marginal increase in the top element
				a.append(max_node) 
				obj_val = trunc_obj(adj_cur,a,c,sets,pre_covered)
			else:
				exit_flag = 1 # this means that all the nodes are already covered in A
				
			
			print('current A list length', len(a), 'cur a is', a)
			#print('comp_val currently',comp_val)
			print('func val in GPC', obj_val)
		else:
			exit_flag == 1
		
	return a
	
#preliminary setup
#some of the startup constants needed:
total_nodes_covered = []
stage_wise_coverage = [] #nodes covered stagewise
final_seeds = []
num_trainings = 0
best_seeds=[]
stage_wise_best_seeds = []
final_seeds=[] # based on random simulation those who do not show up
stagewise_len_scenarios = []

cur_adj = adj # initially we use the full constructed graph
cur_keylist = key_list # initially we take in the full key_list
cur_invitees = create_invitees_list(cur_adj)

prev_covered = []

while num_trainings < num_training_sessions and len(total_nodes_covered) != len(key_list):
	#generate some initial scenarios
	ini_scenarios = generate_scenarios(cur_adj,cur_keylist,NUM_TOTAL_SETS,k)
	best_seed = []
	final_seed = []
	end_flag = False
	if len(cur_invitees) > k:
		while len(ini_scenarios)< total_scenarios:
			c_min = 0
			c_max =  len(cur_invitees) # the best thing to do is to invite everyone in the network. 
			binary_flag = False
			
			#search of an optimal solution using current uncertainty sets
			while c_max-c_min>=0.5 and not(binary_flag):#c_max - c_min>=0.005:
				print('diff' ,c_max-c_min)
				c = (c_max+c_min)/2
				print('current c', c)
				cur_seed = GPC(cur_invitees,cur_adj,ini_scenarios,c,prev_covered)
				print('cur_seed', cur_seed,'size',len(cur_seed))
			
				if len(cur_seed) > k:
					c_max = c
				else:
					c_min = c
					best_seed = cur_seed
					if len(best_seed) == k:
						binary_flag = True
			
			c = (c_max+c_min)/2
			
		
			#append a new uncertainty set based on the uncertainty set
			budget = int(alpha*len(best_seed))
			output = adv_oracle(budget,cur_adj,cur_keylist,best_seed)
			new_set = output[0]
			#no_shows = list(set(best_seed).difference(set(new_set)))
			finally_cov = output[1]
			#create a new scenario
			new_scenario = create_new_scenario(cur_invitees,new_set)
			ini_scenarios.append(new_scenario)
		
			if finally_cov > c:
				end_flag = True
	else:
		best_seed = cur_invitees
			
	stagewise_len_scenarios.append(len(ini_scenarios))
	best_seeds.append(best_seed)
	
	print('----------stage:',num_trainings+1,'results are:','--------')
	print('current best seed is', best_seed,len(best_seed))
	
	best_seeds.append(best_seed)
	stage_wise_best_seeds.append(len(best_seed))
	
	#final seed is the worst case realization from the current uncertainty set
	worst_case = adv_oracle(int(alpha*len(best_seed)),cur_adj,cur_keylist,best_seed)
	
	
	print(worst_case)
	
	cov = worst_case[2]
	sum = worst_case[1]
	final_seed = worst_case[0]
	final_seeds.append(final_seed)
	
	print('stage ',num_trainings+1,' coverage ',sum)
	stage_wise_coverage.append(sum)
	
	#keep a track of all the nodes covered so far
	for e in cov:
		if not(total_nodes_covered) or e not in total_nodes_covered:
			total_nodes_covered.append(e)
			
	if num_trainings + 1 < num_training_sessions and len(total_nodes_covered)< len(key_list):
	
		'''
			After finishing a stage we do the following:
			(a) Reconstruct the adj using information from the previous stage:
				(i) The covered nodes cannot be keys in the adj.
				(ii) For neighbours: chosen best seeds cannot be present.
					- we will not want to send invitations to those who came
					- we assume those we invite will show up.
			
			(b) for this we only need to keep information about previous stage.
		
		'''



		new_adj = {}

		for e in cur_keylist:
			if e not in cov: 
				prev_ngh = cur_adj[e]
				new_ngh = []
				for prev_n in prev_ngh:
					if prev_n not in final_seed: #extra check not needed since covered[final_seed] are removed.
						new_ngh.append(prev_n)
				new_adj[e] = new_ngh
		
		
		# build the new key_list
		new_key_list = []
		for e in new_adj:
			new_key_list.append(e)
		
		

		# tracking progress
		print('--------------------------newly constructed adj for stage:',num_trainings+2)
		print('new adj ',new_adj)
		
		print('the corresonding key_lists',new_key_list,'with length',len(new_key_list))

		print('-----------------------------------------------------------------------------------------------------------')
	
		cur_keylist = new_key_list
		cur_adj = new_adj
		cur_invitees = create_invitees_list(new_adj)
		
	num_trainings+=1 # increase the number of trainings
	print('---------------------------------------------------------------------------')
		
all_invited_nodes = []
for e in final_seeds:
	for invitee in e:
		all_invited_nodes.append(invitee)
budget = int(alpha*len(all_invited_nodes))
final_worst_case = adv_oracle(budget,adj,key_list,all_invited_nodes)
#print('worst case coverage', final_worst_case)
print('total nodes:', len(total_nodes_covered))
print('stage-wise-coverage', stage_wise_coverage)
#print('stage-wise-best-seeds',best_seeds)
print('length of best seeds in each stage', stage_wise_best_seeds)
print('stage wise length of uncertainty sets added', stagewise_len_scenarios)

end = t.time()

print('Time taken is:',(end-start)/3600)
				

	

	
	
