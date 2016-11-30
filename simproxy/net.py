from socket import socket, AF_INET, SOCK_STREAM
import base64, json, time, sys, msgpack, struct

class PackBase(object):
    # Package struct implement Hub Protocol 

    _headerSync = '\x05\x00\x0B\x00'
    _version = 1
    _headerLen = 14

    def dump(self):
        # Dump the package to bytes.
        #   Will generate a new session id if self.sid is None. 

        bodyPacked = msgpack.packb(self.body) if self.body != None else ""
        sidPacked = '' if self.sid == None else uuid.UUID(hex=self.sid).bytes
        header = struct.pack("!4sccHHc3s", self._headerSync, chr(self._version), chr(self._flags), self.apiRet, self.id, chr(len(sidPacked)), struct.pack("!I", len(bodyPacked))[1:])
        return header + sidPacked + bodyPacked

    def __init__(self, id, apiRet, sid, body):
        # @param id:          Package id, unique in socket.
        # @param apiRet:      Route code to match the route api in Request package, Route return code in Respond package
        # @param sid:         Session id
        # @param body:        Package body, should be array or hash

        self.id, self.apiRet, self.sid, self.body  = id, apiRet, sid, body
        self.routeCode = None
        self._TPack = None
        self._PPack = None

    def length(self):
        sidLen = 0 if self.sid == '' else len(uuid.UUID(hex=self.sid).bytes)
        return self._headerLen + sidLen + len(msgpack.packb(self.body) if self.body != None else "")

class TPack(PackBase):
    # Request Package inherit from PackBase
    #   See Wiki for more: http://192.168.6.66/projects/sim/wiki/Hub%E5%8D%8F%E8%AE%AE

    _flags = 0x00

    def __init__(self, id, apiRet, sid, body):
        PackBase.__init__(self, id, apiRet, sid, body)
        self.routeCode = apiRet

    def peerToPPack(self, pp):
        self._PPack = pp
        return self

class DPack(PackBase):
    # Respond Package inherit from PackBase
    #   See Wiki for more: http://192.168.6.66/projects/sim/wiki/Hub%E5%8D%8F%E8%AE%AE

    _flags = 0x80

    def peerToTPack(self, tp):
        self._TPack = tp
        self.routeCode = tp.routeCode
        self._PPack = tp._PPack
        return self

class SimProxySck():
    def __init__(self):
        self.start()
        # self.sck.connect(('114.215.209.188', 9898))

    def start(self):
        self.buf = ''
        self.addr = ('192.168.6.151', 7878)
        # self.addr = ('114.215.209.188', 9898)
        # self.addr = ('115.29.241.227', 9898)
        self.sck = socket(AF_INET, SOCK_STREAM)
        self.sck.connect(self.addr)

    def sendT(self, pid, apiRet, body):
        self.sck.send(TPack(pid, apiRet, None, body).dump())
        return self.recvPack()

    def sendD(self, pid, apiRet, body):
        self.sck.send(DPack(pid, apiRet, None, body).dump())
        return self.recvPack()

    def recvPack(self):
        st = time.time()
        pack = None
	time.sleep(1)
        self.buf = (self.buf + self.sck.recv(1024))
        bufLen = len(self.buf)
        while bufLen > 4:
            self.buf, pack = self.packLoads(self.buf)
            if len(self.buf) == bufLen: break
            bufLen = len(self.buf)
	return pack

    def packLoads(self, buf):
    # Load TPack or DPack from socket buffer
    #   return remaining buffer and parsed Pack
    #   -*- TODO -*- : Make it into SHProtocol class, global method is not good

        if len(buf) < 4: return buf, None

        idx = buf.find(PackBase._headerSync)
        if idx < 0:
            print "no header_sync, drop", len(buf)-3
            return buf[-3:], None
        elif idx > 0:
            print "some noise before header_sync, drop", idx
            buf = buf[idx:]

        if len(buf) < PackBase._headerLen: return buf, None

        sync, ver, flags, apiRet, packid, sidLen, bodyLen = struct.unpack("!4sccHHc3s", buf[:PackBase._headerLen])
        ver = ord(ver)
        flags = ord(flags)
        sidLen = ord(sidLen)
        bodyLen, = struct.unpack("!I",'\x00'+bodyLen)

        if ver == PackBase._version and (flags & 0xffffff3f) == 0 and (sidLen == 0 or sidLen == 16) : pass
        else:
            print "header check error, drop", 1
            return buf[1:], None

        pkgLen = PackBase._headerLen + sidLen + bodyLen
        if len(buf) < pkgLen: return buf, None
        elif len(buf) > pkgLen:
            if not buf[pkgLen:].startswith(PackBase._headerSync[:len(buf)-pkgLen]):
                print "header_sync after body check error, drop", 1
                return buf[1:], None

        sid = buf[PackBase._headerLen : PackBase._headerLen+sidLen]
        if sidLen == 16: sid = uuid.UUID(bytes=sid).hex
        bodyStr  = buf[PackBase._headerLen+sidLen : pkgLen]

        if len(bodyStr) == 0: body = None
        else:
            try:
                body = msgpack.unpackb(bodyStr, encoding = 'utf-8')
            except Exception, e:
                print "body decode error, drop", pkgLen
                return buf[pkgLen:], None

        pack = TPack(packid, apiRet, sid, body) if flags == 0x00 else DPack(packid, apiRet, sid, body)
        
        return buf[pkgLen:], pack

    def close(self):
        self.sck.close()
        self.sck = None

