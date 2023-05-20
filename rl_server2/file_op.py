import os
def mkdir(path):
    folder = os.path.exists(path)
    if not folder:    
        os.makedirs(path)
def remove_dir(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    if os.path.exists(top):
        os.rmdir(top)
def get_files_name(folder):
    list=[]
    num_files_rec=0
    for root,dirs,files in os.walk(folder):
            for each in files:
                list.append(each)
    return list
def count_files(folder):
    list=get_files_name(folder)
    return (len(list))
def check_filename_contain(path,string):
    ret=False
    files=get_files_name(path)
    for i in range(len(files)):
        if string in files[i]:
            ret=True
            break
    return ret
def get_lines(pathname):
    count=0
    for index, line in enumerate(open(pathname,'r')):
        count += 1
    return count