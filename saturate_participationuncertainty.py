#saturate implementation with different sets of uncertain people who may not show up
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
import random 
import math

total_nodes = 200 # changeable

adj = {}

key_list = []

for i in range(0,total_nodes):
	key_list.append(i)
	
for e in key_list:
	#for each element
	#generate a random no. of neighbours
	num_ngh = random.randint(1,4)
	#generate a possible neighbour set
	possible_neighbours = random.sample(key_list,num_ngh)
	ngh = [x for x in possible_neighbours if x != e]
	adj[e] = ngh
	
#now generate a couple of subsets to add to uncertainty sets

uncertainty_sets = []

#use only if sampling lesser number of nodes
#all_sets = random.sample(key_list, 400) # 100 nodes divided into 10 sets

num_sets = int(total_nodes/10)
print('number of subsets',num_sets)
already_chosen = []
for i in range(0,num_sets):
	cur_set = []
	while len(cur_set) < 10:
		cur_ele = random.sample(key_list,1)[0]
		if cur_ele not in already_chosen:
			cur_set.append(cur_ele)
	uncertainty_sets.append(cur_set)
	
	

	


#write the definition of the submodular function
#input a current set of monitors and an uncertainty set
# precovered is data not decision variable
#return: f(monitored/no_shows) 
def objective(seed_set, uncertainty_set,pre_covered):
	sum = 0
	already_covered = []
	for s in seed_set:
		if s not in uncertainty_set: # if s comes
			for e in adj:
				if e not in pre_covered:
					if not(already_covered) or e not in already_covered:
						if s in adj[e]:
							sum+=1
							already_covered.append(e)
	return sum
						
	

#print(objective([0,9,44,26,3,2],adjacency_lists[2]))

#write the definition of the truncated submodular function
def trunc_obj(seed_set,c,uncertainty_sets,pre_covered):
	#print('in trunc_obj, current seedset',seed_set)
	sum = 0
	for uncertainty_set in uncertainty_sets:
		objval = objective(seed_set,uncertainty_set,pre_covered)
		st = c
		if objval < c:
			st = objval
		sum+=st
	return sum/(len(uncertainty_sets))
	
def GPC(c,pre_covered):
	a = []
	prev_comp_val = 0
	comp_val = 100
	while trunc_obj(a,c,uncertainty_sets,pre_covered) < c and comp_val >0.0001:
		prev_comp_val = comp_val
		max_delta = 0
		max_node = 0
		max_flag = 1
		new_list = deepcopy(a)
		for e in key_list:
			if e not in new_list:
				new_list.append(e) 		
				new_val = trunc_obj(new_list,c,uncertainty_sets,pre_covered)			
				new_list.remove(e)
				old_val =trunc_obj(a,c,uncertainty_sets,pre_covered)
				comp_val = new_val-old_val
			
				if max_flag == 1:
					max_delta = comp_val
					max_node = e
					max_flag = 0
				else:
					cur_delta = comp_val
					if cur_delta > max_delta:
						max_delta = cur_delta
						max_node = e
		a.append(max_node)
		print('current A list length', len(a))
		print('comp_val currently',comp_val)
		print('func val in GPC', trunc_obj(a,c,uncertainty_sets,pre_covered))
	return a
			
#print(GPC(1400))
			
#some of the startup constants needed:

#setting c_max
min = 0
minflag = 1
for w_list in uncertainty_sets:
	cur_obj = objective(key_list,w_list,[])
	if minflag == 1:
		min = cur_obj
		minflag = 0
	else:
		if cur_obj < min:
			min = cur_obj
		
c_max = min

# #setting alpha
# alpha_max = 0
# maxflag = 1
# for ele in key_list:
	# ele_sum = 0
	# e_list = [ele]
	# for w_list in adjacency_lists:
		# ele_sum += objective(e_list,w_list)
	# if maxflag == 1:
		# maxflag = 0
		# alpha_max = ele_sum
	# else:
		# if alpha_max < ele_sum:
			# alpha_max = ele_sum
# alpha = 1+math.log(alpha_max)

#print(c_max,alpha)

#set K = budget
k = 30
#main binary search routine
c_min = 0
#c_max already set
best_seed = []
while c_max - c_min >= 5:
	print('diff' ,c_max-c_min)
	c = (c_max+c_min)/2
	print('current c', c)
	cur_seed = GPC(c,[])
	print('cur_seed', cur_seed,'size',len(cur_seed))
	if len(cur_seed) > k:
		c_max = c
	else:
		c_min = c
		best_seed = cur_seed
		
print(best_seed,len(best_seed))
	
cov = []
sum = 0
for e in best_seed:
	for ele in adj:
		if ele not in cov:
			if e in adj[ele]:
				sum+=1
				cov.append(ele)
print('coverage', sum/total_nodes)
		
		
		