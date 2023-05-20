import signal, os
import multiprocessing as mp
import numpy as np
import rl_agent as ra
import file_op as fp
import tcp_service as ts
import time
import math
import logging
import argparse
Terminate=False
def signal_handler(signum, frame):
    global Terminate
    Terminate =True
def multi_thread_train(port_str,num_agent,id_span,left,right):
    state_pipes=[]
    control_msg_pipes=[]
    managers=[]
    num_manager=math.ceil(num_agent/id_span)
    for i in range(num_manager):
        first_id=i*id_span
        last_id=min((i+1)*id_span,num_agent)
        conn1,conn2=mp.Pipe()
        conn3,conn4=mp.Pipe()
        state_pipes.append((conn1,conn2))
        control_msg_pipes.append((conn3,conn4))
        manager=ra.AgentManager(first_id,last_id,state_pipes[i],control_msg_pipes[i])
        managers.append(manager)
        manager.start()
    port=int(port_str)
    tcp_server=ts.TcpServer("localhost",port,state_pipes,id_span)
    coordinator=ra.CentralAgent(num_agent,id_span,left,right,control_msg_pipes)
    coordinator.start()
    for i in range(len(state_pipes)):
        state_pipes[i][1].close()
    while not Terminate:
        tcp_server.loop_once()
        active=0;
        for i in range(num_manager):
            if managers[i].is_alive():
                active+=1
        if coordinator.is_alive():
            active+=1
        if active==0:
            break
    tcp_server.shutdown()
    coordinator.stop_process()
    coordinator.join()
    for i in range(num_manager):
        managers[i].stop_process()
        managers[i].join()
def multi_thread_test(port_str,num_agent,id_span):
    state_pipes=[]
    control_msg_pipes=[]
    managers=[]
    num_manager=math.ceil(num_agent/id_span)
    for i in range(num_manager):
        first_id=i*id_span
        last_id=min((i+1)*id_span,num_agent)
        conn1,conn2=mp.Pipe()
        conn3,conn4=mp.Pipe()
        state_pipes.append((conn1,conn2))
        control_msg_pipes.append((conn3,conn4))
        manager=ra.AgentManager(first_id,last_id,state_pipes[i],control_msg_pipes[i])
        managers.append(manager)
        manager.start()
    port=int(port_str)
    tcp_server=ts.TcpServer("localhost",port,state_pipes,id_span)
    coordinator=ra.CentralTestAgent(num_agent,id_span,control_msg_pipes)
    coordinator.start()
    for i in range(len(state_pipes)):
        state_pipes[i][1].close()
    while not Terminate:
        tcp_server.loop_once()
        active=0;
        for i in range(num_manager):
            if managers[i].is_alive():
                active+=1
        if coordinator.is_alive():
            active+=1
        if active==0:
            break
    tcp_server.shutdown()
    coordinator.stop_process()
    coordinator.join()
    for i in range(num_manager):
        managers[i].stop_process()
        managers[i].join()
def start_train(port_str,train_epoch=50000):
    NUM_AGENTS=8
    id_span=4
    fp.remove_dir(ra.NN_INFO_STORE_FOLDER)
    multi_thread_train(port_str,NUM_AGENTS,id_span,0,train_epoch)
def start_test(port_str):
    NUM_AGENTS=8
    id_span=4
    multi_thread_test(port_str,NUM_AGENTS,id_span)
def train_model(port_str,train_epoch,dataset,id_folder):
    train_id_lines=0
    test_id_lines=0
    exe_train_template=""
    exe_test_template=""
    nn_store_dir=""
    if dataset=="cooked":
        train_id=id_folder+"cooked_train_id.txt"
        test_id=id_folder+"cooked_test_id.txt"
        train_id_lines=fp.get_lines(train_id)
        test_id_lines=fp.get_lines(test_id)
        exe_train_template=EXE_COOK_TRAIN
        exe_test_template=EXE_COOK_TEST
        nn_store_dir="cooked_nn_info"
    elif dataset=="oboe":
        train_id=id_folder+"oboe_train_id.txt"
        test_id=id_folder+"oboe_test_id.txt"
        train_id_lines=fp.get_lines(train_id)
        test_id_lines=fp.get_lines(test_id)
        exe_train_template=EXE_OBOE_TRAIN
        exe_test_template=EXE_OBOE_TEST
        nn_store_dir="oboe_nn_info"
    elif dataset=="synthesize":
        train_id=id_folder+"synthesize_train_id.txt"
        test_id=id_folder+"synthesize_test_id.txt"
        train_id_lines=fp.get_lines(train_id)
        test_id_lines=fp.get_lines(test_id)
        exe_train_template=EXE_OBOE_TRAIN
        exe_test_template=EXE_OBOE_TEST
        nn_store_dir="synthesize_nn_info"
    else:
        return 
    ra.set_num_train_traces(train_id_lines)
    ra.set_num_test_traces(test_id_lines)
    ra.set_train_template(exe_train_template)
    ra.set_test_template(exe_test_template)
    ra.set_nn_info_store_dir(nn_store_dir)
    start_train(port_str,train_epoch)
