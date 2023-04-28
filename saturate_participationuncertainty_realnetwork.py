#saturate implementation with different sets of uncertain people who may not show up
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
import random 
import math

#some preprocessing to create the adjacency matrix and adjacency list
file = open("social_network_dataset.txt", "r")
data = file.readlines()
processed_data = []

#1st read in the data
for line in data:
	cur_line = line.split()
	processed_data.append(cur_line)
	
adj = {}
#adjacency_list_weights = {}
key_list = []

friends_of = {} # key = person, connections = [nodes they cover]
isolated = [] #nodes that do not have any nodes covering them

for i in range(0,len(processed_data)):
	cur_line = processed_data[i]
	connections = []
	for j in range(0,len(cur_line)):
		if int(cur_line[j]) > 0:
			connections.append(j)
			#adjacency_list_weights[(j,i)]=int(cur_line[j])/5 #add the weights normalized
	friends_of[i]= connections
	
for ele in friends_of:
	neighbour_set = []
	for ele1 in friends_of:
		cur_connections = friends_of[ele1]
		for c in cur_connections:
			if c == ele:
				neighbour_set.append(ele1) #neighbour who covers me
			
	if len(neighbour_set)>0:
		adj[ele] = neighbour_set
	else:
		isolated.append(ele)
		
#remove the isolated nodes from the neighbour list of every node
for iso in isolated:
	for k in adj.keys():
		neighbour = adj[k]
		if iso in neighbour:
			neighbour.remove(iso)
			adj[k] = neighbour
			
#create the key list
key_list = []
for key in adj.keys():
	key_list.append(key)
	
def neighbours(key):
	return adj[key]
	
#now generate a couple of subsets to add to uncertainty sets

uncertainty_sets = []

#use only if sampling lesser number of nodes
#all_sets = random.sample(key_list, 400) # 100 nodes divided into 10 sets
total_nodes = len(key_list)
num_sets = total_nodes//10 + 1 #integer number of sets
print('number of subsets',num_sets)
counter = 0
already_chosen = []
flag = 0
for i in range(0,num_sets):
	cur_set = []
	 
	while len(cur_set) < 10 and not(flag):
		cur_ele = random.sample(key_list,1)[0]
			
		if cur_ele not in already_chosen:
			cur_set.append(cur_ele)
		
		if len(already_chosen) == len(key_list):
			to_add = random.sample(key_list, 10 - len(cur_set))
			flag = 1
		
		
	uncertainty_sets.append(cur_set)
	counter+=1 #keep track of how many sets have been formed

	


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
		
		
		