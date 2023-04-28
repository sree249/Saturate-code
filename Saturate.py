#Saturate algorithm simple implementation

#1st create 10 different weight configurations
import networkx as nx
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
	
adjacency_list = {}
adjacency_list_weights = {}
key_list = []

friends_of = {} # key = person, connections = [nodes they cover]
isolated = [] #nodes that do not have any nodes covering them

temp_weights = {} #initial mapping from neighbours->their connections key = (me,those whom I can cover)
for i in range(0,len(processed_data)):
	cur_line = processed_data[i]
	connections = []
	for j in range(0,len(cur_line)):
		if int(cur_line[j]) > 0:
			connections.append(j)
			temp_weights[(i,j)]=int(cur_line[j])/5 #add the weights normalized
	friends_of[i]= connections


for ele in friends_of:
	neighbour_set = []
	for ele1 in friends_of:
		cur_connections = friends_of[ele1]
		for c in cur_connections:
			if c == ele:
				neighbour_set.append(ele1) #neighbour who covers me
				adjacency_list_weights[(ele1,ele)] = temp_weights[(ele1,ele)]
	if len(neighbour_set)>0:
		adjacency_list[ele] = neighbour_set
	else:
		isolated.append(ele)
		
#remove the isolated nodes from the neighbour list of every node
for iso in isolated:
	for k in adjacency_list.keys():
		neighbour = adjacency_list[k]
		if iso in neighbour:
			neighbour.remove(iso)
			adjacency_list[k] = neighbour
			
#create the key list
key_list = []
for key in adjacency_list.keys():
	key_list.append(key)
	
#helper to get neighbours
# if 1->2 then 2 is a neighbour
#if 3-> 1 then 1 is a neighbour however 1 does not have 2 as a neighbour
def neighbours(key):
	return adjacency_list[key]
	
#we want to make 10 possible adjacency_list_weights configurations
weight_list = []
weight_list.append(adjacency_list_weights) #1st weight list is added to the list

for i in range(0,2):
	weight1 = {}
	for e in adjacency_list_weights:
		weight1[e] = random.randint(0,5)/5
	weight_list.append(weight1)
	





#write the definition of the submodular function
#input: current set of monitors(a list), a weight configurations
#returns the total coverage function as per the seed_set and the weight configurations
def objective(seed_set, cur_weights):
	sum = 0
	if seed_set: #empty list
		for e in key_list:
			ngh = neighbours(e)
			for e1 in ngh:
				if e1 in seed_set:
					sum+=cur_weights[(e1,e)]
		
	return sum
	

#print(objective([0,9,44,26,3,2],weight_list[9]))

#write the definition of the truncated submodular function
def trunc_obj(seed_set,c,weights_list):
	#print('in trunc_obj, current seedset',seed_set)
	sum = 0
	for w_list in weights_list:
		objval = objective(seed_set,w_list)
		st = c
		if objval < c:
			st = objval
		sum+=st
	return sum/(len(weights_list))
	
def GPC(c):
	a = []
	prev_comp_val = 0
	comp_val = 100
	while trunc_obj(a,c,weight_list) < c and comp_val >0:
		prev_comp_val = comp_val
		max_delta = 0
		max_node = 0
		max_flag = 1
		new_list = deepcopy(a)
		for e in key_list:
			
			new_list.append(e) 
			#print('current new list is',new_list)
			new_val = trunc_obj(new_list,c,weight_list)
			#print('current element',e,'value',new_val)
			new_list.remove(e)
			old_val =trunc_obj(a,c,weight_list)
			comp_val = new_val-old_val
			#print('current A', a,'current comp val',comp_val)
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
	return a
			
#print(GPC(667))
			
#some of the startup constants needed:

#setting c_max
min = 0
minflag = 1
for w_list in weight_list:
	cur_obj = objective(key_list,w_list)
	if minflag == 1:
		min = cur_obj
		minflag = 0
	else:
		if cur_obj < min:
			min = cur_obj
		
c_max = min

#setting alpha
alpha_max = 0
maxflag = 1
for ele in key_list:
	ele_sum = 0
	e_list = [ele]
	for w_list in weight_list:
		ele_sum += objective(e_list,w_list)
	if maxflag == 1:
		maxflag = 0
		alpha_max = ele_sum
	else:
		if alpha_max < ele_sum:
			alpha_max = ele_sum
alpha = 1+math.log(alpha_max)

print(c_max,alpha)
#set K = budget
k = 20
#main binary search routine
c_min = 0
#c_max already set
best_seed = []
while c_max - c_min >= 1/len(weight_list):
	print('diff' ,c_max-c_min)
	c = (c_max+c_min)/2
	print('current c', c)
	cur_seed = GPC(c)
	print('cur_seed', cur_seed,'size',len(cur_seed))
	if len(cur_seed) > k:
		c_max = c
	else:
		c_min = c
		best_seed = cur_seed
		
print(best_seed)
	
		
		
		