"""

 (c) Copyright Ascensio System SIA 2021
 *
 The MIT License (MIT)

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.

"""


from asyncio.windows_events import NULL
import config
import os
import shutil
import io
import re
import requests
import time
import urllib.parse
import magic

from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from todo import settings
from . import fileUtils, historyManager
from django.contrib.auth.decorators import login_required

LANGUAGES = {
    'en': 'English',
    'be': 'Belarusian',
    'bg': 'Bulgarian',
    'ca': 'Catalan',
    'zh': 'Chinese',
    'cs': 'Czech',
    'da': 'Danish',
    'nl': 'Dutch',
    'fi': 'Finnish',
    'fr': 'French',
    'de': 'German',
    'el': 'Greek',
    'hu': 'Hungarian',
    'id': 'Indonesian',
    'it': 'Italian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'lv': 'Latvian',
    'lo': 'Lao',
    'nb': 'Norwegian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'es': 'Spanish',
    'sv': 'Swedish',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'vi': 'Vietnamese'
}

def isCanFillForms(ext):
    return ext in config.DOC_SERV_FILLFORMS

# check if the file extension can be viewed
def isCanView(ext):
    return ext in config.DOC_SERV_VIEWED

# check if the file extension can be edited
def isCanEdit(ext):
    return ext in config.DOC_SERV_EDITED

# check if the file extension can be converted
def isCanConvert(ext):
    return ext in config.DOC_SERV_CONVERT

# check if the file extension is supported by the editor (it can be viewed or edited or converted)
def isSupportedExt(ext):
    return isCanView(ext) | isCanEdit(ext) | isCanConvert(ext) | isCanFillForms(ext)

# get internal extension for a given file type
def getInternalExtension(fileType):
    mapping = {
        'word': '.docx',
        'cell': '.xlsx',
        'slide': '.pptx',
        'docxf': '.docxf'
    }

    return mapping.get(fileType, '.docx') # the default file type is .docx

# get image url for templates
def getTemplateImageUrl(fileType, request):
    path = getServerUrl(True, request) + '/static/images/'
    mapping = {
        'word': path + 'file_docx.svg',
        'cell': path + 'file_xlsx.svg',
        'slide': path + 'file_pptx.svg'
    }

    return mapping.get(fileType, path + 'file_docx.svg') # the default file type

# get file name with an index if such a file name already exists
def getCorrectName(filename, req):
    basename = fileUtils.getFileNameWithoutExt(filename)
    ext = fileUtils.getFileExt(filename)
    name = f'{basename}{ext}'

    i = 1
    while os.path.exists(getStoragePath(name, req)): # if file with such a name already exists
        name = f'{basename} ({i}){ext}'  # add an index to its name
        i += 1

    return name

# get server url
def getServerUrl (forDocumentServer, req):
    if (forDocumentServer and config.EXAMPLE_DOMAIN is not None):
        return  config.EXAMPLE_DOMAIN 
    else:
        return req.headers.get("x-forwarded-proto") or req.scheme + "://" + req.get_host()

# get file url
def getFileUri(filename, forDocumentServer, req):
    host = getServerUrl(forDocumentServer, req)
    curAdr = req.META['REMOTE_ADDR']
    #username = getUserFolder(req)
    #print (username+' getFileuri')
    #return f'{host}{settings.STATIC_URL}{curAdr}/dimar/{filename}'
    return f'{host}{settings.STATIC_URL}{curAdr}/{filename}'
    #print (host+settings.STATIC_URL+curAdr+'/'+username+'/'+filename+ '  getFileUri')
   # return f'{host}{settings.STATIC_URL}{curAdr}/{username}/{filename}'
    

# get absolute URL to the document storage service
def getCallbackUrl(filename, req):
    host = getServerUrl(True, req)
    curAdr = req.META['REMOTE_ADDR']
    #username = getUserFolder(req)
    #print (username+' username getCallbackUrl')
    #return f'{host}/dimar/track?filename={filename}&userAddress={curAdr}'
    if req.user.is_authenticated == True:
        return f'{host}/track?filename={filename}&userAddress={curAdr}/'
    #print(f'{host}/track?filename={filename}&userAddress={curAdr}/{username}'+'  getCallbackUrl')
    #return f'{host}/track?filename={filename}&userAddress={curAdr}/{username}'
    

