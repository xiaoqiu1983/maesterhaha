import os
import math
import random
import shutil
class CdfInfo():
    def __init__(self,mark):
        self.mark=mark
        #the num of samples that value <=mark
        self.num=0
        self.index=-1
def mkdir(path):
    folder = os.path.exists(path)
    if not folder:    
        os.makedirs(path)
def get_files_name(folder):
    list=[]
    num_files_rec=0
    for root,dirs,files in os.walk(folder):
            for each in files:
                list.append(each)
    return list
def count_files(root_path,folder_name):
    data_dir=root_path+folder_name
    sz=len(data_dir)
    if data_dir[sz-1]!='/':
        data_dir=data_dir+"/"
    files=get_files_name(data_dir)
    return len(files)
def get_average_bw(pathname,column):
    sum=0.0
    rows_count=0
    for index, line in enumerate(open(pathname,'r')):
        lineArr = line.strip().split()
        sum+=float(lineArr[column])
        rows_count+=1
    average=0.0
    if rows_count>0:
        average=sum/rows_count
    return average
def get_cdf_list(sort_data,start,points,delta):
    cdf_list=[]
    n=len(sort_data)
    for i in range(points):
        mark=1.0*start+i*delta*1.0
        cdf=CdfInfo(mark);
        num=0
        if len(cdf_list)==0 or cdf_list[-1].index<0:
            for j in range(n):
                if sort_data[j]<=mark:
                    num=num+1
                    cdf.num=num
                    cdf.index=j
                else:
                    break
            cdf_list.append(cdf)
        else:
            last_cdf=cdf_list[-1]
            if last_cdf.num>=n:
                cdf.index=last_cdf.index
                cdf.num=n
            else:
                num=last_cdf.num
                cdf.num=last_cdf.num
                cdf.index=last_cdf.index
                assert num>0,"wrong"
                for j in range(last_cdf.index+1,n):
                    if sort_data[j]<=mark:
                        num=num+1
                        cdf.num=num
                        cdf.index=j
                    else:
                        break
            cdf_list.append(cdf)
    return cdf_list
def write_cdf_to_file(value_vector,fout):
    value_vector.sort()
    min_value=math.floor(value_vector[0])
    max_value=math.ceil(value_vector[-1])
    length_unit=1.0
    points_unit=20+1
    delta=length_unit/(points_unit-1)
    semgments=max_value-min_value
    points=semgments*(points_unit-1)+1
    start=1.0*min_value
    cdf_list=get_cdf_list(value_vector,start,points,delta)
    denom=len(value_vector)
    for j in range (len(cdf_list)):
        mark=cdf_list[j].mark
        precision="%.4f"
        mark_str=precision%mark
        rate=cdf_list[j].num*1.0/denom
        rate_str=precision%rate
        out=str(j+1)+"\t"+mark_str+"\t"+rate_str+"\t"+str(cdf_list[j].num)+"\n"
        fout.write(out)
def get_average_bw_cdf(root_path,folder_in):
    folder_name=folder_in
    data_dir=root_path+folder_name
    data_out_name=folder_name+"_cdf.txt"
    sz=len(data_dir)
    if data_dir[sz-1]!='/':
        data_dir=data_dir+"/"
    file_names=get_files_name(data_dir)
    file_names.sort()
    average_vector=[]
    for i in range (len(file_names)):
        pathname=data_dir+file_names[i]
        average=get_average_bw(pathname,1)
        average_vector.append(average)
    fout=open(data_out_name,"w")
    write_cdf_to_file(average_vector,fout)
    fout.close()
def extract_set_from_folder(root_path,folder_in,folder_train_out,
                    folder_test_out,howmany=100):
    data_from_dir=root_path+folder_in
    data_train_dir=root_path+folder_train_out
    data_test_dir=root_path+folder_test_out
    sz=len(data_from_dir)
    if data_from_dir[sz-1]!='/':
        data_from_dir=data_from_dir+"/"
    sz=len(data_train_dir)
    if data_train_dir[sz-1]!='/':
        data_train_dir=data_train_dir+"/"
    sz=len(data_test_dir)
    if data_test_dir[sz-1]!='/':
        data_test_dir=data_test_dir+"/"
    mkdir(data_train_dir)
    mkdir(data_test_dir)
    file_names=get_files_name(data_from_dir)
    file_names.sort()
    random.shuffle(file_names)
    total=len(file_names)
    howmany=min(howmany,total)
    for i in range(howmany):
        shutil.copy2(data_from_dir+file_names[i],data_test_dir)
    for i in range(howmany,total):
        shutil.copy2(data_from_dir+file_names[i],data_train_dir)
if __name__ == '__main__':
    root_path="/home/ipcom/zsy/ns-allinone-3.31/ns-3.31/bw_data/"
    dataset1="cook_all"
    dataset2="Oboe_traces"
    dataset1_train="cooked_traces"
    dataset1_test="cooked_test_traces"
    dataset2_train="oboe_train_traces"
    dataset2_test="oboe_test_traces"
    #extract_set_from_folder(root_path,dataset2,dataset2_train,dataset2_test,200)
    get_average_bw_cdf(root_path,dataset1)
    get_average_bw_cdf(root_path,dataset2)
    get_average_bw_cdf(root_path,dataset1_train)
    get_average_bw_cdf(root_path,dataset1_test)
    get_average_bw_cdf(root_path,dataset2_train)
    get_average_bw_cdf(root_path,dataset2_test)
