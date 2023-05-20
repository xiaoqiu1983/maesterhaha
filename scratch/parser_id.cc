#include <string>
#include <iostream>
#include <fstream>
#include <unistd.h>
#include <vector>
#include "ns3/core-module.h"
#include "ns3/cardiac-stem-cell-module.h"
#include "ns3/hunnan-module.h"
#include "ns3/log.h"
using namespace ns3;
using namespace std;
int main(int argc,char *argv[]){
    std::string ns3_path="/home/ipcom/zsy/ns-allinone-3.31/ns-3.31/";
    {
        std::string id_folder=ns3_path+"id_folder/";
        std::string id_name="cooked_id.txt";
        std::string pathname=id_folder+id_name;
        int line_num=CountFileLines(pathname);
        std::cout<<line_num<<std::endl;
        std::fstream id_fp;
        id_fp.open(pathname.c_str());
        for (int i=0;i<3;i++){
            std::string buffer;
            getline(id_fp,buffer);
            std::cout<<buffer<<std::endl;
            std::vector<std::string> numbers;
            BufferSplit(buffer,numbers);
            for (int j=0;j<numbers.size();j++){
                std::cout<<std::stoi(numbers[j])<<" ";
            }
            std::cout<<std::endl;
        }

        id_fp.close();
    }
    {
        
        std::string bw_folder=ns3_path+std::string("bw_data/cooked_traces/");
        std::string pathname=bw_folder+"bus.ljansbakken-oslo-report.2010-09-28_1407CEST.log";
        std::fstream bw_fp;
        bw_fp.open(pathname.c_str());
        std::string buffer;
        std::vector<std::string> numbers;
        getline(bw_fp,buffer);
        BufferSplit(buffer,numbers);
        for (int i=0;i<numbers.size();i++){
            std::cout<<numbers[i]<<std::endl;
        }
        getline(bw_fp,buffer);
        BufferSplit(buffer,numbers);
        for (int i=0;i<numbers.size();i++){
            std::cout<<numbers[i]<<std::endl;
        }
        bw_fp.close();
    }
    return 0;
}