def test_model(port_str,dataset,dispatch,id_folder):
    train_id=id_folder+"cooked_train_id.txt"
    train_id_lines=fp.get_lines(train_id)
    test_id_lines=0
    exe_train_template=EXE_COOK_TRAIN
    exe_test_template=""
    if dataset=="cooked":
        test_id=id_folder+"cooked_test_id.txt"
        test_id_lines=fp.get_lines(test_id)
        exe_test_template=EXE_COOK_TEST
        if dispatch=="eps":
            exe_test_template=EXE_COOK_TEST_EPS
        elif dispatch=="ucb":
            exe_test_template=EXE_COOK_TEST_UCB
    elif dataset=="oboe":
        test_id=id_folder+"oboe_test_id.txt"
        test_id_lines=fp.get_lines(test_id)
        exe_test_template=EXE_OBOE_TEST
        if dispatch=="eps":
            exe_test_template=EXE_OBOE_TEST_EPS
        elif dispatch=="ucb":
            exe_test_template=EXE_OBOE_TEST_UCB
    elif dataset=="synthesize":
        test_id=id_folder+"synthesize_test_id.txt"
        test_id_lines=fp.get_lines(test_id)
        exe_test_template=EXE_SYNTHESIZE_TEST
        if dispatch=="eps":
            exe_test_template=EXE_SYNTHESIZE_TEST_EPS
        elif dispatch=="ucb":
            exe_test_template=EXE_SYNTHESIZE_TEST_UCB
    else:
        return 
    ra.set_num_train_traces(train_id_lines)
    ra.set_num_test_traces(test_id_lines)
    ra.set_train_template(exe_train_template)
    ra.set_test_template(exe_test_template)
    start_test(port_str)
rl_server_port_str="1233";
NS3_PATH="/home/ipcom/zsy/ns-allinone-3.31/ns-3.31/"
NS3_ID_FOLDER=NS3_PATH+"id_folder/"
NS3_LIB_PATH=NS3_PATH+"build/lib/"
NS3_EXE_PATH=NS3_PATH+"build/scratch/"

EXE_COOK_TRAIN=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=1 --gr=%s --ag=%s --bwid=%s"
EXE_COOK_TEST=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=2 --log=%s --gr=%s --ag=%s --bwid=%s"
EXE_COOK_TEST_EPS=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=2 --cd=2 --log=%s --gr=%s --ag=%s --bwid=%s"
EXE_COOK_TEST_UCB=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=2 --cd=4 --log=%s --gr=%s --ag=%s --bwid=%s"

EXE_OBOE_TRAIN=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=3 --gr=%s --ag=%s --bwid=%s"
EXE_OBOE_TEST=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=4 --log=%s --gr=%s --ag=%s --bwid=%s"
EXE_OBOE_TEST_EPS=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=4 --cd=2 --log=%s --gr=%s --ag=%s --bwid=%s"
EXE_OBOE_TEST_UCB=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=4 --cd=4 --log=%s --gr=%s --ag=%s --bwid=%s"

EXE_SYNTHESIZE_TRAIN=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=5 --gr=%s --ag=%s --bwid=%s"
EXE_SYNTHESIZE_TEST=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=6 --log=%s --gr=%s --ag=%s --bwid=%s"
EXE_SYNTHESIZE_TEST_EPS=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=6 --cd=2 --log=%s --gr=%s --ag=%s --bwid=%s"
EXE_SYNTHESIZE_TEST_UCB=NS3_EXE_PATH+"mp-rl-train --p="+rl_server_port_str+" --it=6 --cd=4 --log=%s --gr=%s --ag=%s --bwid=%s"
#python ns3-mpdash-train.py --mode train --dataset cooked
#python ns3-mpdash-train.py --mode test --dataset cooked --dispatch eps
if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler) # ctrl+c
    signal.signal(signal.SIGTSTP, signal_handler) #ctrl+z
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--mode', type=str,default ='test')
    parser.add_argument('--dataset', type=str,default ='cooked')
    parser.add_argument('--dispatch', type=str,default ='def')
    args = parser.parse_args()
    mode=args.mode
    dataset=args.dataset
    dispatch_algo=args.dispatch
    #ns3 so library path
    old = os.environ.get("LD_LIBRARY_PATH")
    if old:
        os.environ["LD_LIBRARY_PATH"] = old + ":" +NS3_LIB_PATH
    else:
        os.environ["LD_LIBRARY_PATH"] = NS3_LIB_PATH
    logging.basicConfig(format='[%(filename)s:%(lineno)d] %(message)s')
    logging.getLogger("rl").setLevel(logging.DEBUG)
    last= time.time()
    train_eoch=60000
    if mode=="train":
        train_model(rl_server_port_str,train_eoch,dataset,NS3_ID_FOLDER)
    elif mode=="test":
        test_model(rl_server_port_str,dataset,dispatch_algo,NS3_ID_FOLDER)
    delta=time.time()-last
    print("stop: "+str(int(round(delta* 1000))))