# get url to the created file
def getCreateUrl(fileType, req):
    host = getServerUrl(False, req)
    #username = getUserFolder(req)
    return f'{host}/create?fileType={fileType}'
    #return f'{host}/dimar/create?fileType={fileType}'

# get url to download a file
def getDownloadUrl(filename, req):
    host = getServerUrl(True, req)
    curAdr = req.META['REMOTE_ADDR']
   #username = getUserFolder(req)
    #return f'{host}/dimar/download?fileName={filename}&userAddress={curAdr}/{username}'
    return f'{host}/download?fileName={filename}&userAddress={curAdr}'
    #print (f'{host}/download?fileName={filename}&userAddress={curAdr}/{username}' + '  getDownloadUrl docManager')
    #return f'{host}/download?fileName={filename}&userAddress={curAdr}/{username}'
    

#получение пользовательской директории


#def folderUserFull(req):
 #   username = getUserFolder(req)
 #   directory2 = os.path.join(config.STORAGE_PATH, username)
#    print (directory2)
   # return directory2

#def getUserFolder(req):
    #username = 'dimar'
#    print ('Start getUserFolder')
#    username = req.user.username
##    print (username + ' getUserFolder')
 #   return username


#def userfolder(req):
   
  #  if req.user.is_authenticated:
 #       username = req.user.username
  #  else:
  #     username=''
 #   print (username+' userfolder')
 #   return username

# get root folder for the current file
def getRootFolder(req):
    print ('start  getRootFolder')
    if isinstance(req, str):
        curAdr = req
        print (curAdr + ' curAdr1 getRootFolder')
    else:
        curAdr = req.META['REMOTE_ADDR']
        print (curAdr + ' curAdr2 getRootFolder')
    
   # username = req.user.username
    #username = 'dimar'
    #print (username + '  username getRootFolder')
    
   # directory = os.path.join(config.STORAGE_PATH, curAdr, username)
    #print(directory + '  directory getRootFolder')
    #directory = os.path.join(config.STORAGE_PATH, username)
    directory = os.path.join(config.STORAGE_PATH, curAdr)
    if not os.path.exists(directory): # if such a directory does not exist, make it
        os.makedirs(directory)
    print (directory+ '   getRootFolder')
    return directory

# get the file path
def getStoragePath(filename, req):
    print ('getStoragePath   Start')
    directory = getRootFolder(req)
    print (directory+ '  directory  getStoragePath')
    print (os.path.join(directory, fileUtils.getFileName(filename)))
    return os.path.join(directory, fileUtils.getFileName(filename))

# get the path to the forcesaved file version

def getForcesavePath(filename, req, create ):
    print ('Start getForcesavePat')
    
    if isinstance(req, str):
        curAdr = req
        print (curAdr+' curAdr 1 getForcesavePath')
    else:
        curAdr = req.META['REMOTE_ADDR']
        print (curAdr+' curAdr 2 getForcesavePath')
    #username = 'dimar'
    #if username==NULL:
     #   username=req.user.username

    #print (str(username)+'  username getForcesavePath')
    directory = os.path.join(config.STORAGE_PATH, curAdr)
    
    #directory = os.path.join(config.STORAGE_PATH, username)
    #print (directory+ '  diectory 1 getForcesavePath')
    if not os.path.exists(directory): # the directory with host address doesn't exist
        print ('  diectory 2 getForcesavePath')
        return ""
 
    directory = os.path.join(directory, f'{filename}-hist') # get the path to the history of the given file
    print (directory+'  diectory 3 getForcesavePath')
    if (not os.path.exists(directory)):
        if create: # if the history directory doesn't exist
            print ('  diectory 4 getForcesavePath')
            os.makedirs(directory) # create history directory if it doesn't exist
        else: # the history directory doesn't exist and we are not supposed to create it
            print ('  diectory 5 getForcesavePath')
            return ""
    print ('  start diectory 6 getForcesavePath')
    directory = os.path.join(directory, filename) # and get the path to the given file
    print (directory+ '  diectory 6 getForcesavePath')
    if (not os.path.exists(directory) and not create):
        print ('  diectory 7 getForcesavePath')
        return ""
    print (directory+ '  diectory 8 getForcesavePath')
    return directory

