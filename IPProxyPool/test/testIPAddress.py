#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os

import socket
import struct

import logging


logger = logging.getLogger('util')


class IPAddresss:
    def __init__(self, ipdbFile):
        """
        Initialize database

        Args:
            self: (todo): write your description
            ipdbFile: (str): write your description
        """
        self.ipdb = open(ipdbFile, "rb")
        str = self.ipdb.read(8)
        (self.firstIndex, self.lastIndex) = struct.unpack('II', str)
        self.indexCount = int((self.lastIndex - self.firstIndex) / 7 + 1)
        # print self.getVersion(), u" 纪录总数: %d 条 "%(self.indexCount)

    def getVersion(self):
        """
        Get the version of the server.

        Args:
            self: (todo): write your description
        """
        s = self.getIpAddr(0xffffff00)
        return s

    def getAreaAddr(self, offset=0):
        """
        Return the ip address of the address.

        Args:
            self: (todo): write your description
            offset: (int): write your description
        """
        if offset:
            self.ipdb.seek(offset)
        str = self.ipdb.read(1)
        (byte,) = struct.unpack('B', str)
        if byte == 0x01 or byte == 0x02:
            p = self.getLong3()
            if p:
                return self.getString(p)
            else:
                return ""
        else:
            self.ipdb.seek(-1, 1)
            return self.getString(offset)

    def getAddr(self, offset, ip=0):
        """
        Get an ip address from the packet.

        Args:
            self: (todo): write your description
            offset: (int): write your description
            ip: (todo): write your description
        """
        self.ipdb.seek(offset + 4)
        countryAddr = ""
        areaAddr = ""
        str = self.ipdb.read(1)
        (byte,) = struct.unpack('B', str)
        if byte == 0x01:
            countryOffset = self.getLong3()
            self.ipdb.seek(countryOffset)
            str = self.ipdb.read(1)
            (b,) = struct.unpack('B', str)
            if b == 0x02:
                countryAddr = self.getString(self.getLong3())
                self.ipdb.seek(countryOffset + 4)
            else:
                countryAddr = self.getString(countryOffset)
            areaAddr = self.getAreaAddr()
        elif byte == 0x02:
            countryAddr = self.getString(self.getLong3())
            areaAddr = self.getAreaAddr(offset + 8)
        else:
            countryAddr = self.getString(offset + 4)
            areaAddr = self.getAreaAddr()
        return countryAddr + " " + areaAddr

    def dump(self, first, last):
        """
        Dump the icalculate the i. ipdb file.

        Args:
            self: (todo): write your description
            first: (todo): write your description
            last: (todo): write your description
        """
        if last > self.indexCount:
            last = self.indexCount
        for index in range(first, last):
            offset = self.firstIndex + index * 7
            self.ipdb.seek(offset)
            buf = self.ipdb.read(7)
            (ip, of1, of2) = struct.unpack("IHB", buf)
            address = self.getAddr(of1 + (of2 << 16))
            # 把GBK转为utf-8
            address = str(address, 'gbk').encode("utf-8")
            logger.info("%d %s %s" % (index, self.ip2str(ip), address))

    def setIpRange(self, index):
        """
        Set the ip address } range

        Args:
            self: (todo): write your description
            index: (int): write your description
        """
        offset = self.firstIndex + index * 7
        self.ipdb.seek(offset)
        buf = self.ipdb.read(7)
        (self.curStartIp, of1, of2) = struct.unpack("IHB", buf)
        self.curEndIpOffset = of1 + (of2 << 16)
        self.ipdb.seek(self.curEndIpOffset)
        buf = self.ipdb.read(4)
        (self.curEndIp,) = struct.unpack("I", buf)

    def getIpAddr(self, ip):
        """
        Get the ip address of the ip address.

        Args:
            self: (todo): write your description
            ip: (todo): write your description
        """
        L = 0
        R = self.indexCount - 1
        while L < R - 1:
            M = int((L + R) / 2)
            self.setIpRange(M)
            if ip == self.curStartIp:
                L = M
                break
            if ip > self.curStartIp:
                L = M
            else:
                R = M
        self.setIpRange(L)
        # version information, 255.255.255.X, urgy but useful
        if ip & 0xffffff00 == 0xffffff00:
            self.setIpRange(R)
        if self.curStartIp <= ip <= self.curEndIp:
            address = self.getAddr(self.curEndIpOffset)
            # 把GBK转为utf-8
            address = str(address)
        else:
            address = "未找到该IP的地址"
        return address

    def getIpRange(self, ip):
        """
        Return the ip range of the ip address

        Args:
            self: (todo): write your description
            ip: (todo): write your description
        """
        self.getIpAddr(ip)
        range = self.ip2str(self.curStartIp) + ' - ' \
                + self.ip2str(self.curEndIp)
        return range

    def getString(self, offset=0):
        """
        Get a string representation of this string.

        Args:
            self: (todo): write your description
            offset: (int): write your description
        """
        if offset:
            self.ipdb.seek(offset)
        str = b''
        ch = self.ipdb.read(1)
        (byte,) = struct.unpack('B', ch)
        while byte != 0:
            str += ch
            ch = self.ipdb.read(1)
            (byte,) = struct.unpack('B', ch)
        return str.decode('gbk')

    def ip2str(self, ip):
        """
        Convert ip address to network string.

        Args:
            self: (todo): write your description
            ip: (todo): write your description
        """
        return str(ip >> 24) + '.' + str((ip >> 16) & 0xff) + '.' + str((ip >> 8) & 0xff) + '.' + str(ip & 0xff)

    def str2ip(self, s):
        """
        Convert a ipv6 address to a network address.

        Args:
            self: (todo): write your description
            s: (todo): write your description
        """
        (ip,) = struct.unpack('I', socket.inet_aton(s))
        return ((ip >> 24) & 0xff) | ((ip & 0xff) << 24) | ((ip >> 8) & 0xff00) | ((ip & 0xff00) << 8)

    def getLong3(self, offset=0):
        """
        Read a 4 bytes from the given offset.

        Args:
            self: (todo): write your description
            offset: (int): write your description
        """
        if offset:
            self.ipdb.seek(offset)
        str = self.ipdb.read(3)
        (a, b) = struct.unpack('HB', str)
        return (b << 16) + a


QQWRY_PATH = os.path.dirname(__file__) + "/../data/qqwry.dat"
ips = IPAddresss(QQWRY_PATH)
addr = ips.getIpAddr(ips.str2ip('183.61.236.53'))
print(addr)
