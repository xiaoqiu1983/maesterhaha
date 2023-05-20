#include "ns3/libae-module.h"
#include <iostream>

int main(){
    aeEventLoop *loop;
    loop = aeCreateEventLoop(1024); 
    aeDeleteEventLoop(loop);
    std::cout<<"libae"<<std::endl;
    return 0;
}
