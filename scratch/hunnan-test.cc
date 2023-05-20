#include <iostream>
#include "ns3/core-module.h"
#include "ns3/hunnan-module.h"
#include "ns3/data-rate.h"
#include "ns3/network-module.h"
using namespace ns3;
void hunnan_helper_test(Time start=Time(0)){
    Ptr<HunnanNode> h1=CreateObject<HunnanNode>();
    Ptr<HunnanNode> h2=CreateObject<HunnanNode>();
    HunnanPointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate",DataRateValue(DataRate(4000000)));
    p2p.SetDeviceAttribute("MaxSize",UintegerValue(1500*20));
    p2p.SetChannelAttribute("Delay",TimeValue(MilliSeconds(20)));
    p2p.Install(h1,h2);
    Ptr<HunnanSourceApp> source=CreateObject<HunnanSourceApp>();
    Ptr<HunnanSinkApp> sink=CreateObject<HunnanSinkApp>();
    source->SetStartTime(start);
    h1->AddApplication(source);
    h2->AddApplication(sink);
    Simulator::Run ();
    Simulator::Destroy();
}
void test_rate(){
    DataRate rate(0);
    Time next=rate.CalculateBytesTxTime(1500);
    std::cout<<next.GetMilliSeconds();
}
int main(int argc,char *argv[]){
    LogComponentEnable("HunnanHostList",LOG_LEVEL_ALL);
    LogComponentEnable("HunnanNode",LOG_LEVEL_ALL);
    LogComponentEnable("HunnanChannel",LOG_LEVEL_ALL);
    LogComponentEnable("HunnanNetDevice",LOG_LEVEL_ALL);
    LogComponentEnable("HunnanSourceSink",LOG_LEVEL_ALL);
    //hunnan_helper_test();
    test_rate();
    std::cout<<"test done"<<std::endl;
    return 0;
}
