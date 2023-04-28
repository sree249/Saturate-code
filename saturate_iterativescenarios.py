#Iterative scenario generation - integrated with saturate.
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

import math
total_nodes = 100 # changeable
k = 10 #budget of how many invitees per round
alpha = 0.3 #participation rate
total_sets = 1 #5 #initial number of sets to be generated
NUM_TOTAL_SETS = 10
num_iterations = 10
num_training_sessions = 1
beta = .3 #beta is the % for new set generation
num_noshows = int((1-alpha)*k)
total_uncertainty_sets = 5 #50

start = t.time()

adj = {}

key_list = []

file = open("sim_graph_sbm_directed_fortest.txt","r")

all_lines = file.readlines()

for line in all_lines:
	line= line.replace("\n","")
	data = line.split(":")
	node = int(data[0])
	ngh = [int(x) for x in data[1].split(",")]
	adj[node] = ngh
for e in adj.keys():
	key_list.append(e)
	
#define a helper function to compute a number of subsets
#list is the place from where we make the subsets
#k is the number of subsets you need
# def make_subsets(list,k,size):
	# set_counter = 0
	# all_subsets = []
	# while set_counter < k:
		# possible_subset = random.sample(list,size)
		# #check that the subset is not identical to any list in the subsets
		# # for e in all_subsets:
			# # intersection = set(possible_subset).intersection.set(e)
			# # if len(intersection) < size: # all the elements are not same
		# all_subsets.append(possible_subset)
		# set_counter+=1
	# return all_subsets
	
	
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
	
def adv_oracle1(budget,adj,key_list,cur_invitees, cur_set):
	m = gp.Model('Moniter selection no time dependency')
	
	# #binary variable for each of the nodes in the network
	# #x_i = {1 , if i is a monitor otherwise 0}
	
	x = []
	for i in range(0, len(cur_invitees)):
		x.append(m.addVar(vtype = gp.GRB.BINARY, name = 'x_' + str(i)))
		
	#coverage
	y = []
	for i in range(0,len(key_list)):
		y.append(m.addVar(vtype = gp.GRB.BINARY, name = 'y_' + str(i)))
		
		
	m.update()

	for i in range(0,len(cur_invitees)):
		x[i] = x[i]*cur_set[cur_invitees[i]]
	#add budget constraint - total no. of monitors <= alphaK #alpha participation rate
	
	m.addConstr(gp.quicksum(x)>=budget)

	#coverage constraint
	for i in range(0,len(key_list)):
		if key_list[i] in adj:
			ngh = adj[key_list[i]]
			for n in ngh:
				m.addConstr(y[i] >= x[cur_invitees.index(n)]*cur_set[n])
				
			
		
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
				monitors.append(cur_invitees[monitor_index])
		if v.varName[0] == 'y':
			if v.x == 1:
				sum_covered +=1
				v_data = v.varName.split("_")
				covered_index = int(v_data[1])
				covered_nodes.append(cur_keylist[covered_index])
				
				
	return [monitors,sum_covered,covered_nodes]



# #initial test for adv_oracle
# budget = int(alpha*k)
# cur_set = random.sample(key_list,k)
# results = adv_oracle(budget,adj,key_list,cur_set)
# print('currently chosen set', cur_set)
# #print(results[0],len(results[0]))
# #check = list(set(cur_set).intersection(set(results[0])))
# #print(check)
# print(set(results[0])== set(check))

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
def objective(adj_cur,seed_set, uncertainty_set,pre_covered):
	sum = 0
	already_covered = []
	for s in seed_set:
		if s not in uncertainty_set: # if s comes
			for e in adj_cur:
				if e not in pre_covered:
					if not(already_covered) or e not in already_covered:
						if s in adj_cur[e]:
							sum+=1
							already_covered.append(e)
	return sum
	