# get information about all the stored files
def getStoredFiles(req):
    directory = getRootFolder(req)

    files = os.listdir(directory)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True) # sort files by time of last modification

    fileInfos = []

    for f in files:
        if os.path.isfile(os.path.join(directory, f)):
            fileInfos.append({'isFillFormDoc': isCanFillForms(fileUtils.getFileExt(f)),'version':historyManager.getFileVersion(historyManager.getHistoryDir(getStoragePath(f, req))), 'type': fileUtils.getFileType(f), 'title': f, 'url': getFileUri(f, True, req), 'canEdit': isCanEdit(fileUtils.getFileExt(f))}) # write information about file type, title and url

    return fileInfos

# create a file
def createFile(stream, path, req = None, meta = False):
    bufSize = 8192
    with io.open(path, 'wb') as out: # write data to the file by streams
        read = stream.read(bufSize)
        while len(read) > 0:
            out.write(read)
            read = stream.read(bufSize)
    if meta:
        historyManager.createMeta(path, req) # create meta data for the file if needed
    return

# create file response
def createFileResponse(response, path, req, meta):
    response.raise_for_status()
    with open(path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    return

# save file from the given url 
def saveFileFromUri(uri, path, req = None, meta = False):
    resp = requests.get(uri, stream=True)
    createFileResponse(resp, path, req, meta)
    return

# create sample file
def createSample(fileType, sample, req):
    ext = getInternalExtension(fileType) # get the internal extension of the given file type

    if not sample:
        sample = 'false'

    sampleName = 'sample' if sample == 'true' else 'new' # create sample or new template 

    filename = getCorrectName(f'{sampleName}{ext}', req) # get file name with an index if such a file name already exists
    path = getStoragePath(filename, req)

    with io.open(os.path.join('assets', 'sample' if sample == 'true' else 'new', f'{sampleName}{ext}'), 'rb') as stream: # create sample file of the necessary extension in the directory
        createFile(stream, path, req, True)
    return filename

# remove file from the directory
def removeFile(filename, req):
    path = getStoragePath(filename, req)
    if os.path.exists(path):
        os.remove(path)
    histDir = historyManager.getHistoryDir(path) # get history directory
    if os.path.exists(histDir): # remove all the history information about this file
        shutil.rmtree(histDir)

# generate file key
def generateFileKey(filename, req):
    path = getStoragePath(filename, req)
    uri = getFileUri(filename, False, req)
    stat = os.stat(path) # get the directory parameters

    h = str(hash(f'{uri}_{stat.st_mtime_ns}')) # get the hash value of the file url and the date of its last modification and turn it into a string format
    replaced = re.sub(r'[^0-9-.a-zA-Z_=]', '_', h)
    return replaced[:20] # take the first 20 characters for the key

# generate the document key value
def generateRevisionId(expectedKey):
    if (len(expectedKey) > 20):
        expectedKey = str(hash(expectedKey))

    key = re.sub(r'[^0-9-.a-zA-Z_=]', '_', expectedKey)
    return key[:20]

# get files information
def getFilesInfo(req):
    fileId = req.GET.get('fileId') if req.GET.get('fileId') else None

    result = []
    resultID = []
    for f in getStoredFiles(req): # run through all the files from the directory
        stats = os.stat(os.path.join(getRootFolder(req), f.get("title"))) # get file information
        result.append( # write file parameters to the file object
            {   "version" : historyManager.getFileVersion(historyManager.getHistoryDir(getStoragePath(f.get("title"), req))),
                "id" :  generateFileKey(f.get("title"), req),   
                "contentLength" : "%.2f KB" % (stats.st_size/1024),
                "pureContentLength" : stats.st_size,
                "title" :  f.get("title"),
                "updated" : time.strftime("%Y-%m-%dT%X%z",time.gmtime(stats.st_mtime))
        })
        if fileId : # if file id is defined
            if fileId == generateFileKey(f.get("title"), req) : # and it is equal to the file key value
                resultID.append(result[-1]) # add file object to the response array
        

    if fileId :
        if len(resultID) > 0 : return resultID
        else : 
            print ('File not found')
            return "File not found"     
    else :
        return result
        
    

# download the file
def download(filePath):
    print (filePath +'    docManager dowloand start 1')
    response = FileResponse(open(filePath, 'rb'), True) # write headers to the response object
    print (' docManager dowloand start 2')
    response['Content-Length'] =  os.path.getsize(filePath)
    print (' docManager dowloand start 3')
    response['Content-Disposition'] = "attachment;filename*=UTF-8\'\'" + urllib.parse.unquote(os.path.basename(filePath))
    print (' docManager dowloand start 4')
    response['Content-Type'] = magic.from_file(filePath, mime=True)
    print (' docManager dowloand start 5')
    return response