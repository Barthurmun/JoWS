#!/usr/bin/python

'This example runs stations in AP mode'

import sys

from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.node import OVSKernelAP
from mn_wifi.cli import CLI_wifi
from mn_wifi.net import Mininet_wifi
from time import sleep

def topology():
    'Create a network.'
    net = Mininet_wifi(controller=Controller, accessPoint=OVSKernelAP)

    info("*** Creating nodes\n")
     
    internet = net.addHost('internet', ip='10.0.0.1/24', position='30,30,30')
    
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:01',position='20,8,0') #YouTube
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:02',position='20,7,8') #YouTube
    #sta2 = net.addHost('sta2', mac='00:00:00:00:00:02',position='20,7,8') #YouTube
    
    ap1 = net.addAccessPoint('ap1', ssid='Jows-proj1', channel='36', mode='ac', position='25,10,15')
        
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:03', position='30,10,5') #BE DL traffic
    sta4 = net.addStation('sta4', mac='00:00:00:00:00:04', position='30,15,10') #VoIP between sta4 and sta5
    #sta5 = net.addStation('sta5', mac='00:00:00:00:00:05',  position='30,17,8') #VoIP between sta4 and sta5
    
    c0 = net.addController('c0', controller=Controller, ip='127.0.0.1', port=6633)
    
    #net.setPropagationModel(model="logDistance", exp=4.5)

    info("***Ploting the graph***\n")
    net.plotGraph(max_x=60, max_y=60)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Adding Link\n")
    net.addLink(ap1, internet)
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap1)
    net.addLink(sta3, ap1)
    net.addLink(sta4, ap1)
    #net.addLink(sta5, ap1)

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    
    net.pingFull()
    
    #Pewnie trzeba dodac tutaj odpowiednie Wait'y
    sleep(5)
    ap1.cmd("tc qdisc add dev ap1-eth2 root handle 1: htb default 20")
    ap1.cmd("tc class add dev ap1-eth2 parent 1: classid 1:1 htb rate 125kbps ceil 125kbps")
    ap1.cmd("tc class add dev ap1-eth2 parent 1:1 classid 1:10 htb rate 90kbps ceil 125kbps") #Sta1 Video
    #Zakomentowac ponisza linijke gry robimy DL video:
    #ap1.cmd("tc class add dev ap1-eth2 parent 1:1 classid 1:11 htb rate 124kbps ceil 250kbps") #Sta2 Video
    ap1.cmd("tc class add dev ap1-eth2 parent 1:1 classid 1:12 htb rate 1kbps ceil 125kbps") #Sta3 BE
    ap1.cmd("tc class add dev ap1-eth2 parent 1:1 classid 1:13 htb rate 34kbps ceil 125kbps") #Sta4 VoIP
    
    #Konfiguracja transmisji w kierunku DL (nie potrzeba dodawania algorytmu kolejkowania pfifo/sfq jako ze jest to jedyny ruch w tym kierunku)
    internet.cmd("tc qdisc add dev internet-eth0 root handle 1: htb default 180")
    internet.cmd("tc class add dev internet-eth0 parent 1: classid 1:1 htb rate 250kbps ceil 250kbps")
    internet.cmd("tc class add dev internet-eth0 parent 1:1 classid 1:11 htb rate 180kbps ceil 250kbps") #Sta2 Video
    

    #Konfiguracja portu ingressowego dla VLC ( sta2 obsluguje vlc)
    #Odkomentowa jak robimy DL
    #ap1.cmd("modprobe ifb")
    #ap1.cmd("ip link set dev ifb0 down")
    #ap1.cmd("ip link set dev ifb0 up")
    #ap1.cmd("tc qdisc add dev ifb0 root handle 1: htb default 10")
    #ap1.cmd("tc qdisc add dev ap1-eth2 ingress handle ffff:")
    #ap1.cmd("tc class add dev ifb0 parent 1: classid 1:1 htb rate 250kbps ceil 250kbps")
    #ap1.cmd("tc class add dev ifb0 parent 1:1 classid 1:12 htb rate 1kbps ceil 250kbps")
    #ap1.cmd("tc filter add dev ap1-eth2 protocol ip parent 1:0 prio 1 u32 match ip src 10.0.0.1 match ip dport 80 0xffff flowid 1:12")
 
    #ap1.cmd("tc filter add dev ap1-eth2 parent ffff: protocol ip u32 match u32 0 0 action connmark action mirred egress redirect dev ifb0 flowid ffff:1")
    
    sleep(0.5)
    ap1.cmd("tc filter add dev ap1-eth2 protocol ip parent 1:0 prio 1 u32 match ip src 10.0.0.2 match ip dport 50 0xffff flowid 1:10")
    #ap1.cmd("tc filter add dev ap1-eth2 protocol ip parent 1:0 prio 1 u32 match ip src 10.0.0.3 match ip dport 5005 0xffff flowid 1:11")
    ap1.cmd("tc filter add dev ap1-eth2 protocol ip parent 1:0 prio 2 u32 match ip src 10.0.0.4 match ip dport 80 0xffff flowid 1:12")
    ap1.cmd("tc filter add dev ap1-eth2 protocol ip parent 1:0 prio 3 u32 match ip src 10.0.0.5 match ip dport 25 0xffff flowid 1:13")

    internet.cmd("tc filter add dev internet-eth0 protocol ip parent 1:0 prio 1 u32 match ip src 10.0.0.1 match ip dport 5005 0xffff flowid 1:11")
    

    #Miejsce aby dodac algorytmy kolejkowania odpowiednie:
    #Pfifo/FIFO/SFQ

    sleep(0.5)
    ap1.cmd("tc qdisc add dev ap1-eth2 parent 1:10 handle 20: pfifo limit 5")  
    #ap1.cmd("tc qdisc add dev ap1-eth2 parent 1:11 handle 10: pfifo limit 5")
    #Odkomentowac gdy robimy DL i zakomentowac linijke powyzej
    #ap1.cmd("tc qdisc add dev ifb0 parent 1:11 handle 20: pfifo limit 5")
    ap1.cmd("tc qdisc add dev ap1-eth2 parent 1:13 handle 30: pfifo limit 5")
    ap1.cmd("tc qdisc add dev ap1-eth2 parent 1:12 handle 40: sfq perturb 10")

    #Uruchamianie iperfa 
    sleep(0.5)
    internet.cmd("iperf -s -u -p 50 -i 1 > internet_log1_2.txt &")
    #internet.cmd("iperf -s -u -p 5005 -i 1 > internet_log2.txt &")
    internet.cmd("iperf -s -p 80 -i 1 > internet_log3_2.txt &")
    internet.cmd("iperf -s -u -p 25 -i 1 > internet_log4_2.txt &")

    internet.cmd("tcpdump -i internet-eth0 -w jows-dl.pcap &")

    sta1.cmd("iperf -c 10.0.0.1 -p 50 -t 100 -u -b 1.5M &")
    sleep(5)
    sta3.cmd("iperf -c 10.0.0.1 -p 80 -t 140 &")
    sleep(5)
    sta4.cmd("iperf -c 10.0.0.1 -p 25 -t 120 -u -b 1.5M -l 160 &") #dlugosc pakietu 160 Bajtow
    sta2.cmd("vlc-wrapper &")
    sleep(5)
    internet.cmd("vlc-wrapper &")
    sleep(160)
    internet.cmd("sudo killall tcpdump")

    info("*** Running CLI\n")
    CLI_wifi(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
