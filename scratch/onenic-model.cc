#include <string>
#include <unistd.h>
#include "ns3/core-module.h"
#include "ns3/cardiac-stem-cell-module.h"
#include "ns3/hunnan-module.h"
#include "ns3/log.h"
using namespace ns3;
NS_LOG_COMPONENT_DEFINE("onenic-model");
bool compare_by_string(const DatasetDescriptation& t1, const DatasetDescriptation & t2) {
    return t1.name<t2.name;
}
struct PathTrace{
    bool AddId(int id);
    int trace_id_[kPieroPathYDim];
    int length_=0;
};
bool PathTrace::AddId(int id){
    bool added=false;
    if(length_<kPieroPathYDim){
        trace_id_[length_]=id;
        length_++;
        added=true;
    }
    return added;
}
const uint32_t DEFAULT_PACKET_SIZE = 1500;
static float VIDEO_BIT_RATE[]={300,750,1200,1850,2850,4300}; //kbps
static    float appStart=0.001;
static HunnanNodeContainer BuildP2PTopo(uint32_t msDelay,uint32_t msQdelay){
    HunnanNodeContainer nodes;
    nodes.Create (2);
    uint32_t bps=1000000000;//1Gbps
    auto bufSize = std::max<uint32_t> (DEFAULT_PACKET_SIZE, bps * msQdelay / 8000);
    HunnanPointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate",DataRateValue(DataRate(bps)));
    p2p.SetDeviceAttribute("MaxSize",UintegerValue(bufSize));
    p2p.SetChannelAttribute("Delay",TimeValue(MilliSeconds(msDelay)));
    p2p.Install(nodes.Get(0),nodes.Get(1));
    return nodes;
}
void InstallHunnanApp(Ptr<HunnanNode> h1,Ptr<HunnanNode> h2,
                   Ptr<DashHunnanSource> dash_source,Ptr<DashHunnanSink> dash_sink,
                   Time  max_processing_delay=Seconds(200)){
    Ptr<HunnanClientChannel> clientChan=CreateObject<HunnanClientChannel>(max_processing_delay);
    Ptr<HunnanServerChannel> servChan=CreateObject<HunnanServerChannel>();
    h1->AddApplication(clientChan);
    h2->AddApplication(servChan);
    dash_source->RegisterChannel(clientChan);
    dash_sink->RegisterChannel(servChan);
}
void one_nic_dash_run(std::vector<std::string> &video_log,std::vector<double> &average_rate,std::string &algo,
                std::vector<DatasetDescriptation> &bw_traces,std::vector<PathTrace> &path_trace_vec,std::string &result_folder,
                std::string &bid, std::string &group_id,std::string &agent_id,DispatchType dispatch_type){
    uint32_t one_trans_delay=50;
    uint32_t link_queue_delay=100;
    int segment_ms=4000;
    int init_segment=2;
    DataRate default_rate(2000000);
    std::string delimit("_");
    std::string trace;
    if(result_folder.size()>0){
        MakePath(result_folder);
        piero_set_trace_root_folder(result_folder.c_str());
        trace=group_id+delimit+agent_id+delimit+bid+delimit+algo;
    }
    Ptr<MultiNicMultiServerDash> dash_source=CreateObject<MultiNicMultiServerDash>(video_log,average_rate,trace
    ,segment_ms,init_segment,Seconds(appStart));
    std::vector<Ptr<DashHunnanSink>> dash_sinks;
    int channel_index=0;
    PieroPathInfo info;
    for(int i=0;i<path_trace_vec.size();i++){
        for(int j=0;j<path_trace_vec.at(i).length_;j++){
            bool is_default=false;
            if(0==j){
                is_default=true;
            }
            info.AddId(i,channel_index,is_default);
            channel_index++;
            int trace_id=path_trace_vec.at(i).trace_id_[j];
            DatasetDescriptation dataset=bw_traces.at(trace_id);
            auto topo=BuildP2PTopo(one_trans_delay,link_queue_delay);
            Ptr<DashHunnanSink> dash_sink=CreateObject<DashHunnanSink>(Seconds(appStart),Time(0),&dataset,default_rate);
            dash_sink->SetSeed(12321);
            dash_sinks.push_back(dash_sink);
            InstallHunnanApp(topo.Get(0),topo.Get(1),dash_source,dash_sink);
        }
    }
    dash_source->SetAdaptationAlgorithm(algo,group_id,agent_id);
    dash_source->SetDispatchAlgo(dispatch_type,info);
    dash_source->Initialize();
    for(int i=0;i<dash_sinks.size();i++){
        dash_sinks[i]->Initialize();
    }
    Simulator::Run ();
    Simulator::Destroy();
}
//id1, id2,
int main(int argc,char *argv[]){
    LogComponentEnable("onenic-model",LOG_LEVEL_ALL);
    LogComponentEnable("piero_hunnan_chan",LOG_LEVEL_ALL);
    LogComponentEnable("piero_dash_app",LOG_LEVEL_ALL);
    LogComponentEnable("piero_rate_limit",LOG_LEVEL_ALL);
    LogComponentEnable("piero_dash_base",LOG_LEVEL_INFO);
    std::string instance("1");
    std::string chunk_dispatch("0");
    std::string bid("0");
    std::string group_id("0");
    std::string agent_id("0");
    DispatchType dispatch_type=DEF_CHUNK_SPLIT;
    CommandLine cmd;
    cmd.AddValue ("it", "instance",instance);
    cmd.AddValue ("cd", "chunkdis",chunk_dispatch);
    cmd.Parse (argc, argv);
    if(0==chunk_dispatch.compare("1")){
        dispatch_type=DEF_CHUNK_UNSPLIT;
    }else if(0==chunk_dispatch.compare("2")){
        dispatch_type=EPS_CHUNK_SPLIT;
    }else if(0==chunk_dispatch.compare("3")){
        dispatch_type=EPS_CHUNK_UNSPLIT;
    }else if(0==chunk_dispatch.compare("4")){
        dispatch_type=UCB_CHUNK_SPLIT;
    }else if(0==chunk_dispatch.compare("5")){
        dispatch_type=UCB_CHUNK_UNSPLIT;
    }
    std::string prefix;
    prefix="hunnan_"+DispatchTypeToString(dispatch_type)+"_";
    std::string ns3_path="/home/ipcom/zsy/ns-allinone-3.31/ns-3.31/";
    std::string trace_folder=ns3_path+"traces/";
    std::string video_path=ns3_path+std::string("video_data/");
    std::string video_name("video_size_");
    std::vector<std::string> video_log;
    std::vector<double> average_rate;
    {
        int n=6;
        for(int i=0;i<n;i++){
            std::string name=video_path+video_name+std::to_string(i);
            video_log.push_back(name);
        }
        for (int i=0;i<n;i++){
            double bps=VIDEO_BIT_RATE[i]*1000;
            average_rate.push_back(bps);
        }
    }
    const char *algorithms[]={"festive","panda","tobasco","osmp","raahs","fdash","sftm","svaa"};
    int algorithms_sz=sizeof(algorithms)/sizeof(algorithms[0]);
    DatasetDescriptation cooked_dataset[]={
        {ns3_path+std::string("bw_data/cooked_traces/"),
        RateTraceType::TIME_BW,TimeUnit::TIME_S,RateUnit::BW_Mbps},
    };
    DatasetDescriptation cooked_test_dataset[]={
        {ns3_path+std::string("bw_data/cooked_test_traces/"),
        RateTraceType::TIME_BW,TimeUnit::TIME_S,RateUnit::BW_Mbps},
    };
    DatasetDescriptation oboe_dataset[]={
        {ns3_path+std::string("bw_data/Oboe_traces/"),
        RateTraceType::TIME_BW,TimeUnit::TIME_S,RateUnit::BW_Mbps},
    };
    std::string id_folder=ns3_path+"id_folder/";
    std::string id_pathname;
    
    
    int dataset_n=0;
    DatasetDescriptation *dataset_ptr=nullptr;
    std::vector<DatasetDescriptation> bw_traces;
    int kConcurrency=2;
    Matrix <int> *combi_id_2d=nullptr;
    int combi_id_row=0;
    int combi_id_column=4;
    if(0==instance.compare("1")){
        dataset_n=sizeof(cooked_dataset)/sizeof(cooked_dataset[0]);
        dataset_ptr=cooked_dataset;
        std::fstream id_fp;
        std::string id_name="cooked_id.txt";
        id_pathname=id_folder+id_name;
        combi_id_row=CountFileLines(id_pathname);
        if(0==combi_id_row){
            return -1;
        }
        if(nullptr==combi_id_2d){
            combi_id_2d=new Matrix <int>(combi_id_row,combi_id_column);
        }
        id_fp.open(id_pathname.c_str());
        for (int i=0;i<combi_id_row;i++){
            std::string buffer;
            getline(id_fp,buffer);
            std::vector<std::string> numbers;
            BufferSplit(buffer,numbers);
            NS_ASSERT(combi_id_column==(int)numbers.size());
            for (int j=0;j<combi_id_column;j++){
                int v=std::stoi(numbers[j]);
                (*combi_id_2d)[i][j]=v;
            }
        }
        id_fp.close();  
    }else if(0==instance.compare("2")){
        dataset_n=sizeof(cooked_test_dataset)/sizeof(cooked_test_dataset[0]);
        dataset_ptr=cooked_test_dataset;
        std::fstream id_fp;
        std::string id_name="cooked_test_id.txt";
        id_pathname=id_folder+id_name;
        combi_id_row=CountFileLines(id_pathname);
        if(0==combi_id_row){
            return -1;
        }
        if(nullptr==combi_id_2d){
            combi_id_2d=new Matrix <int>(combi_id_row,combi_id_column);
        }
        id_fp.open(id_pathname.c_str());
        for (int i=0;i<combi_id_row;i++){
            std::string buffer;
            getline(id_fp,buffer);
            std::vector<std::string> numbers;
            BufferSplit(buffer,numbers);
            NS_ASSERT(combi_id_column==(int)numbers.size());
            for (int j=0;j<combi_id_column;j++){
                int v=std::stoi(numbers[j]);
                (*combi_id_2d)[i][j]=v;
            }
        }
        id_fp.close();
    }else if(0==instance.compare("3")){
        dataset_n=sizeof(oboe_dataset)/sizeof(oboe_dataset[0]);
        dataset_ptr=oboe_dataset;
        std::fstream id_fp;
        std::string id_name="oboe_id.txt";
        id_pathname=id_folder+id_name;
        combi_id_row=CountFileLines(id_pathname);
        if(0==combi_id_row){
            return -1;
        }
        if(nullptr==combi_id_2d){
            combi_id_2d=new Matrix <int>(combi_id_row,combi_id_column);
        }
        id_fp.open(id_pathname.c_str());
        for (int i=0;i<combi_id_row;i++){
            std::string buffer;
            getline(id_fp,buffer);
            std::vector<std::string> numbers;
            BufferSplit(buffer,numbers);
            NS_ASSERT(combi_id_column==(int)numbers.size());
            for (int j=0;j<combi_id_column;j++){
                int v=std::stoi(numbers[j]);
                (*combi_id_2d)[i][j]=v;
            }
        }
        id_fp.close();
    }else{
        return 0;
    }
    if(dataset_n>0&&dataset_ptr){
        for(int i=0;i<dataset_n;i++){
            std::vector<std::string> files;
            std::string folder=dataset_ptr[i].name;
            GetFiles(folder,files);
            for (size_t j=0;j<files.size();j++){
                std::string path_name=folder+files[j];
                DatasetDescriptation des(path_name,dataset_ptr[i].type,
                dataset_ptr[i].time_unit,dataset_ptr[i].rate_unit);
                bw_traces.push_back(des);
            }
        }
        std::sort(bw_traces.begin(), bw_traces.end(),compare_by_string);
    }
    int bw_traces_sz=bw_traces.size();
    uint64_t last_time=PieroTimeMillis();
    std::string result_folder;
    if(0==instance.compare("1")){
        result_folder=trace_folder+prefix+"cooked";
    }else if(0==instance.compare("2")){
        result_folder=trace_folder+prefix+"cooked_test";
    }else if(0==instance.compare("3")){
        result_folder=trace_folder+prefix+"oboe";
    }
    for(int i=0;i<algorithms_sz;i++){
        std::string algo(algorithms[i]);  
        for(int j=0;j<combi_id_row;j++){
            std::vector<PathTrace> path_trace_vec;
            int index=0;
            for(int m=0;m<combi_id_column/kConcurrency;m++){
                PathTrace  temp;
                for(int n=0;n<kConcurrency;n++){
                    int v=(*combi_id_2d)[j][index]%bw_traces_sz;
                    temp.AddId(v);
                    index++;
                }
                path_trace_vec.push_back(temp);
            }
            bid=std::to_string(j);
            one_nic_dash_run(video_log,average_rate,algo,
                            bw_traces,path_trace_vec,result_folder,
                            bid,group_id,agent_id,dispatch_type);
        }
    }
    uint64_t delta=PieroTimeMillis()-last_time;
    double seconds=1.0*delta/1000;
    if(combi_id_2d){
        delete combi_id_2d;
    }
    NS_LOG_INFO("run time: "<<seconds);
    return 0;
}
