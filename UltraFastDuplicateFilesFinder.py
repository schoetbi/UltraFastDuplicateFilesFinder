#!/usr/bin/python
"""
Ultra Fast Duplicate Files Finder

Deletes multiple files within a directory

Example use:

  ./UltraFastDuplicateFilesFinder.py - dir


To be fast the files are grouped by size first. Only if there are files
with the same size a md5 checksum will be performed.
"""

import sys
import os
import hashlib
import itertools

class FileInfo:
	filename = ""
	size = 0
	hash = ""

class DelStat:
    def __init__(self):
        self.nDupGroups = 0
        self.nDupFiles = 0
        self.sizeOfDups = 0
        self.deletedFileSize = 0
                
    def __add__(self, other):
        retstat = DelStat()
        retstat.nDupGroups = self.nDupGroups + other.nDupGroups
        retstat.nDupFiles = self.nDupFiles + other.nDupFiles
        retstat.sizeOfDups = self.sizeOfDups + other.sizeOfDups
        retstat.deletedFileSize = self.deletedFileSize + other.deletedFileSize
        return retstat

# read one CHUNK_SIZE bytes to check duplicates
CHUNK_SIZE = 1024

# buffer size when doing whole file md5
BUFFER_SIZE = 64*1024
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

def humanize_size(size):
	"""
	Return the file size as a nice, readable string.
	"""
	for limit, suffix in ((1024**3, 'GiB'), (1024**2, 'MiB'), (1024, 'KiB'), (1, 'B')):
		hsize = float(size) / limit
		if hsize > 0.5:
			return '%.2f %s' % (hsize, suffix)

def parseArgs(argv):
	import argparse
	parser = argparse.ArgumentParser(description='Find duplicate files.')
	parser.add_argument('-d', metavar='dir', action='append')
	parser.add_argument('-c', metavar='check', action='append')
	parser.add_argument('--dry', action='store_true')
	parser.add_argument('--nohash', action='store_true')
	parser.add_argument('--min-size', type=int)
	return parser.parse_args(argv)

def calculateHashes(filesBySize):
    print ('calculate hashes of ' + humanize_size(sizeToHash))
    sizeHashed = 0.0
    hashlist = {}
    for size, filesOfThisSize in filesBySize.iteritems():
            if len(filesOfThisSize) <= 1:
                    continue

            # calculate the hashes for this group
            for fn in filesOfThisSize:
                    h = get_file_hash(fn.filename)
                    if not hashlist.has_key(h):
                            hashlist[h] = []
                    
                    fn.hash=h
                    hashlist[h].append(fn)
                    sizeHashed += fn.size
                    sys.stdout.write('{0:.2%}                    \r'.format(sizeHashed / sizeToHash))

    # print the report
    print '%10s   %s' % ('size', 'filename')
    return hashlist

def deleteFileInfoGroup(fileinfos, delstat):
    if len(fileinfos) <= 1:
        return delstat

    print 20 * '-'
    
    delstat.nDupGroups += 1  
    delstat.nDupFiles += len(fileinfos)
    filesToDelete = []
    for fi in fileinfos:
        delstat.sizeOfDups += fi.size
        print '(%10s) %s' % (humanize_size(fi.size), fi.filename)
        if delpaths != None:
            for dp in delpaths:
                if fi.filename.find(dp) >= 0:
                    filesToDelete.append(fi)

    if len(fileinfos) == len(filesToDelete):
            # do not delete all files. Keep the first one
            keep = filesToDelete[0]
            print('keep %s' % keep.filename)
            filesToDelete.remove(keep)

    for toDel in filesToDelete:
            if not dryRun:
                    os.remove(toDel.filename)
                    print ('deleted %s' % toDel.filename)
            else:
                    print ('simulate deletion of %s' % toDel.filename)
            
            delstat.deletedFileSize += toDel.size
    
    return delstat

def deleteByHash(hashlist, delstat):
    for hl,fileinfos in sorted(hashlist.iteritems(), key=lambda(k,v):v[0].size):
        deleteFileInfoGroup(fileinfos, delstat)
        
    return delstat

def delBySize(filesBySize, delstat):
    for size, filesOfThisSize in filesBySize.iteritems():
        if len(filesOfThisSize) <= 1:
            continue
        
        deleteFileInfoGroup(filesOfThisSize, delstat)
        
    return delstat

args = parseArgs(sys.argv[1:])
delpaths = [os.path.abspath(abs) for abs in args.d]
if delpaths == None:
	delpaths = {}

dryRun = args.dry
min_size = args.min_size

files = {}
totalsize = 0
totalfiles = 0

rootDirs = delpaths + args.c

# we start here by checking all filesizes
for path, directories, filelist in itertools.chain.from_iterable(os.walk(path) for path in rootDirs):
	for relFileName in filelist:
		filename = os.path.join(path, relFileName)

		if not os.path.isfile(filename):
			continue
			
		size = os.path.getsize(filename)
		if size < min_size:
			continue
		
		fi = FileInfo()
		fi.filename = filename
		fi.size = size
		files[filename] = fi
		totalfiles += 1
		totalsize += size
		sys.stdout.write('%d files (%s)           \r' % (totalfiles, humanize_size(totalsize)))

print ''
print ("group by size")

# group files by size
filesBySize = {}
sizeToHash = 0
for f in files.values():
	if not filesBySize.has_key(f.size):
		filesBySize[f.size] = []
	filesBySize[f.size].append(f)
	lGroup = len(filesBySize[f.size])
	if lGroup == 2:
		sizeToHash += 2*f.size
	if lGroup > 2:
		sizeToHash += f.size

delstat = DelStat()
if (args.nohash):
    delBySize(filesBySize, delstat)
else:
    hashlist = calculateHashes(filesBySize)
    deleteByHash(hashlist, delstat)
 
# final summary
print 20*'-'
print 'found %d groups with %d duplicate files with a total size of %s' % \
 (delstat.nDupGroups, delstat.nDupFiles, humanize_size(delstat.sizeOfDups))
print 'deletedFileSize %s'% humanize_size(delstat.deletedFileSize)
