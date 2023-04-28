#Iterative scenario generation - integrated with saturate.
#initial imports
from multiprocessing import Process 
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
num_sims = 10
k = 15 #budget of how many invitees per round
alpha = 0.3 #participation rate
#num_noshows = int(alpha*k) #changeable
total_sets = 5 #initial number of sets to be generated
NUM_TOTAL_SETS = 10
num_training_sessions = 4
num_noshows = int((1-alpha)*k)
num_uncertainty_sets = 30

start = t.time()

#------------------------------------------- VARIOUS HELPERS --------------------------------------#
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
	
def GPC(invitees_list_cur,adj_cur,sets,c,pre_covered,sim_no):
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
				top_node = myqueue.get()
				max_node = top_node[1]	#the top is the maximum,second element is our node
				max_delta = -top_node[0]
			else:
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
					max_node = myqueue.get()[1]	#the top is the maximum,second element is our node
					max_delta = -cur_top[0]
			if max_delta > 0: #there is actually a marginal increase in the top element
				a.append(max_node) 
				obj_val = trunc_obj(adj_cur,a,c,sets,pre_covered)
			else:
				exit_flag = 1 # this means that all the nodes are already covered in A
				
			
			print('In sim no',sim_no,'current A list length', len(a), 'cur a is', a)
			print('In sim no',sim_no,'func val in GPC', obj_val)
		else:
			exit_flag == 1
		
	return a
	
def create_invitees_list(possible_adj):
	invitees = []
	for e in possible_adj:
		ngh = possible_adj[e]
		for n in ngh: 
				if n not in invitees: # if it has already not been added
					invitees.append(n)
	
		
	return invitees
	
	
def run_simulation(adj,key_list,type,sim_no,alpha):
	#open_file to write details of simulation
	#construct file_name 
	file_name = "sim_results_"+str(type)+"_"+str(alpha)+"_"+str(sim_no)+".txt"
	file_handle = open(file_name,"w")
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
	print('In sim', sim_no,'total number of uncertainty sets', len(cur_uncertainty_sets))
		
	while num_trainings < num_training_sessions and len(total_nodes_covered) != len(key_list):
		print('------------------------------------------------------')
		print('In sim no',sim_no,'result for stage:',num_trainings+1)
		best_seed = []
	
		#main binary search routine
		if len(cur_invitees) > k:
	
			while(len(cur_uncertainty_sets) < ):
			
				c_min = 0
				c_max =  len(cur_invitees) # the best thing to do is to invite everyone in the network. 
				binary_flag = False
			
				#search of an optimal solution using current uncertainty sets
				while c_max-c_min>=0.5 and not(binary_flag):#c_max - c_min>=0.005:
					print('diff' ,c_max-c_min)
					c = (c_max+c_min)/2
					print('current c', c)
					cur_seed = GPC(cur_invitees,cur_adj,cur_uncertainty_sets,c,prev_covered,sim_no)
					print('cur_seed', cur_seed,'size',len(cur_seed))
			
					if len(cur_seed) > k:
						c_max = c
					else:
						c_min = c
						best_seed = cur_seed
						if len(best_seed) == k:
							binary_flag = True
			
				#append a new uncertainty set based on the uncertainty set
				budget = int(alpha*len(best_seed))
				output = adv_oracle(budget,cur_adj,cur_keylist,best_seed)
				new_set = output[0]
				no_shows = list(set(best_seed).difference(set(new_set)))
				cur_uncertainty_sets.append(no_shows)
			
				
			
						
				
			
		else:
			best_seed = cur_invitees
		
		print('In sim no', sim_no,'----------stage:',num_trainings+1,'results are:','--------')
		print('In sim no', sim_no,'current best seed is', best_seed,len(best_seed))
		print('In sim no',sim_no,'final uncertainty set', cur_uncertainty_sets, len(cur_uncertainty_sets))
		for e in cur_uncertainty_sets:
			print(len(e))
		print('------------------------------------------------------------')
	
		best_seeds.append(best_seed)
		stage_wise_best_seeds.append(len(best_seed))
	
		#final seed is the worst case realization from the current uncertainty set
		worst_case = adv_oracle(int(alpha*len(best_seed)),cur_adj,cur_keylist,best_seed)
	
	
		print('In sim no:worst case', sim_no,worst_case)
	
		cov = worst_case[2]
		sum = worst_case[1]
		final_seed = worst_case[0]
		final_seeds.append(final_seed)
	
			
		print('In sim no',sim_no,'stage ',num_trainings+1,' coverage ',sum)
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
			print('In sim no',sim_no,'--------------------------newly constructed adj for stage:',num_trainings+2)
			print('In sim no','new adj ',new_adj)
		
			print('In sim no',sim_no,'the corresonding key_lists',new_key_list,'with length',len(new_key_list))

			print('-----------------------------------------------------------------------------------------------------------')
		

			if len(cur_invitees) > k:
				#build the uncertainty sets based on the new adj
				num_new_sets = len(cur_invitees)//num_noshows + 1
			
				uncertainty_sets = []
			
				if num_new_sets < total_sets:

					new_counter = 0
					new_already_chosen = []
					new_flag = 0
					for i in range(0,num_new_sets):
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
					num_new_sets = total_sets
			
					new_counter = 0
					new_already_chosen = []
					new_flag = 0
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
	file_handle.write('worst case coverage '+str(final_worst_case))
	file_handle.write('total nodes: '+str(len(total_nodes_covered)))
	file_handle.write('stage-wise-coverage '+str(stage_wise_coverage))
	file_handle.write('stage-wise-best-seeds'+str(best_seeds))
	file_handle.write('length of best seeds in each stage'+str(stage_wise_best_seeds))
	file_handle.close()

if __name__ == '__main__':	

	net_stats = [] #store network stats	
	
	for sim in range(0,num_sims):
		print('--------------------------------------------------')
		print('current simulation no', sim)
		#generate a graph
		adj = {} 

		key_list = [] 

		for i in range(0,total_nodes): #we have only 50 nodes in the network
			key_list.append(i)
	
		for i in key_list:
			#randomly select a set of neighbours between 6-10 neighbours (assume dense networks)
			num_neighbours = random.randint(4,8)
			temp_list = deepcopy(key_list)
			temp_list.remove(i)
			#neighbour set:
			cur_neighbours = random.sample(temp_list,num_neighbours)
			adj[i] = cur_neighbours
	
		def neighbours(adj,k):
			return adj[k]
		
		sum = 0
		std = 0
		for ele in adj:
			ngh_num = len(neighbours(adj,ele))
			sum+=ngh_num
	
		avg_deg = sum/len(key_list)
	

		for ele in adj:
			ngh_num = len(neighbours(adj,ele))
			std+=(ngh_num-avg_deg)*(ngh_num-avg_deg)
	
	
		net_stats.append((avg_deg,std/len(key_list)))
		p = Process(target = run_simulation, args = (adj, key_list,total_nodes,sim,alpha,))
		p.start()
		#p.join()


end_total = t.time()
diff = end_total - start

print('parent process time elapsed is:',diff/3600)		

	
	

	
	
