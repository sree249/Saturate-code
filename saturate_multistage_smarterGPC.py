#saturate implementation with different sets of uncertain people who may not show up
import numpy as np
import gurobipy as gp
import matplotlib.pyplot as plt
from copy import deepcopy
import random 
import math
import csv
import queue as q
import time as t
	
total_nodes = 200 # changeable
k = 25 #budget of how many invitees per round
alpha = 0.7
num_noshows = int(alpha*k) #changeable
total_sets = 10 #changable
num_iterations = 10
num_training_sessions = 4

start = t.time()

adj = {}

key_list = []

file = open("sim_graph_200_med.txt","r")

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
def make_subsets(list,k,size):
	set_counter = 0
	all_subsets = []
	while set_counter < k:
		possible_subset = random.sample(list,size)
		#check that the subset is not identical to any list in the subsets
		# for e in all_subsets:
			# intersection = set(possible_subset).intersection.set(e)
			# if len(intersection) < size: # all the elements are not same
		all_subsets.append(possible_subset)
		set_counter+=1
	return all_subsets
	
	
#for i in range(0,total_nodes):
	#key_list.append(i)

'''
	code to generate graph
'''	
# for e in key_list:
	# #for each element
	# #generate a random no. of neighbours
	# num_ngh = random.randint(2,5)
	# #generate a possible neighbour set
	# possible_neighbours = random.sample(key_list,num_ngh)
	# ngh = [x for x in possible_neighbours if x != e]
	# adj[e] = ngh
	
'''
	Save graph
'''


#write the generated graph to a file
# file = open("50_graph.txt","w")

# for ele in adj:
	# file.write(str(ele))
	# file.write(':')
	# ngh = adj[ele]
	# for i in range(0,len(ngh)):
		# if i < len(ngh)-1:
			# file.write(str(ngh[i]))
			# file.write(',')
		# else:
			# file.write(str(ngh[i]))
	# file.write('\n')
	
# file.close()
	

		
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
	
