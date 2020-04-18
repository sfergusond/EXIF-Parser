"""
Created on Fri Feb 15 21:07:29 2019

@author: sferg
"""
import struct
import tags
import argparse

class ExifParseError(Exception):
    """
    An exception representing a failure to parse a JPEG for a valid Exif tag.
    """
    def init(self):
        pass

def carve(f, start, end):
    f.seek(start)
    carve = f.read(end - start)
    return carve

def find_jfif(f, max_length = None):  
    offset = 0
    data = f.read()
    list_pairs = []
    
    while offset < len(data) - 1:
        soi = struct.unpack('>H', data[offset:offset + 2])
        
        if soi[0] == 0xFFD8:
            soi_offset = offset
            eoi_offset = offset + 2
            
            if type(max_length) is int:
                while (eoi_offset + 1) - soi_offset < max_length and eoi_offset < len(data) - 1:
                    eoi = struct.unpack('>H', data[eoi_offset:eoi_offset + 2])
                    if eoi[0] == 0xFFD9:
                        list_pairs.append((soi_offset, eoi_offset + 1))
                    eoi_offset += 1
            else:
                while eoi_offset < len(data) - 1:
                    eoi = struct.unpack('>H', data[eoi_offset:eoi_offset + 2])
                    if eoi[0] == 0xFFD9:
                        list_pairs.append((soi_offset, eoi_offset + 1))
                    eoi_offset += 1

        offset += 1
        
    return list_pairs

def parse_exif(f):
    endian = True # Big Endian = true
    data = f.read()
    
    # Check SOI marker
    if struct.unpack('>H', data[0:2])[0] != 0xFFD8:
        raise ExifParseError(Exception) # raise ExifParseError here!
    
    # Find EXIF segment, determine big/little endian, find # of entries
    exif = data[find_exif(data) - 1:]
    byte_order = struct.unpack('BB', exif[10:12])
    if chr(byte_order[0]) == 'I' and chr(byte_order[1]) == 'I':
        endian = False # Little endian
    ifd_offset = unpack(endian, 'I', exif[14:18], 0)       
    bom = exif[10:]
    entries = unpack(endian, 'H', bom[ifd_offset:ifd_offset + 2], 0)
    
    return parse_ifd(bom, bom[ifd_offset + 2:], endian, entries, 0)
    
def parse_ifd(bom, ifd, end, entries, recur):
    ifd_dict = {}
    i = 0    
 
    for j in range(entries):
        key = unpack(end, 'H', ifd[i:i+2], 0)
        if key in tags.TAGS:
            _format = unpack(end, 'H', ifd[i+2:i+4], 0) # Format
            
            if 1 <= _format <= 7 and _format != 6:
                comp = unpack(end, 'I', ifd[i+4:i+8], 0) # Components
                value = parse_value(_format, comp, ifd[i+8:i+12], bom, end) # Data Field
                
                if tags.TAGS[key] in ifd_dict:
                    if type(value) is list:
                        ifd_dict[tags.TAGS.get(key)] += value
                    else:
                        ifd_dict[tags.TAGS.get(key)].append(value)
                else:
                    if type(value) is list:
                        ifd_dict.setdefault(tags.TAGS.get(key), value)
                    else:
                        ifd_dict.setdefault(tags.TAGS.get(key), [value])
            else:
                ifd_dict[tags.TAGS.get(key)] = None
        i += 12
    
    next_ifd_offset = unpack(end, 'L', ifd[i:i+4], 0) # Find next IFD
    
    if next_ifd_offset != 0: # Recursive parsing of next IFDs
        next_ifd_entries = unpack(end, 'H', bom[next_ifd_offset:next_ifd_offset+2], 0)
        next_ifd = bom[next_ifd_offset + 2:]
        next_ifd_dict = parse_ifd(bom, next_ifd, end, next_ifd_entries, recur + 1)
        
        for e in next_ifd_dict: 
            if e in ifd_dict:
                if type(next_ifd_dict[e]) is list:
                    ifd_dict[e] += next_ifd_dict[e]
                else:
                    ifd_dict[e].append(next_ifd_dict[e])
            else:
                if type(next_ifd_dict[e]) is list:
                    ifd_dict.setdefault(e, next_ifd_dict[e])
                else:
                    ifd_dict.setdefault(e, next_ifd_dict[e])
    
    return ifd_dict


def parse_value(_format, comp, data, bom, end):
    offset = unpack(end, 'L', data[0:4], 0)
    if _format == 1: # Unsigned byte
        return struct.unpack('>B', data[0:1])
    elif _format == 2: # ASCII string
        size = comp * 1
        string = ""
        i = 1
        if size <= 4:
            char = struct.unpack('B', data[0:1])[0]
            while char != 0:
                string += chr(char)
                char = struct.unpack('B', data[i:i+1])[0]
                i += 1
            return string
        else:
            data_field = bom[offset:offset + size]
            char = struct.unpack('B', data_field[0:1])[0]
            string = ""
            while char != 0:
                string += chr(char)
                char = struct.unpack('B', data_field[i:i+1])[0]
                i += 1
            return string
    elif _format == 3: # Unsigned short
        size = comp * 2
        li = []
        if size <= 4:
            for i in range(comp):
                li.append(unpack(end, 'H', data[i*2:i*2+2], 0))
            return li
        else:
            data_field = bom[offset:offset + size]
            for i in range(comp):
                li.append(unpack(end, 'H' * comp, data_field[0:size], i))
            return li
    elif _format == 4: # Unsigned long
        return unpack(end, 'L', data[0:4], 0)
    elif _format == 5: # Unsigned rational
        data_field = bom[offset:offset + 8] 
        return "{}/{}".format(unpack(end, 'LL', data_field, 0), unpack(end, 'LL', data_field, 1))
    else: # Undefined (raw)
        size = comp * 1
        li = []
        data_field = bom[offset:offset + size]
        if size <= 4:
            for i in range(size):
                li.append("{:x}".format(struct.unpack('B', data[i:i+1])[0]))
                return ''.join(li)
        else:
            for i in range(size):
                li.append("{:x}".format(struct.unpack('B', data_field[i:i+1])[0]))
            return ''.join(li)
        
def find_exif(f):
    i = 0
    scan = 0
    while scan != 0xFFE1 and i < len(f) - 1:
        scan = struct.unpack('>H', f[i:i+2])[0]
        i += 1
    if scan != 0xFFE1:
        raise ExifParseError(Exception)
    return i

def unpack(endian, _type, buffer, index):
    _format = ''
    if endian == True:
        _format = '>'
    else:
        _format = '<'
    _format += _type
    return struct.unpack(_format, buffer)[index]
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    
    args = parser.parse_args()

    with open(args.filename, 'rb') as f:
        _dict = parse_exif(f)
    
    print(_dict)
        
if __name__ == '__main__':
    main()