# def objective(adj_cur, seed_set, uncertainty_set, pre_covered):
	# sum = 0
	# already_covered = set()
	
	# for e in adj_cur:
		# for s in seed_set:
			# if s not in uncertainty_set:
				# if s in adj_cur[e]:
					# sum += 1
					# already_covered.add(e)
					
	# return sum
						 
	

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
		if len(new_list) < len(invitees_list_cur) : #check that there are elements possible to be added
			
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
				print('length of current queue is', len(myqueue.queue))
				print(myqueue.queue)
				if len(myqueue.queue) == 0:
					exit_flag = 1					
				elif len(myqueue.queue) == 1:
					print('came here')
					max_node = myqueue.queue[0][1]
					max_delta = myqueue.queue[0][0]
				else:
					print('I AM STUCK')
					print((myqueue.queue))
					# if this is not the 1st pass
					#get the marginal of the current top element
					cur_top = myqueue.get()
					#recalculate the marginal of it
					new_list.append(cur_top[1])
					marginal_value = -(trunc_obj(adj_cur,new_list,c,sets,pre_covered)-obj_val) #negate since its a min-heap
					new_list.remove(cur_top[1])
					next_top = myqueue.get()
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
				if max_node not in a:
					a.append(max_node) 
					obj_val = trunc_obj(adj_cur,a,c,sets,pre_covered)
				else:
					exit_flag = 1
			else:
				exit_flag = 1 # this means that all the nodes are already covered in A
				
			
			print('current A list length', len(a), 'cur a is', a)
			#print('comp_val currently',comp_val)
			print('func val in GPC', obj_val)
		else:
			exit_flag == 1
		
	return a
			
#print(GPC(1400))

'''
	the helper function below is useful in the case -
	where we have nodes which can be potential invitees
	basically a set of those who cover nodes, no point in going
	over nodes that dont cover any nodes.
'''

def create_invitees_list(possible_adj):
	invitees = []
	for e in possible_adj:
		ngh = possible_adj[e]
		for n in ngh: 
				if n not in invitees: # if it has already not been added
					invitees.append(n)
	
		
	return invitees

#initially run for just single phase
#preliminary setup
#some of the startup constants needed:
prev_covered = []
total_nodes_covered = []
stage_wise_coverage = [] #nodes covered stagewise
final_seeds = []
num_trainings = 0
best_seeds=[]
stage_wise_best_seeds = []
final_seeds=[] # based on random simulation those who do not show up

cur_adj = adj # initially we use the full constructed graph
cur_keylist = key_list # initially we take in the full key_list
cur_invitees = create_invitees_list(cur_adj)


#now generate a couple of subsets to add to uncertainty sets

uncertainty_sets = []

#use only if sampling lesser number of nodes
#all_sets = random.sample(key_list, 400) # 100 nodes divided into 10 sets

num_sets = len(cur_invitees)//num_noshows + 1
if num_sets < total_sets:
	
	print('non overlapping subsets',num_sets)
	counter = 0
	already_chosen = []
	flag = 0
	for i in range(0,total_sets):
		cur_set = []
	 
		while len(cur_set) < num_noshows and not(flag):
			cur_ele = random.sample(cur_invitees,1)[0]
		
			cur_set.append(cur_ele)
		
		
		uncertainty_sets.append(cur_set)
		counter+=1 #keep track of how many sets have been formed
		
	# we want around 20 subsets 
	#augment random subsets to the uncertainty set
	#new_sets = make_subsets(cur_invitees,total_sets - len(uncertainty_sets),num_noshows)
	#for e in new_sets:
		#uncertainty_sets.append(e)
else:
	num_sets = total_sets
	print('non overlapping subsets',num_sets)
	counter = 0
	already_chosen = []
	flag = 0
	for i in range(0,num_sets):
		cur_set = []
	 
		while len(cur_set) < num_noshows and not(flag):
			cur_ele = random.sample(cur_invitees,1)[0]
		
			cur_set.append(cur_ele)
		
		
		uncertainty_sets.append(cur_set)
		counter+=1 #keep track of how many sets have been formed
		
cur_uncertainty_sets = uncertainty_sets # initialize the uncertainty sets
print('total number of uncertainty sets', len(cur_uncertainty_sets))
		
