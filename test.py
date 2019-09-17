#!/usr/bin/env python3
# This program makes some hard-coded output in the style of cdb-dump. It
# should be piped directly to cdbmake or cdb

import sys
out = sys.stdout.buffer

RR_TYPE_A = 1
RR_TYPE_TXT = 16
RR_TYPE_AAAA = 28

def ipv4_to_u32(ipv4):
    parts = ipv4.split('.')
    if len(parts) != 4:
        raise Exception("invalid IPv4 address")
    res = 0
    for part in parts:
        res <<=8
        res |= int(part)
    return res

def u_to_bytes(u, bits):
    if bits & 0x7:
        raise Exception("Extra bits; not byte aligned")
    byte_count = bits >> 3
    res = []
    for i in range(byte_count):
        res.append(u & 0xff)
        u >>= 8
    res.reverse()
    return bytes(res)

def u16_to_bytes(u16):
    return u_to_bytes(u16, 16)

def u32_to_bytes(u32):
    return u_to_bytes(u32, 32)

def u64_to_bytes(u64):
    return u_to_bytes(u64, 64)

#print(bytes(u32_to_bytes(ipv4_to_u32(address))).hex(), flush=True)
#out.write(bytes(u32_to_bytes(ipv4_to_u32(address))))

def name_to_labels(name):
    parts = name.split('.')
    return parts

def labels_to_dns(labels):
    # TODO: Handle unicde to punicode or whatever
    res = []
    for part in labels:
        p = part.encode('ascii')
        l = len(part)
        if l == 0 or l > 255:
            raise Exception("bad label length {}".format(l))
        res.append(bytes([l]) + p)
    res.append(bytes([0])) # NULL aka root label
    return b''.join(res)

def overlay(given, defaults):
    """Pull elements from given until we run out, then use defaults
    also, use defaults if an element in given is empty (that is, None or '')
    """
    l1 = len(given)
    l2 = len(defaults)
    rem = l2 - l1
    res = []
    for i in range(min(l1,l2)):
        if given[i] in [None, '']:
            res.append(defaults[i])
        else:
            res.append(given[i])
    if l1 < l2:
        res.extend(defaults[l2 - rem:])
    return res

def make_record(name, type_, loc, ttl, ttd, data):
    key = labels_to_dns(name_to_labels(name))
    if loc is None:
        value = u16_to_bytes(type_) + b'=' + u32_to_bytes(ttl) + u64_to_bytes(ttd) + data
    else:
        loc = loc.encode('ascii')
        if len(loc) != 2:
            raise Exception("Bad loc")
        value = u16_to_bytes(type_) + b'>' + loc + u32_to_bytes(ttl) + u64_to_bytes(ttd) + data
    klen = len(key)
    vlen = len(value)
    record = "+{},{}:".format(klen,vlen).encode('ascii') + key + b'->' + value + bytes((0x0a,))
    return record

with open("data") as data:
    for line in data:
        line = line.rstrip()
        if len(line) == 0 or line[0] == '#':
            continue
        rtype = line[0]
        line = line[1:]
        if rtype == '+':
            defaults = [None, None, "86400", "0", None]
            givenfields = line.split(':')
            fields = overlay(givenfields, defaults)
            name = fields[0]
            address = fields[1]
            ttl = int(fields[2])
            ttd = int(fields[3],16)
            loc = fields[4]
            data = u32_to_bytes(ipv4_to_u32(address))
            out.write(make_record(name, RR_TYPE_A, loc, ttl, ttd, data))


# Finally, after the last record is an extra newline
out.write(b'\n')
