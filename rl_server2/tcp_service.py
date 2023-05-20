import threading
import socket
import select
import errno
import logging
import byte_codec as bc
import piero_message as pmsg
class TcpPeer(object):
    def __init__(self,server,conn):
        self.server=server
        self.conn=conn
        self.buffer=b''
        self.dead=False
    def __del__(self):
        pass
    def incoming_data(self,buffer):
        self.buffer+=buffer
        reader=bc.DataReader()
        reader.append(self.buffer)
        all=len(self.buffer)
        sum,success=reader.read_varint()
        remain=b''
        close=False
        if success and sum>0:
            sum_bytes=all-reader.byte_remain()
            if sum<=reader.byte_remain():
                type,_=reader.read_uint8()
                last,_=reader.read_uint8()
                mid,_=reader.read_varint()
                agent_id,_=reader.read_varint()
                message=pmsg.MessageBufferWrap(self.conn.fileno(),agent_id,self.buffer[0:sum+sum_bytes])
                if sum+sum_bytes<all:
                    remain=self.buffer[sum+sum_bytes:all]
                self.server.handele_request(message)
                self.buffer=remain
            return close
    def send_responce(self,res):
        if self.dead is False:
            sum=7
            type=1
            writer=bc.DataWriter()
            writer.write_varint(sum)
            writer.write_uint8(type)
            writer.write_uint8(res.choice)
            writer.write_uint8(res.terminate)
            writer.write_uint32(res.downloadDelay)
            self.conn.sendall(writer.content())
            if res.terminate:
                self.dead=True
    def read_event(self):
        close=False
        buffer=b''
        length=0
        try:
            while True:
                msg=self.conn.recv(1500)
                length+=len(msg)
                if msg:
                    buffer+=msg
                else:
                    if buffer:
                        self.incoming_data(buffer)
                        buffer=b''
                    #print("only close")
                    close=True
                    break
        except socket.error as e:
            err = e.args[0]
            #print ("error: "+str(err))
            if buffer:
                ret=self.incoming_data(buffer)
                if ret:
                   close=True
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                pass
            else:
                close=True
        return close
    def close_fd(self):
        self.dead=True
        self.conn.close()
class TcpServer():
    def __init__(self, mode, port,state_pipes,id_span):
        self._thread = None
        self._thread_terminate = False
        if mode == "localhost":
            self.ip = mode
        elif mode == "public":
            self.ip ="0.0.0.0"
        else:
            self.ip ="127.0.0.1"
        self.port = port
        self.state_pipes=state_pipes
        self.id_span=id_span
        self.logger = logging.getLogger("rl")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.ip, self.port))
        self._socket.setblocking(False)
        self.peers={}
        self._socket.listen(128)
        self._epl= select.epoll()
        self._epl.register(self._socket.fileno(),select.EPOLLIN)
    def handele_request(self,message):
        index=int(message.agent_id/self.id_span)
        self.state_pipes[index][0].send(message)
    def check_pipe(self):
        for i in range(len(self.state_pipes)):
            res=None
            if self.state_pipes[i][0].poll(0):
                try:
                   res=self.state_pipes[i][0].recv()
                except EOFError:
                    self.logger.debug("pipe read error {}".format(i))
            if res:
                peer=self.peers.get(res.fd)
                assert peer
                if peer:
                    peer.send_responce(res)
    def loop_start(self):
        if self._thread is not None:
            return 
        self._thread_terminate = False
        self._thread = threading.Thread(target=self._thread_main)
        #self._thread.daemon = True
        self._thread.start()
    def loop_stop(self, force=False):
        if self._thread is None:
            return
        self._thread_terminate = True
        if threading.current_thread() != self._thread:
            self._thread.join()
            self._thread = None
    def loop_once(self):
        epoll_list = self._epl.poll(0)
        for fd,events in epoll_list:
            if fd == self._socket.fileno():
                conn,addr =self._socket.accept()
                conn.setblocking(False)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                peer=TcpPeer(self,conn)
                self.peers.update({conn.fileno():peer})
                self._epl.register(conn.fileno(), select.EPOLLIN)
            elif events == select.EPOLLIN:
                ret=self.peers[fd].read_event()
                if ret:
                    #print("close")
                    self._close(fd)
        self.check_pipe()
        for fd in list(self.peers.keys()):
            if self.peers[fd].dead:
                self._close(fd)
    def _thread_main(self):
        while True:
            self.loop_once()
            if self._thread_terminate is True:
                self.shutdown()
                break
    def _close(self,fd):
        if fd==self._socket.fileno():
            self._epl.unregister(fd)
            self._socket.close()
        elif fd in self.peers:
            self._epl.unregister(fd)
            self.peers[fd].close_fd()
            self.peers.pop(fd)
    def shutdown(self):
        for fd, peer in self.peers.items():
            self._epl.unregister(fd)
            peer.close_fd()
        self.peers.clear()
        self._close(self._socket.fileno())
        self._epl.close()