while num_trainings < num_training_sessions and len(total_nodes_covered) != len(key_list):
	print('------------------------------------------------------')
	print('result for stage:',num_trainings+1)
	best_seed = []
	
	#main binary search routine
	if len(cur_invitees) > k:
		c_opt = 0 #the optimal value of c obtained
		end_flag = False
		while len(cur_uncertainty_sets) < total_uncertainty_sets and end_flag == False:
			
			c_min = 0
			c_max =  len(cur_invitees) # the best thing to do is to invite everyone in the network. 
			binary_flag = False
			
			#search of an optimal solution using current uncertainty sets
			while c_max-c_min>=0.5 and not(binary_flag):#c_max - c_min>=0.005:
				print('diff' ,c_max-c_min)
				c = (c_max+c_min)/2
				print('current c', c)
				cur_seed = GPC(cur_invitees,cur_adj,cur_uncertainty_sets,c,prev_covered)
				print('cur_seed', cur_seed,'size',len(cur_seed))
			
				if len(cur_seed) > k:
					c_max = c
				else:
					c_min = c
					best_seed = cur_seed
					if len(best_seed) == k:
						binary_flag = True
			
			#append a new uncertainty set based on the uncertainty set
			budget = math.ceil(alpha*len(best_seed))
			cur_set = {}
			for b in cur_invitees:
				if b in best_seed:
					cur_set[b] = 1
				else:
					cur_set[b] = 0
			output = adv_oracle(budget,cur_adj,cur_keylist,best_seed)
			new_set = output[0]
			no_shows = list(set(best_seed).difference(set(new_set)))
			cur_uncertainty_sets.append(no_shows)
			
			c = (c_max+c_min)/2
			print('comparator',output[1])
			print('c',c)
			#termination condition
			if output[1] >= c:
				end_flag = True
						
				
			
	else:
		best_seed = cur_invitees
		
	print('----------stage:',num_trainings+1,'results are:','--------')
	print('current best seed is', best_seed,len(best_seed))
	print('final uncertainty set', cur_uncertainty_sets, len(cur_uncertainty_sets))
	for e in cur_uncertainty_sets:
		print(len(e))
	print('------------------------------------------------------------')
	
	best_seeds.append(best_seed)
	b_cov = []
	for e in best_seed:
		for ele in cur_adj:
			if ele not in b_cov:
				if e in cur_adj[ele]:
					#sum+=1
					b_cov.append(ele)
	print('best seed cov', len(b_cov))
	stage_wise_best_seeds.append(len(best_seed))
	
	#final seed is the worst case realization from the current uncertainty set
	worst_case = adv_oracle(math.ceil(alpha*len(best_seed)),cur_adj,cur_keylist,best_seed)


	
	cov = worst_case[2]
	sum = worst_case[1]
	final_seed = worst_case[0]
	final_seeds.append(final_seed)
	
	
				
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
		
		cur_invitees = create_invitees_list(new_adj)

		# tracking progress
		print('--------------------------newly constructed adj for stage:',num_trainings+2)
		print('new adj ',new_adj)
		
		print('the corresonding key_lists',new_key_list,'with length',len(new_key_list))
		print(len(cur_invitees))
		print('cur_invitees', cur_invitees)
		print('-----------------------------------------------------------------------------------------------------------')
		

		if len(cur_invitees) > k:
			#build the uncertainty sets based on the new adj
			num_new_sets = len(cur_invitees)//num_noshows + 1
			print('In stage:', num_trainings+2,'the new num of sets are',num_new_sets)
			uncertainty_sets = []
			
			if num_new_sets < total_sets:

				new_counter = 0
				new_already_chosen = []
				new_flag = 0
				for i in range(0,total_sets):
					cur_set = []
					print('DEBUG...................')
					while len(cur_set) < num_noshows and not(flag):
						cur_ele = random.sample(cur_invitees,1)[0]
		
						cur_set.append(cur_ele)
	
					uncertainty_sets.append(cur_set)
					counter+=1 #keep track of how many sets have been formed
	
				# we want around 20 subsets 
				#augment random subsets to the uncertainty set
				#new_sets = make_subsets(cur_invitees,total_sets - len(uncertainty_sets),num_noshows)
				#for e in new_sets:
					#uncertainty_sets.append(e)
			else:
				print('IN THE ELSE CASE : DEBUG')
				num_new_sets = total_sets
		
				new_counter = 0
				new_already_chosen = []
				new_flag = 0
				for i in range(0,num_new_sets):
					cur_set = []
 
					while len(cur_set) < num_noshows: #and not(flag):
						cur_ele = random.sample(cur_invitees,1)[0]
		
						cur_set.append(cur_ele)
	
	
					uncertainty_sets.append(cur_set)
					counter+=1 #keep track of how many sets have been formed
					print('IN ELSE:', i)
	

			cur_uncertainty_sets = uncertainty_sets # initialize the uncertainty sets
		cur_keylist = new_key_list
		cur_adj = new_adj
	


	num_trainings+=1 # increase the number of trainings
	print('---------------------------------------------------------------------------')

all_invited_nodes = []
for e in final_seeds:
	for invitee in e:
		all_invited_nodes.append(invitee)
budget = int(alpha*len(all_invited_nodes))
final_worst_case = adv_oracle(budget,adj,key_list,all_invited_nodes)
print('worst case coverage', final_worst_case)
print('total nodes:', len(total_nodes_covered))
print('stage-wise-coverage', stage_wise_coverage)
print('stage-wise-best-seeds',best_seeds)
print('length of best seeds in each stage', stage_wise_best_seeds)
print('finally chosen for coverage', final_seeds)

end = t.time()

print('total time taken', (end-start)/3600)
