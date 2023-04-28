#saturate implementation with different sets of uncertain people who may not show up
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
import random 
import math

total_nodes = 50 # changeable
k = 5 #budget of how many invitees per round
num_noshows = int(.34*k) #changeable


adj = {}

key_list = []

for i in range(0,total_nodes):
	key_list.append(i)
	
for e in key_list:
	#for each element
	#generate a random no. of neighbours
	num_ngh = random.randint(5,10)
	#generate a possible neighbour set
	possible_neighbours = random.sample(key_list,num_ngh)
	ngh = [x for x in possible_neighbours if x != e]
	adj[e] = ngh
	

	
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
	prev_comp_val = 0
	comp_val = 100
	prev_obj = 0 
	cur_obj = 100
	exit_flag = 0
	while trunc_obj(adj_cur,a,c,sets,pre_covered) < c and not(exit_flag): #and comp_val > 0:
		prev_comp_val = comp_val
		prev_obj = trunc_obj(adj_cur,a,c,sets,pre_covered)
		max_delta = -1
		max_node = -1
		max_flag = 1
		new_list = deepcopy(a)
		if len(new_list) < len(invitees_list_cur): #check that there are elements possible to be added
			for e in invitees_list_cur:
				if e not in new_list:
					new_list.append(e) 		
					new_val = trunc_obj(adj_cur,new_list,c,sets,pre_covered)			
					new_list.remove(e)
					old_val =trunc_obj(adj_cur,a,c,sets,pre_covered)
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
			if max_delta > 0:
				a.append(max_node)
			else:
				exit_flag = 1 # this means that all the nodes are already covered in A
			print('current A list length', len(a), 'cur a is', a)
			print('comp_val currently',comp_val)
			print('func val in GPC', trunc_obj(adj_cur,a,c,sets,pre_covered))
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
	
	
			
#some of the startup constants needed:
prev_covered = []
total_nodes_covered = []
num_trainings = 0
best_seeds=[]

cur_adj = adj # initially we use the full constructed graph
cur_keylist = key_list # initially we take in the full key_list
cur_invitees = create_invitees_list(cur_adj)


#now generate a couple of subsets to add to uncertainty sets

uncertainty_sets = []

#use only if sampling lesser number of nodes
#all_sets = random.sample(key_list, 400) # 100 nodes divided into 10 sets

num_sets = len(cur_invitees)//num_noshows + 1
print('number of subsets',num_sets)
counter = 0
already_chosen = []
flag = 0
for i in range(0,num_sets):
	cur_set = []
	 
	while len(cur_set) < num_noshows and not(flag):
		cur_ele = random.sample(cur_invitees,1)[0]
			
		if cur_ele not in already_chosen:
			cur_set.append(cur_ele)
		
		if len(already_chosen) == len(cur_invitees):
			to_add = random.sample(cur_invitees, num_noshows - len(cur_set))
			flag = 1
		
		
	uncertainty_sets.append(cur_set)
	counter+=1 #keep track of how many sets have been formed
	
cur_uncertainty_sets = uncertainty_sets # initialize the uncertainty sets
	
while num_trainings < 4 and len(total_nodes_covered) != len(key_list):
	print('------------------------------------------------------')
	print('result for stage:',num_trainings+1)
	
	
	#main binary search routine
	c_min = 0
	c_max =  len(cur_invitees) # the best thing to do is to invite everyone in the network. 
	cur_best_seed = []
	while c_max - c_min >= 0.5:
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
			#if len(best_seed) == k:
				#break
		
	print('best seed for stage:', num_trainings+1,' is:',best_seed, ' with length ', len(best_seed))
	
	#append the currently chosen element to the chosen set of best seeds
	for e in best_seed:
		if not(best_seeds) or e not in best_seeds:
			best_seeds.append(e)
	
	cov = []
	sum = 0
	for e in best_seed:
		for ele in cur_adj:
			if ele not in cov:
				if e in cur_adj[ele]:
					sum+=1
					cov.append(ele)
	print('stage', num_trainings+1,'coverage', sum)
	
	
	#keep a track of all the nodes covered so far
	for e in cov:
		if not(total_nodes_covered) or e not in total_nodes_covered:
			total_nodes_covered.append(e)
	
		
	if num_trainings + 1 < 4 and len(total_nodes_covered)< len(key_list):
	
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
					if prev_n not in best_seed: #extra check not needed since covered[best_seed] are removed.
						new_ngh.append(prev_n)
				new_adj[e] = new_ngh
			
			
		# build the new key_list
		new_key_list = []
		for e in new_adj:
			new_key_list.append(e)
			
		cur_invitees = create_invitees_list(new_adj)
	
		# tracking progress
		print('--------------------------newly constructed adj for stage:',num_trainings+2,'------------------------------')
		print('new adj',new_adj)
		print('the corresonding key_lists', new_key_list,'with length',len(new_key_list))
		print('-----------------------------------------------------------------------------------------------------------')
	
			
		#build the uncertainty sets based on the new adj
		num_new_sets = len(cur_invitees)//num_noshows + 1
		
		#delete this part if not using fixed number of subset enumeration
		if num_new_sets > num_sets:
			num_new_sets = num_sets
			
		print('number of new subsets',num_new_sets, 'for stage:', num_trainings+2)
		new_counter = 0
		new_already_chosen = []
		new_flag = 0
		new_uncertainty_sets = []
		for i in range(0,num_new_sets):
			cur_set = []
	 
			while len(cur_set) < num_noshows and not(new_flag):
				cur_ele = random.sample(cur_invitees,1)[0]
			
				if cur_ele not in new_already_chosen:
					cur_set.append(cur_ele)
		
				if len(new_already_chosen) == len(cur_invitees):
					to_add = random.sample(cur_invitees, num_noshows - len(cur_set))
					flag = 1
		
			new_uncertainty_sets.append(cur_set)
			counter+=1 #keep track of how many sets have been formed
	
		cur_uncertainty_sets = new_uncertainty_sets
		cur_keylist = new_key_list
		cur_adj = new_adj
		
	
	
	num_trainings+=1 # increase the number of trainings
	print('---------------------------------------------------------------------------')