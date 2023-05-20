import random
import os
import copy
# shuffle algorithm  
# https://blog.csdn.net/qq_26399665/article/details/79831490
# random.shuffle https://www.jb51.net/article/173984.htm
def insider_out_shuffle(x):
    num=len(x)
    for i in range(num):
        j=random.randint(0,i)
        x[i], x[j] = x[j], x[i]
def two_list_equal(a,b):
    equal=True
    if len(a)==len(b):
        for i in range (len(b)):
            if a[i]!=b[i]:
                equal=False
                break
    else:
        equal=False
    return equal
def check_if_exist(sample_vec,sample):
    found=False
    for i in range(len(sample_vec)):
        if two_list_equal(sample_vec[i],sample):
            found=True
            break
    return found
def get_files_name(folder):
    list=[]
    num_files_rec=0
    for root,dirs,files in os.walk(folder):
            for each in files:
                list.append(each)
    return list
def count_files(pathname):
    data_dir=pathname
    sz=len(data_dir)
    if data_dir[sz-1]!='/':
        data_dir=data_dir+"/"
    files=get_files_name(data_dir)
    return len(files)
def generate_id(pathname_in,pathname_out,target):
    all=count_files(pathname_in)
    span=4
    sample_vec=[]
    fp=open(pathname_out,"w")
    a1=set()
    b1=set()
    while True:
        sample=[]
        i=0
        while True:
            id=random.randint(0,all-1)
            if id in sample:
                continue
            if i==0 and len(a1)<all and id in a1:
                continue
            if i==2 and len(b1)<all and id in b1:
                continue
            sample.append(id)
            i=i+1
            if i>=span:
                break
        if check_if_exist(sample_vec,sample) is False:
            sample_vec.append(sample)
            a1.add(sample[0])
            b1.add(sample[2])
        if len(a1)==all:
            a1=set()
        if len(b1)==all:
            b1=set()
        if len(sample_vec)>=target:
            break
    row=len(sample_vec)
    x=[i for i in range(row)]
    random.shuffle(x)
    for k in range(row):
        fp.write("\t{")
        i=x[k]
        num=len(sample_vec[i])
        for j in range(num):
            fp.write(str(sample_vec[i][j]))
            if j<num-1:
                fp.write(",")
        fp.write("},")
        if i<row:
            fp.write("\n")
    fp.close()
if __name__ == '__main__':
    NS3_PATH="/home/ipcom/zsy/ns-allinone-3.31/ns-3.31/"
    cook_train_traces=NS3_PATH+"bw_data/cooked_traces/" #127
    cook_test_traces=NS3_PATH+"bw_data/cooked_test_traces/" #142
    oboe_train_traces=NS3_PATH+"bw_data/oboe_train_traces/"  # 228
    oboe_test_traces=NS3_PATH+"bw_data/oboe_test_traces/" #200
    synthesize_train_traces=NS3_PATH+"bw_data/synthesize_train_traces/" #355
    synthesize_test_traces=NS3_PATH+"bw_data/synthesize_test_traces/" #342
    pathname_out="cooked_train_id.txt";
    generate_id(cook_train_traces,pathname_out,300)
    pathname_out="cooked_test_id.txt";
    generate_id(cook_test_traces,pathname_out,300)
    pathname_out="oboe_train_id.txt";
    generate_id(oboe_train_traces,pathname_out,300)
    pathname_out="oboe_test_id.txt";
    generate_id(oboe_test_traces,pathname_out,300)
    pathname_out="synthesize_train_id.txt";
    generate_id(synthesize_train_traces,pathname_out,500)
    pathname_out="synthesize_test_id.txt";
    generate_id(synthesize_test_traces,pathname_out,500)
