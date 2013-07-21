#!/usr/bin/python
# -*- coding: utf-8 -*-
#

"""
Ultra Fast Duplicate Files Finder
=================================
  by Gautier Portet <kassoulet gmail com>


Takes a list of file from stdin.
And print the duplicate ones.


example use:

  find ~/ -size +10M | ./UltraFastDuplicateFilesFinder.py

to find duplicates in your home folder, all files more than 10MB.

UltraFastDuplicateFilesFinder compares only the very beginning of the files.
Its sufficient for most uses, but use with caution.

But this way is quite useful to detect duplicates within corrupted media files...


this is public domain.
"""

import sys
import os
import hashlib
import itertools

# read one CHUNK_SIZE bytes to check duplicates
CHUNK_SIZE = 1024

# buffer size when doing whole file md5
BUFFER_SIZE = 64*1024


class FileInfo:
    filename = ""
    size = 0
    hash = ""

def get_file_hash(filename, limit_size=None, buffer_size=BUFFER_SIZE):
    """
    Return the md5 hash of given file as an hexadecimal string.
    
    limit_size can be used to read only the first n bytes of file.
    """
    # open file

    try:
        f = file(filename, "rb")
    except IOError:
        return 'NONE'

    # get md5 hasher
    hasher = hashlib.md5()
    
    if limit_size:
        # get the md5 of beginning of file
        chunk = f.read(limit_size)
        hasher.update(chunk)
    else:        
        # get the md5 of whole file
        chunk = True
        while chunk:
            chunk = f.read(buffer_size)
            hasher.update(chunk)

    f.close()
    return hasher.hexdigest()

delpaths = ''
if len(sys.argv) > 1 and sys.argv[1] == '-d':
    delpaths = sys.argv[2].split(';')
    print(delpaths)

files = {}
hashlist = {}
totalsize = 0
totalfiles = 0

def humanize_size(size):
    """
    Return the file size as a nice, readable string.
    """
    for limit, suffix in ((1024**3, 'GiB'), (1024**2, 'MiB'), (1024, 'KiB'), (1, 'B')):
        hsize = float(size) / limit
        if hsize > 0.5:
            return '%.2f %s' % (hsize, suffix)

# we start here by checking all filesizes
for filename in sys.stdin:
    filename = filename.strip()
    if not os.path.isfile(filename):
        continue
        
    size = os.path.getsize(filename)
    
    fi = FileInfo()
    fi.filename = filename
    fi.size = size
    files[filename] = fi
    totalfiles += 1
    totalsize += size
    sys.stdout.write('%d files (%s)           \r' % (totalfiles, humanize_size(totalsize)))

print ''
# print the report
print '%10s   %s' % ('size', 'filename')

# group files by size
selFsize = lambda fi:fi.size
filenamesBySize = sorted(files.values(), key=selFsize)
for k, g in itertools.groupby(filenamesBySize, selFsize):
    filesOfThisSize = list(g)
    if len(filesOfThisSize) <= 1:
        continue
        
    # calculate the hashes for this group
    for fn in filesOfThisSize:     
        h = get_file_hash(fn.filename)
        if not hashlist.has_key(h):
        	hashlist[h] = []
        
        fn.hash=h
        hashlist[h].append(fn)

nDupGroups = 0
nDupFiles = 0
sizeOfDups = 0
deleted = 0
for hl,fileinfos in sorted(hashlist.iteritems(), key=lambda(k,v):v[0].size):
    if len(fileinfos) > 1:
        print 20 * '-'
        
        nDupGroups += 1  
        nDupFiles += len(fileinfos)          
        for fi in fileinfos:
            sizeOfDups += fi.size
            print '(%10s) %s' % (humanize_size(fi.size), fi.filename)
            for dp in delpaths:
                if fi.filename.find(dp) == 0:
                    os.remove(fi.filename)
                    deleted += fi.size
                    print ('deleted')
# final summary
print 20*'-'
print 'found %d groups with %d duplicate files with a total size of %s' % \
 (nDupGroups, nDupFiles, humanize_size(sizeOfDups))
print 'deleted %s'% humanize_size(deleted)
