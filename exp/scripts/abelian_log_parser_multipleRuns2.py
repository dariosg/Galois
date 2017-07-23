##########################################
# To parse log files generated by abelian.
# Author: Gurbinder Gill
# Email: gurbinder533@gmail.com
#########################################

import re
import os
import sys, getopt
import csv
import numpy
import subprocess

######## NOTES:
# All time values are in sec by default.


def match_timers(fileName, benchmark, forHost, numRuns, numThreads, time_unit, total_hosts, partition, run_identifier):

  mean_time = 0.0;
  recvNum_total = 0
  recvBytes_total = 0
  sendNum_total = 0
  sendBytes_total = 0
  sync_pull_avg_time_total = 0.0;
  extract_avg_time_total = 0.0;
  set_avg_time_total = 0.0;
  sync_push_avg_time_total = 0.0;
  graph_init_time = 0
  hg_init_time = 0
  total_time = 0

  if(benchmark == "cc"):
    benchmark = "ConnectedComp"

  if(benchmark == "pagerank"):
    benchmark = "PageRank"

  if (time_unit == 'seconds'):
    divisor = 1000
  else:
    divisor = 1

  log_data = open(fileName).read()


  timer_regex = re.compile(re.escape(run_identifier) + r',\(NULL\),0\s,\sTIMER_0,\d*,0,(\d*)')
  timers = re.findall(timer_regex, log_data)
  #print timers

  time = []
  total_mean_time=0.0

  print timers
  for i in range(int(total_hosts)):
    time.append(0)

  for timer in timers:
    total_mean_time += float(timer)
    #print "TIMER : ", timer

  print "TOTAL MEAN TIME " , total_mean_time
  total_mean_time = total_mean_time/int(total_hosts)
  total_mean_time /= divisor
  mean_time = total_mean_time = round(total_mean_time, 3)
  print "Total Mean time: ", total_mean_time

  rep_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sREPLICATION_FACTOR_0_0,(\d*),\d*,(.*)')

  rep_search = rep_regex.search(log_data)
  rep_factor = 0;
  if rep_search is not None:
    rep_factor = rep_search.group(2)
    rep_factor = round(float(rep_factor), 3)
  print ("Replication factor  : ", rep_factor)

  num_iter_regex = re.compile((run_identifier) +r',\(NULL\),0\s,\sNUM_ITERATIONS_0' + r',\d*,\d*,(\d*)')
  num_iter_search = num_iter_regex.search(log_data)
  if num_iter_regex is not None:
    if num_iter_search is None:
      num_iter = -1
    else:
      num_iter = num_iter_search.group(1)
    print "NUM_ITER : ", num_iter


  #Finding mean,max,sd compute time over all hosts
  max_do_all = 0
  sum_do_all = 0
  for i in range(0,int(num_iter)):
    do_all_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\s.*DO_ALL_IMPL_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    do_all_all_hosts = re.findall(do_all_regex, log_data)
    num_arr = numpy.array(map(int,do_all_all_hosts))

    if len(num_arr) != 0:
      #print (" COMPUTE NUM_ARR", num_arr)
      max_compute = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_do_all += max_compute
      sum_do_all += numpy.sum(num_arr, axis=0)
  print "max_do_all " , max_do_all
  print "sum_do_all " , sum_do_all
  mean_do_all = float(sum_do_all)/float(total_hosts)


  print "mean_do_all", mean_do_all


  ##################### SYNC ##############################
  ############## SYNC = BROADCAST + REDUCE ################
  #Finding mean,max,sd sync time over all hosts
  max_sync = 0
  sum_sync = 0
  for i in range(0,int(num_iter)):
    sync_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sSYNC_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    sync_all_hosts = re.findall(sync_regex, log_data)
    num_arr = numpy.array(map(int,sync_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_sync_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_sync += max_sync_itr
      sum_sync += numpy.sum(num_arr, axis=0)
  mean_sync_time = float(sum_sync)/float(total_hosts)


  print "NEW SYNC_TIME ", mean_sync_time



  ##################### BROADCAST ##############################
  #### BROADCAST = BROADCAST_SEND + BROADCAST_EXTRACT + BROADCAST_RECV + BROADCAST_SET
  #Finding mean,max,sd BROADCAST time over all hosts
  max_broadcast = 0
  sum_broadcast = 0
  for i in range(0,int(num_iter)):
    broadcast_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sBROADCAST_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    broadcast_all_hosts = re.findall(broadcast_regex, log_data)
    num_arr = numpy.array(map(int,broadcast_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_broadcast_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_broadcast += max_broadcast_itr
      sum_broadcast += numpy.sum(num_arr, axis=0)
  mean_broadcast_time = float(sum_broadcast)/float(total_hosts)


  print "NEW BROADCAST_TIME ", mean_broadcast_time

  ##################### BROADCAST SEND ##############################
  #Finding mean,max,sd BROADCAST time over all hosts
  max_broadcast_send = 0
  sum_broadcast_send = 0
  for i in range(0,int(num_iter)):
    broadcast_send_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sBROADCAST_SEND_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    broadcast_send_all_hosts = re.findall(broadcast_send_regex, log_data)
    num_arr = numpy.array(map(int,broadcast_send_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_broadcast_send_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_broadcast_send += max_broadcast_send_itr
      sum_broadcast_send += numpy.sum(num_arr, axis=0)
  mean_broadcast_send_time = float(sum_broadcast_send)/float(total_hosts)


  print "NEW broadcast_send_TIME ", mean_broadcast_send_time


  ##################### BROADCAST EXTRACT ##############################
  #Finding mean,max,sd BROADCAST time over all hosts
  max_broadcast_extract = 0
  sum_broadcast_extract = 0
  for i in range(0,int(num_iter)):
    broadcast_extract_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sBROADCAST_EXTRACT_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    broadcast_extract_all_hosts = re.findall(broadcast_extract_regex, log_data)
    num_arr = numpy.array(map(int,broadcast_extract_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_broadcast_extract_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_broadcast_extract += max_broadcast_extract_itr
      sum_broadcast_extract += numpy.sum(num_arr, axis=0)
  mean_broadcast_extract_time = float(sum_broadcast_extract)/float(total_hosts)


  print "NEW broadcast_extract_TIME ", mean_broadcast_extract_time


##################### BROADCAST recv ##############################
  #Finding mean,max,sd BROADCAST time over all hosts
  max_broadcast_recv = 0
  sum_broadcast_recv = 0
  for i in range(0,int(num_iter)):
    broadcast_recv_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sBROADCAST_RECV_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    broadcast_recv_all_hosts = re.findall(broadcast_recv_regex, log_data)
    num_arr = numpy.array(map(int,broadcast_recv_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_broadcast_recv_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_broadcast_recv += max_broadcast_recv_itr
      sum_broadcast_recv += numpy.sum(num_arr, axis=0)
  mean_broadcast_recv_time = float(sum_broadcast_recv)/float(total_hosts)


  print "NEW broadcast_recv_TIME ", mean_broadcast_recv_time


  ##################### BROADCAST SET ##############################
  #Finding mean,max,sd BROADCAST time over all hosts
  max_broadcast_set = 0
  sum_broadcast_set = 0
  for i in range(0,int(num_iter)):
    broadcast_set_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sBROADCAST_SET_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    broadcast_set_all_hosts = re.findall(broadcast_set_regex, log_data)
    num_arr = numpy.array(map(int,broadcast_set_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_broadcast_set_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_broadcast_set += max_broadcast_set_itr
      sum_broadcast_set += numpy.sum(num_arr, axis=0)
  print "max_do_all " , max_broadcast_set
  print "sum_do_all " , sum_broadcast_set
  mean_broadcast_set_time = float(sum_broadcast_set)/float(total_hosts)


  print "NEW broadcast_set_TIME ", mean_broadcast_set_time





  ##################### REDUCE ##############################
  #Finding mean,max,sd REDUCE time over all hosts
  max_reduce = 0
  sum_reduce = 0
  for i in range(0,int(num_iter)):
    reduce_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sREDUCE_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    reduce_all_hosts = re.findall(reduce_regex, log_data)
    num_arr = numpy.array(map(int,reduce_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_reduce_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_reduce += max_reduce_itr
      sum_reduce += numpy.sum(num_arr, axis=0)
  mean_reduce_time = float(sum_reduce)/float(total_hosts)


  print "NEW REDUCE_TIME ", mean_reduce_time


  ##################### REDUCE SEND ##############################
  #Finding mean,max,sd reduce time over all hosts
  max_reduce_send = 0
  sum_reduce_send = 0
  for i in range(0,int(num_iter)):
    reduce_send_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sREDUCE_SEND_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    reduce_send_all_hosts = re.findall(reduce_send_regex, log_data)
    num_arr = numpy.array(map(int,reduce_send_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_reduce_send_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_reduce_send += max_reduce_send_itr
      sum_reduce_send += numpy.sum(num_arr, axis=0)
  mean_reduce_send_time = float(sum_reduce_send)/float(total_hosts)


  print "NEW reduce_send_TIME ", mean_reduce_send_time



  ##################### REDUCE EXTRACT ##############################
  #Finding mean,max,sd reduce time over all hosts
  max_reduce_extract = 0
  sum_reduce_extract = 0
  for i in range(0,int(num_iter)):
    reduce_extract_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sREDUCE_EXTRACT_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    reduce_extract_all_hosts = re.findall(reduce_extract_regex, log_data)
    num_arr = numpy.array(map(int,reduce_extract_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_reduce_extract_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_reduce_extract += max_reduce_extract_itr
      sum_reduce_extract += numpy.sum(num_arr, axis=0)
  mean_reduce_extract_time = float(sum_reduce_extract)/float(total_hosts)


  print "NEW reduce_extract_TIME ", mean_reduce_extract_time


##################### REDUCE recv ##############################
  #Finding mean,max,sd reduce time over all hosts
  max_reduce_recv = 0
  sum_reduce_recv = 0
  for i in range(0,int(num_iter)):
    reduce_recv_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sREDUCE_RECV_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    reduce_recv_all_hosts = re.findall(reduce_recv_regex, log_data)
    num_arr = numpy.array(map(int,reduce_recv_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_reduce_recv_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_reduce_recv += max_reduce_recv_itr
      sum_reduce_recv += numpy.sum(num_arr, axis=0)
  mean_reduce_recv_time = float(sum_reduce_recv)/float(total_hosts)


  print "NEW reduce_recv_TIME ", mean_reduce_recv_time


  ##################### REDUCE SET ##############################
  #Finding mean,max,sd reduce time over all hosts
  max_reduce_set = 0
  sum_reduce_set = 0
  for i in range(0,int(num_iter)):
    reduce_set_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sREDUCE_SET_(?i)' + re.escape(benchmark) + r'_0_'+ re.escape(str(i)) + r',.*' + r',\d*,(\d*)')
    reduce_set_all_hosts = re.findall(reduce_set_regex, log_data)
    num_arr = numpy.array(map(int,reduce_set_all_hosts))

    if len(num_arr) != 0:
      #print (" SYNC NUM_ARR", num_arr)
      max_reduce_set_itr = numpy.max(num_arr, axis=0)
      #print ("MAX : ", max_compute)
      max_reduce_set += max_reduce_set_itr
      sum_reduce_set += numpy.sum(num_arr, axis=0)
  mean_reduce_set_time = float(sum_reduce_set)/float(total_hosts)


  print "NEW reduce_set_TIME ", mean_reduce_set_time



  # ######################## BROADCAST SENT BYTES ################################
  #Finding total communication volume in bytes
  #2cc54509-cb49-43f9-b1a5-be8f4a4eaf1f,(NULL),0 , BROADCAST_SEND_BYTES_BFS_0_1,0,0,41851160
  sum_broadcast_bytes = 0
  max_broadcast_bytes = 0
  min_broadcast_bytes = 0
  broadcast_bytes_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sBROADCAST_SEND_BYTES_(?i)' + re.escape(benchmark) + r'_0_' +r'\d*' +r',.*' + r',\d*,(\d*)')
  broadcast_bytes_all_hosts = re.findall(broadcast_bytes_regex, log_data)
  num_arr = numpy.array(map(int,broadcast_bytes_all_hosts))
  if(num_arr.size > 0):
    sum_broadcast_bytes += numpy.sum(num_arr, axis=0)
    max_broadcast_bytes += numpy.max(num_arr, axis=0)
    min_broadcast_bytes += numpy.min(num_arr, axis=0)

  print "BROADCAST SEND BYTES : ", sum_broadcast_bytes


  # ######################## REDUCE SENT BYTES ################################
  #Finding total communication volume in bytes
  #2cc54509-cb49-43f9-b1a5-be8f4a4eaf1f,(NULL),0 , BROADCAST_SEND_BYTES_BFS_0_1,0,0,41851160
  sum_reduce_bytes = 0
  max_reduce_bytes = 0
  min_reduce_bytes = 0
  reduce_bytes_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sREDUCE_SEND_BYTES_(?i)' + re.escape(benchmark) + r'_0_' +r'\d*' +r',.*' + r',\d*,(\d*)')
  reduce_bytes_all_hosts = re.findall(reduce_bytes_regex, log_data)
  num_arr = numpy.array(map(int,reduce_bytes_all_hosts))
  if(num_arr.size > 0):
    sum_reduce_bytes += numpy.sum(num_arr, axis=0)
    max_reduce_bytes += numpy.max(num_arr, axis=0)
    min_reduce_bytes += numpy.min(num_arr, axis=0)

  print "REDUCE SEND BYTES : ", sum_reduce_bytes


  total_sync_bytes = sum_reduce_bytes + sum_broadcast_bytes


  #75ae6860-be9f-4498-9315-1478c78551f6,(NULL),0 , NUM_WORK_ITEMS_0_0,0,0,262144
  #Total work items, averaged across hosts
  work_items_regex = re.compile((run_identifier) + r',\(NULL\),0\s,\sNUM_WORK_ITEMS_0_\d*,\d*,\d*,(\d*)')
  work_items = re.findall(work_items_regex, log_data)
  print work_items
  num_arr = numpy.array(map(int,work_items))
  total_work_item = numpy.sum(num_arr, axis=0)
  print total_work_item

  timer_graph_init_regex = re.compile((run_identifier) +r',\(NULL\),0\s,\sTIMER_GRAPH_INIT' + r',\d*,\d*,(\d*)')
  timer_graph_init_all_hosts = re.findall(timer_graph_init_regex, log_data)

  num_arr = numpy.array(map(int,timer_graph_init_all_hosts))
  #avg_graph_init_time = float(numpy.sum(num_arr, axis=0))/float(total_hosts)
  max_graph_init_time = numpy.max(num_arr, axis=0)
  #avg_graph_init_time = round((avg_graph_init_time / divisor),3)

  print "max_graph_init time : ", max_graph_init_time



  ## Get Graph_init, HG_init, total
  #81a5b117-8054-46af-9a23-1f28e5ed1bba,(NULL),0 , TIMER_GRAPH_INIT,0,0,306
  #timer_graph_init_regex = re.compile((run_identifier) +r',\(NULL\),0\s,\sTIMER_GRAPH_INIT,\d*,\d*,(\d*)')
  timer_hg_init_regex = re.compile((run_identifier) +r',\(NULL\),0\s,\sTIMER_HG_INIT' + r',\d*,\d*,(\d*)')
  timer_hg_init_all_hosts = re.findall(timer_hg_init_regex, log_data)

  num_arr = numpy.array(map(int,timer_hg_init_all_hosts))
  #avg_hg_init_time = float(numpy.sum(num_arr, axis=0))/float(total_hosts)
  max_hg_init_time = numpy.max(num_arr, axis=0)
  #avg_hg_init_time = round((avg_hg_init_time / divisor),3)
  hg_init_time = max_hg_init_time

  timer_comm_setup_regex = re.compile((run_identifier) +r',\(NULL\),0\s,\sCOMMUNICATION_SETUP_TIME' + r',\d*,\d*,(\d*)')
  timer_comm_setup_all_hosts = re.findall(timer_comm_setup_regex, log_data)

  num_arr = numpy.array(map(int,timer_comm_setup_all_hosts))
  #avg_comm_setup_time = float(numpy.sum(num_arr, axis=0))/float(total_hosts)
  max_comm_setup_time = numpy.max(num_arr, axis=0)
  #max_comm_setup_time = round((avg_comm_setup_time / divisor),3)

  print "max_comm_setup time : ", max_comm_setup_time

  timer_total_regex = re.compile((run_identifier) +r',\(NULL\),0\s,\sTIMER_TOTAL' + r',\d*,\d*,(\d*)')
  #timer_graph_init = timer_graph_init_regex.search(log_data)
  #timer_hg_init = timer_hg_init_regex.search(log_data)
  timer_total = timer_total_regex.search(log_data)
  if timer_total is not None:
    total_time = float(timer_total.group(1))
    total_time /= divisor
    total_time = round(total_time, 3)

  return mean_time,rep_factor,mean_do_all,total_sync_bytes,sum_broadcast_bytes,sum_reduce_bytes,num_iter,total_work_item,hg_init_time,total_time,max_do_all,mean_sync_time,mean_broadcast_time,mean_broadcast_send_time,mean_broadcast_extract_time,mean_broadcast_recv_time,mean_broadcast_set_time,mean_reduce_time,mean_reduce_send_time,mean_reduce_extract_time,mean_reduce_recv_time,mean_reduce_set_time,max_comm_setup_time,max_graph_init_time

'''
  if timer_graph_init is not None:
    graph_init_time = float(timer_graph_init.group(1))
    graph_init_time /= divisor
    graph_init_time = round(graph_init_time, 3)

  if timer_hg_init is not None:
    hg_init_time = float(timer_hg_init.group(1))
    hg_init_time /= divisor
    hg_init_time = round(hg_init_time, 3)

  if timer_total is not None:
    total_time = float(timer_total.group(1))
    total_time /= divisor
    total_time = round(total_time, 3)

  print graph_init_time
  print hg_init_time
  print total_time
'''

def get_basicInfo(fileName, run_identifier):

  print ("IDENTIFIER : ", str(run_identifier))
  hostNum_regex = re.compile(re.escape(run_identifier) + r',\(NULL\),0\s,\sHosts,0,0,(\d*)')
  cmdLine_regex = re.compile(re.escape(run_identifier) + r',\(NULL\),0\s,\sCommandLine,0,0,(.*)')
  threads_regex = re.compile(re.escape(run_identifier) + r',\(NULL\),0\s,\sThreads,0,0,(\d*)')
  runs_regex = re.compile(re.escape(run_identifier) + r',\(NULL\),0\s,\sRuns,0,0,(\d*)')

  log_data = open(fileName).read()

  hostNum    = ''
  cmdLine    = ''
  threads    = ''
  runs       = ''
  benchmark  = ''
  algo_type  = ''
  cut_type   = ''
  input_graph = ''

  hostNum_search = hostNum_regex.search(log_data)
  print hostNum_regex.pattern
  print cmdLine_regex.pattern
  if hostNum_search is not None:
    hostNum = hostNum_search.group(1)

  cmdLine_search = cmdLine_regex.search(log_data)
  if cmdLine_search is not None:
    cmdLine = cmdLine_search.group(1)

  threads_search = threads_regex.search(log_data)
  if threads_search is not None:
    threads = threads_search.group(1)

  runs_search    = runs_regex.search(log_data)
  if runs_search is not None:
    runs = runs_search.group(1)
  if runs == "":
    runs = "3"

  print ("CMDLINE : ", cmdLine)
  split_cmdLine_algo = cmdLine.split()[0].split("/")[-1].split("_")
  print split_cmdLine_algo
  benchmark = split_cmdLine_algo[0]
  algo_type = '-'.join(split_cmdLine_algo[1:])

  split_cmdLine_input = cmdLine.split()[1].split("/")
  input_graph_name = split_cmdLine_input[-1]
  input_graph = input_graph_name.split(".")[0]

  print cmdLine
  split_cmdLine = cmdLine.split()
  print split_cmdLine
  cut_type = "edge-cut"
  for index in range(0, len(split_cmdLine)):
    if split_cmdLine[index] == "-enableVertexCut=1":
      cut_type = "vertex-cut"
      break
    elif split_cmdLine[index] == "-enableVertexCut":
         cut_type = "vertex-cut"
         break
    elif split_cmdLine[index] == "-enableVertexCut=0":
         cut_type = "edge-cut"
         break

  num_nodes = hostNum
  for index in range(2, len(cmdLine.split())):
    split_cmdLine_devices = cmdLine.split()[index].split("=")
    if split_cmdLine_devices[0] == '-num_nodes':
      num_nodes = split_cmdLine_devices[-1]
  num_hosts_per_node = int(hostNum) / int(num_nodes)

  devices = str(hostNum) + " CPU"
  deviceKind = "CPU"
  for index in range(2, len(cmdLine.split())):
    split_cmdLine_devices = cmdLine.split()[index].split("=")
    if split_cmdLine_devices[0] == '-pset':
      devices_str = split_cmdLine_devices[-1]
      cpus = devices_str.count('c')
      gpus = devices_str.count('g')
      if cpus + gpus == num_hosts_per_node and gpus > 0:
        if cpus == 0:
          devices = str(gpus) + " GPU"
          deviceKind = "GPU"
        else:
          devices = str(cpus) + " CPU + " + str(gpus) + " GPU"
          deviceKind = "CPU+GPU"
          hostNum = str(int(hostNum) - cpus)
      break

  return hostNum, cmdLine, threads, runs, benchmark, algo_type, cut_type, input_graph, devices, deviceKind

def format_str(col):
  max_len = 0
  for c in col:
    if max_len < len(str(c)):
      max_len = len(str(c))
  return max_len

def main(argv):
  inputFile = ''
  forHost = ''
  outputFile = 'LOG_output.csv'
  time_unit = 'milliseconds'
  try:
    opts, args = getopt.getopt(argv,"hi:n:o:md",["ifile=","node=","ofile=","milliseconds"])
  except getopt.GetoptError:
    print 'abelian_log_parser.py -i <inputFile> [-o <outputFile> -n <hostNumber 0 to hosts-1> --milliseconds]'
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print 'abelian_log_parser.py -i <inputFile> [-o <outputFile> -n <hostNumber 0 to hosts-1> --milliseconds]'
      sys.exit()
    elif opt in ("-i", "--ifile"):
      inputFile = arg
    elif opt in ("-n", "--node"):
      forHost = arg
    elif opt in ("-o", "--ofile"):
      outputFile = arg
    elif opt in ("-m", "--milliseconds"):
      time_unit = 'milliseconds'

  if inputFile == '':
    print 'abelian_log_parser.py -i <inputFile> [-o <outputFile> -n <hostNumber 0 to hosts-1> --milliseconds]'
    sys.exit(2)

  print 'Input file is : ', inputFile
  print 'Output file is : ', outputFile
  print 'Data for host : ', forHost

  if forHost == '':
    print 'Find the slowest host and calculating everything for that host'

  #Find the unique identifiers for different runs
  log_data = open(inputFile).read()
  run_identifiers_regex = re.compile(r'(.*),\(NULL\),0\s,\sTIMER_0,0,0,\d*')
  run_identifiers = re.findall(run_identifiers_regex, log_data)
  for run_identifier in run_identifiers:
    print run_identifier

    hostNum, cmdLine, threads, runs, benchmark, algo_type, cut_type, input_graph, devices, deviceKind = get_basicInfo(inputFile, run_identifier)

    #shorten the graph names:
    if input_graph == "twitter-ICWSM10-component_withRandomWeights" or input_graph == "twitter-ICWSM10-component-transpose" or input_graph == "twitter-ICWSM10-component":
      input_graph = "twitter-50"
    elif input_graph == "twitter-WWW10-component_withRandomWeights" or input_graph == "twitter-WWW10-component-transpose" or input_graph == "twitter-WWW10-component":
      input_graph = "twitter-40"

    print 'Hosts : ', hostNum , ' CmdLine : ', cmdLine, ' Threads : ', threads , ' Runs : ', runs, ' benchmark :' , benchmark , ' algo_type :', algo_type, ' cut_type : ', cut_type, ' input_graph : ', input_graph
    print 'Devices : ', devices
    data = match_timers(inputFile, benchmark, forHost, runs, threads, time_unit, hostNum, cut_type, run_identifier)

    print data

    output_str = run_identifier + ',' + benchmark + ',' + 'abelian' + ',' + hostNum  + ',' + threads  + ','
    output_str += deviceKind  + ',' + devices  + ','
    output_str += input_graph  + ',' + algo_type  + ',' + cut_type
    print output_str


    header_csv_str = "run-id,benchmark,platform,host,threads,"
    header_csv_str += "deviceKind,devices,"
    #header_csv_str += "input,variant,partition,mean_time,rep_factor,mean_do_all,mean_exract_time,mean_set_time,mean_sync_time,total_sync_bytes,num_iter,num_work_items,hg_init_time,total_time,max_do_all,max_extract,max_set,max_sync,max_sync_bytes,max_comm_setup_time,max_graph_init_time"
    header_csv_str += "input,variant,partition,mean_time,rep_factor,mean_do_all,total_sync_bytes,sum_broadcast_bytes,sum_reduce_bytes,num_iter,total_work_item,hg_init_time,total_time,max_do_all,mean_sync_time,mean_broadcast_time,mean_broadcast_send_time,mean_broadcast_extract_time,mean_broadcast_recv_time,mean_broadcast_set_time,mean_reduce_time,mean_reduce_send_time,mean_reduce_extract_time,mean_reduce_recv_time,mean_reduce_set_time,max_comm_setup_time,max_graph_init_time"

    header_csv_list = header_csv_str.split(',')
    try:
      if os.path.isfile(outputFile) is False:
        fd_outputFile = open(outputFile, 'wb')
        wr = csv.writer(fd_outputFile, quoting=csv.QUOTE_NONE, lineterminator='\n')
        wr.writerow(header_csv_list)
        fd_outputFile.close()
        print "Adding header to the empty file."
      else:
        print "outputFile : ", outputFile, " exists, results will be appended to it."
    except OSError:
      print "Error in outfile opening\n"

    data_list = list(data) #[data] #list(data)
    complete_data = output_str.split(",") + data_list
    fd_outputFile = open(outputFile, 'a')
    wr = csv.writer(fd_outputFile, quoting=csv.QUOTE_NONE, lineterminator='\n')
    wr.writerow(complete_data)
    fd_outputFile.close()

'''
  ## Write ghost and slave nodes to a file.
  ghost_array = build_master_ghost_matrix(inputFile, benchmark, cut_type, hostNum, runs, threads)
  ghostNodes_file = outputFile + "_" + cut_type
  fd_ghostNodes_file = open(ghostNodes_file, 'ab')
  fd_ghostNodes_file.write("\n--------------------------------------------------------------\n")
  fd_ghostNodes_file.write("\nHosts : " + hostNum + "\nInputFile : "+ inputFile + "\nBenchmark: " + benchmark + "\nPartition: " + cut_type + "\n\n")
  numpy.savetxt(fd_ghostNodes_file, ghost_array, delimiter=',', fmt='%d')
  fd_ghostNodes_file.write("\n--------------------------------------------------------------\n")
  fd_ghostNodes_file.close()
'''

if __name__ == "__main__":
  main(sys.argv[1:])