#we add a new term called prev_set
#prev_set is basically the term from the past iteration
#the idea is -
#(1)when nextc < c, prev_set has to reduced by removing one element at a time till it reaches nextc
#(2)when nextc > c, prev_set has to be increased greedily till it reaches nextc
#method - 
#set a = prev_set
#get the trunc_obj value - if it is greater than cur c it is case 1
#else case 2
def GPC(invitees_list_cur,adj_cur,sets,c,pre_covered,prev_set):
	a = prev_set
	obj_val = trunc_obj(adj_cur,a,c,sets,pre_covered)
	myqueue = q.PriorityQueue()
	max_delta = -1
	max_node = -1
	max_flag = 1
	exit_flag = 0
	if obj_val > c: #case (1)
		index = len(a)-1
		while obj_val > c and index > 0:
			a.remove(index) # remove a value from the back
			obj_val = trunc_obj(adj_cur,a,c,sets,pre_covered)
			index-=1
	else:			
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
	
	
sim_avg	= 0
sim_total_nodes = []	
for sim in range(0,num_iterations):
	print('--------------------------------------------------')
	print('current simulation no', sim)
	#some of the startup constants needed:
	prev_covered = []
	total_nodes_covered = []
	stage_wise_coverage = [] #nodes covered stagewise
	num_trainings = 0
	best_seeds=[]
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
		for i in range(0,num_sets):
			cur_set = []
	 
			while len(cur_set) < num_noshows and not(flag):
				cur_ele = random.sample(cur_invitees,1)[0]
			
				if cur_ele not in already_chosen:
					cur_set.append(cur_ele)
					already_chosen.append(cur_ele)
		
				if len(already_chosen) == len(cur_invitees):
					to_add = random.sample(cur_invitees, num_noshows - len(cur_set))
					flag = 1
		
		
			uncertainty_sets.append(cur_set)
			counter+=1 #keep track of how many sets have been formed
		
		# we want around 20 subsets 
		#augment random subsets to the uncertainty set
		new_sets = make_subsets(cur_invitees,total_sets - len(uncertainty_sets),num_noshows)
		for e in new_sets:
			uncertainty_sets.append(e)
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
			
				if cur_ele not in already_chosen:
					cur_set.append(cur_ele)
					already_chosen.append(cur_ele)
		
				if len(already_chosen) == len(cur_invitees):
					to_add = random.sample(cur_invitees, num_noshows - len(cur_set))
					flag = 1
		
		
			uncertainty_sets.append(cur_set)
			counter+=1 #keep track of how many sets have been formed
		
		
		
	
	cur_uncertainty_sets = uncertainty_sets # initialize the uncertainty sets
	print('total number of uncertainty sets', len(cur_uncertainty_sets))
	
	while num_trainings < num_training_sessions and len(total_nodes_covered) != len(key_list):
		print('------------------------------------------------------')
		print('result for stage:',num_trainings+1)
	
		if len(cur_invitees) > k:
			#main binary search routine
			c_min = 0
			c_max =  len(cur_invitees) # the best thing to do is to invite everyone in the network. 
			cur_seed = []
			best_seed = []
			binary_flag = False
			while c_max - c_min >= 0.5 and not(binary_flag):
				print('diff' ,c_max-c_min)
				c = (c_max+c_min)/2
				print('current c', c)
				cur_seed = GPC(cur_invitees,cur_adj,cur_uncertainty_sets,c,prev_covered,cur_seed)
				print('cur_seed', cur_seed,'size',len(cur_seed))
				if len(cur_seed) > k:
					c_max = c
				else:
					c_min = c
					best_seed = cur_seed
					if len(best_seed) == k:
						binary_flag = True
		
			print('best seed for stage:', num_trainings+1,' is:',best_seed, ' with length ', len(best_seed))
		
		else:
			best_seed = cur_invitees
		#append the currently chosen element to the chosen set of best seeds
		for e in best_seed:
			if not(best_seeds) or e not in best_seeds:
				best_seeds.append(e)
			
			#generate all subsets of no_shows
			all_noshows = random.sample(best_seed,int(alpha*len(best_seed)))
			#print(all_noshows)
			# min = 0
			# min_subset = all_noshows[0]
			# cur_flag = 1
			# for cur_subset in all_noshows:
				# cur_diff = objective(cur_adj,best_seed,cur_subset,[])
				# if cur_flag == 1:
					# min = cur_diff
					# min_subset = cur_subset
				# else:
					# if min > cur_diff:
						# min = cur_diff
						# min_subset = cur_subset
	
			# to find those covered we will need to know the min subset
			#those whose neighbours are not in the min subset will not be covered
		cov = []
		sum = 0
		final_seed = [x for x in best_seed if x not in all_noshows]
		print('finally based on random simulation attendees are', final_seed)
		final_seeds.append(final_seed)
	
		for e in final_seed:
			for ele in cur_adj:
				if ele not in cov:
					if e in cur_adj[ele]:
						sum+=1
						cov.append(ele)
		print('stage', num_trainings+1,'coverage', sum)
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
			print('--------------------------newly constructed adj for stage:',num_trainings+2,'------------------------------')
			print('new adj',new_adj)
			print('the corresonding key_lists', new_key_list,'with length',len(new_key_list))
			print('-----------------------------------------------------------------------------------------------------------')
	
			if len(cur_invitees) > k:
				# #build the uncertainty sets based on the new adj
				# num_new_sets = len(cur_invitees)//num_noshows + 1
		
				# #delete this part if not using fixed number of subset enumeration
				# if num_new_sets < total_sets:
					# total_sets = num_new_sets # if the number of sets we can generate is less than total_sets then that 
					
				 
				# print('number of new subsets',num_new_sets, 'for stage:', num_trainings+2)
				# new_counter = 0
				# new_already_chosen = []
				# new_flag = 0
				# new_uncertainty_sets = []
				# for i in range(0,num_new_sets):
					# cur_set = []
	 
					# while len(cur_set) < num_noshows and not(new_flag):
						# cur_ele = random.sample(cur_invitees,1)[0]
			
						# if cur_ele not in new_already_chosen:
							# cur_set.append(cur_ele)
		
						# if len(new_already_chosen) == len(cur_invitees):
							# to_add = random.sample(cur_invitees, num_noshows - len(cur_set))
							# flag = 1
		
						# new_uncertainty_sets.append(cur_set)
						# counter+=1 #keep track of how many sets have been formed
	
				cur_uncertainty_sets = uncertainty_sets
			cur_keylist = new_key_list
			cur_adj = new_adj
		
	
	
		num_trainings+=1 # increase the number of trainings
		print('---------------------------------------------------------------------------')
	sim_total_nodes.append([len(total_nodes_covered),stage_wise_coverage])
	sim_avg+=len(total_nodes_covered)
	print('----------------------------------------------------------------------------')
sim_avg = sim_avg/num_iterations
#calculate the variance
var_sum = 0
for e in sim_total_nodes:
	var_sum = (e[0]-sim_avg)*(e[0]-sim_avg)
	
var_sum = var_sum/num_iterations


print('the simulation average is', sim_avg)
print('the simulation variance is',var_sum)

end = t.time()

diff = end - start
print('hours elapsed:', diff/3600)