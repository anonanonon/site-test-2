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
import re
import requests

import config
import json
import os
import urllib.parse
import magic

from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.shortcuts import render, redirect
from base.utils import docManager, fileUtils, serviceConverter, users, jwtManager, historyManager, trackManager
from django.contrib.auth.decorators import login_required

from base.models import UserFiles

#http://127.0.0.1:8000/download?fileName=new.docx
#http://127.0.0.1:8000/edit?filename=new.docx&type=desktop&mode=edit

# upload a file from the document storage service to the document editing service

#@login_required
def upload(request):
    response = {}

    try:
        fileInfo = request.FILES['uploadedFile']
        if ((fileInfo.size > config.FILE_SIZE_MAX) | (fileInfo.size <= 0)):  # check if the file size exceeds the maximum size allowed (5242880)
            raise Exception('File size is incorrect')

        curExt = fileUtils.getFileExt(fileInfo.name)
        if not docManager.isSupportedExt(curExt):  # check if the file extension is supported by the document manager
            raise Exception('File type is not supported')

        name = docManager.getCorrectName(fileInfo.name, request)  # get file name with an index if such a file name already exists
        path = docManager.getStoragePath(name, request)

        docManager.createFile(fileInfo.file, path, request, True)  # create file with meta information in the storage directory

        response.setdefault('filename', name)
        response.setdefault('documentType', fileUtils.getFileType(name))

    except Exception as e:  # if an error occurs
        response.setdefault('error', e.args[0])  # save an error message to the response variable

    return HttpResponse(json.dumps(response), content_type='application/json')  # return http response in json format

# convert a file from one format to another

#@login_required
def convert(request):
    response = {}

    try:
        body = json.loads(request.body)
        filename = fileUtils.getFileName(body.get("filename"))
        filePass = body.get("filePass")
        lang = request.COOKIES.get('ulang') if request.COOKIES.get('ulang') else 'en'
        fileUri = docManager.getDownloadUrl(filename,request)
        fileExt = fileUtils.getFileExt(filename)
        fileType = fileUtils.getFileType(filename)
        newExt = docManager.getInternalExtension(fileType)  # internal editor extensions: .docx, .xlsx or .pptx

        if docManager.isCanConvert(fileExt):  # check if the file extension is available for converting
            key = docManager.generateFileKey(filename, request)  # generate the file key

            newUri = serviceConverter.getConverterUri(fileUri, fileExt, newExt, key, True, filePass, lang)  # get the url of the converted file

            if not newUri:  # if the converter url is not received, the original file name is passed to the response
                response.setdefault('step', '0')
                response.setdefault('filename', filename)
            else:
                correctName = docManager.getCorrectName(fileUtils.getFileNameWithoutExt(filename) + newExt, request)  # otherwise, create a new name with the necessary extension
                path = docManager.getStoragePath(correctName, request)
                docManager.saveFileFromUri(newUri, path, request, True)  # save the file from the new url in the storage directory
                docManager.removeFile(filename, request)  # remove the original file
                response.setdefault('filename', correctName)  # pass the name of the converted file to the response
        else:
            response.setdefault('filename', filename)  # if the file can't be converted, the original file name is passed to the response

    except Exception as e:
        response.setdefault('error', e.args[0])

    return HttpResponse(json.dumps(response), content_type='application/json')

# create a new file

#@login_required
def createNew(request):
    response = {}

    try:
        fileType = request.GET['fileType']
        sample = request.GET.get('sample', False)

        filename = docManager.createSample(fileType, sample, request)  # create a new sample file of the necessary type        
        
        username = request.user
        ext = fileUtils.getFileExt(filename)
        if ext in config.EXT_FILLFORMS:
            fillformdoc = 'True'
        else:
            fillformdoc = 'False'
        b = UserFiles(namefile=str(filename), user=username, filetype=str(fileType), fillformdoc=fillformdoc)
        b.save()
        return HttpResponseRedirect(f'edit?filename={filename}')  # return http response with redirection url

    except Exception as e:
        response.setdefault('error', e.args[0])

    return HttpResponse(json.dumps(response), content_type='application/json')

# save file as...

#@login_required
def saveAs(request):
    response ={}

    try:
        body = json.loads(request.body)
        saveAsFileUrl = body.get('url')
        title = body.get('title')

        filename = docManager.getCorrectName(title, request)
        path = docManager.getStoragePath(filename, request)
        resp = requests.get(saveAsFileUrl)

        if ((len(resp.content) > config.FILE_SIZE_MAX) | (len(resp.content) <= 0)):  # check if the file size exceeds the maximum size allowed (5242880)
            response.setdefault('error', 'File size is incorrect')
            raise Exception('File size is incorrect')

        curExt = fileUtils.getFileExt(filename)
        if not docManager.isSupportedExt(curExt):  # check if the file extension is supported by the document manager
            response.setdefault('error', 'File type is not supported')
            raise Exception('File type is not supported')

        docManager.saveFileFromUri(saveAsFileUrl, path, request, True)  # save the file from the new url in the storage directory

        response.setdefault('file', filename)
    except Exception as e:
        response.setdefault('error', 1)
        response.setdefault('message', e.args[0])

    return HttpResponse(json.dumps(response), content_type='application/json')

# edit a file
#@login_required
def edit(request):
    print('  start edit actions')
    filename = fileUtils.getFileName(request.GET['filename'])
    print(filename+'  filename edit')
    ext = fileUtils.getFileExt(filename)

    fileUri = docManager.getFileUri(filename, True, request)
    print(fileUri+'   fileUri')
    fileUriUser = docManager.getFileUri(filename, False, request)
    docKey = docManager.generateFileKey(filename, request)
    fileType = fileUtils.getFileType(filename)
    user = users.getUserFromReq(request)  # get user
    print (str(user) + ' user get edit action')
    edMode = request.GET.get('mode') if request.GET.get('mode') else 'edit'  # get the editor mode: view/edit/review/comment/fillForms/embedded (the default mode is edit)
    canEdit = docManager.isCanEdit(ext)  # check if the file with this extension can be edited

    if (((not canEdit) and edMode == 'edit') or edMode == 'fillForms') and docManager.isCanFillForms(ext) :
        edMode = 'fillForms'
        canEdit = True
    submitForm = edMode == 'fillForms' and user.id == 'uid-1' and False  # if the Submit form button is displayed or hidden
    mode = 'edit' if canEdit & (edMode != 'view') else 'view'  # if the file can't be edited, the mode is view

    edType = request.GET.get('type') if request.GET.get('type') else 'desktop'  # get the editor type: embedded/mobile/desktop (the default type is desktop)
    lang = request.COOKIES.get('ulang') if request.COOKIES.get('ulang') else 'en'  # get the editor language (the default language is English)

    storagePath = docManager.getStoragePath(filename, request)
    print(storagePath+' storagePath edit action')
    meta = historyManager.getMeta(storagePath)  # get the document meta data
    infObj = None

    actionData = request.GET.get('actionLink')  # get the action data that will be scrolled to (comment or bookmark)
    actionLink = json.loads(actionData) if actionData else None

    templatesImageUrl = docManager.getTemplateImageUrl(fileType, request) # templates image url in the "From Template" section
    createUrl = docManager.getCreateUrl(edType, request)
    print(createUrl+'  createUrl edit action')
    templates = [
        {
            'image': '',
            'title': 'Blank',
            'url': createUrl
        },
        {
            'image': templatesImageUrl,
            'title': 'With sample content',
            'url': createUrl + '&sample=true'
        }
    ]

    if (meta):  # if the document meta data exists,
        infObj = {  # write author and creation time parameters to the information object
            'owner': meta['uname'],
            'uploaded': meta['created']
        }
    else:  # otherwise, write current meta information to this object
        infObj = {
            'owner': 'Me',
            'uploaded': datetime.today().strftime('%d.%m.%Y %H:%M:%S')
        }
    infObj['favorite'] = user.favorite
    # specify the document config
    edConfig = {
        'type': edType,
        'documentType': fileType,
        'document': {
            'title': filename,
            'url': docManager.getDownloadUrl(filename, request),
            'fileType': ext[1:],
            'key': docKey,
            'info': infObj,
            'permissions': {  # the permission for the document to be edited and downloaded or not
                'comment': (edMode != 'view') & (edMode != 'fillForms') & (edMode != 'embedded') & (edMode != "blockcontent"),
                'copy': 'copy' not in user.deniedPermissions,
                'download': 'download' not in user.deniedPermissions,
                'edit': canEdit & ((edMode == 'edit') | (edMode == 'view') | (edMode == 'filter') | (edMode == "blockcontent")),
                'print': 'print' not in user.deniedPermissions,
                'fillForms': (edMode != 'view') & (edMode != 'comment') & (edMode != 'embedded') & (edMode != "blockcontent"),
                'modifyFilter': edMode != 'filter',
                'modifyContentControl': edMode != "blockcontent",
                'review': canEdit & ((edMode == 'edit') | (edMode == 'review')),
                'reviewGroups': user.reviewGroups,
                'commentGroups': user.commentGroups
            }
        },
        'editorConfig': {
            'actionLink': actionLink,
            'mode': mode,
            'lang': lang,
            'callbackUrl': docManager.getCallbackUrl(filename, request),  # absolute URL to the document storage service
            'createUrl' : createUrl if user.id !='uid-0' else None,
            'templates' : templates if user.templates else None,
            'user': {  # the user currently viewing or editing the document
                'id': user.id,
                #'name': user.name,
                'name': request.user.username,
                #'group': user.group
            },
            'embedded': {  # the parameters for the embedded document type
                'saveUrl': fileUriUser,  # the absolute URL that will allow the document to be saved onto the user personal computer
                'embedUrl': fileUriUser,  # the absolute URL to the document serving as a source file for the document embedded into the web page
                'shareUrl': fileUriUser,  # the absolute URL that will allow other users to share this document
                'toolbarDocked': 'top'  # the place for the embedded viewer toolbar (top or bottom)
            },
            'customization': {  # the parameters for the editor interface
                'about': True,  # the About section display
                'feedback': True,  # the Feedback & Support menu button display
                'forcesave': False,  # adds the request for the forced file saving to the callback handler
                'submitForm': submitForm,  # if the Submit form button is displayed or not
                'goback': {  # settings for the Open file location menu button and upper right corner button 
                    'url': docManager.getServerUrl(False, request)  # the absolute URL to the website address which will be opened when clicking the Open file location menu button
                }
            }
        }
    }

    # an image which will be inserted into the document
    dataInsertImage = {
        'fileType': 'png',
        'url': docManager.getServerUrl(True, request) + '/static/images/logo.png'
    }

    # a document which will be compared with the current document
    dataCompareFile = {
        'fileType': 'docx',
        'url': docManager.getServerUrl(True, request) + '/static/sample.docx'
    }

    # recipient data for mail merging
    dataMailMergeRecipients = {
        'fileType': 'csv',
        'url': docManager.getServerUrl(True, request) + '/csv'
    }

    # users data for mentions
    usersForMentions = users.getUsersForMentions(user.id) 

    if jwtManager.isEnabled():  # if the secret key to generate token exists
        edConfig['token'] = jwtManager.encode(edConfig)  # encode the edConfig object into a token
        dataInsertImage['token'] = jwtManager.encode(dataInsertImage)  # encode the dataInsertImage object into a token
        dataCompareFile['token'] = jwtManager.encode(dataCompareFile)  # encode the dataCompareFile object into a token
        dataMailMergeRecipients['token'] = jwtManager.encode(dataMailMergeRecipients)  # encode the dataMailMergeRecipients object into a token


    hist = historyManager.getHistoryObject(storagePath, filename, docKey, fileUri, request)  # get the document history
    #print(str(hist)+ '  hist edit action')
    context = {  # the data that will be passed to the template
        'cfg': json.dumps(edConfig),  # the document config in json format
        'history': json.dumps(hist['history']) if 'history' in hist else None,  # the information about the current version
        'historyData': json.dumps(hist['historyData']) if 'historyData' in hist else None,  # the information about the previous document versions if they exist
        'fileType': fileType,  # the file type of the document (text, spreadsheet or presentation)
        'apiUrl': config.DOC_SERV_SITE_URL + config.DOC_SERV_API_URL,  # the absolute URL to the api
        'dataInsertImage': json.dumps(dataInsertImage)[1 : len(json.dumps(dataInsertImage)) - 1],  # the image which will be inserted into the document
        'dataCompareFile': dataCompareFile,  # document which will be compared with the current document
        'dataMailMergeRecipients': json.dumps(dataMailMergeRecipients),  # recipient data for mail merging
        'usersForMentions': json.dumps(usersForMentions) if user.id !='uid-0' else None
    }
    print('   end edit')
    print(str(request)+ str(context)+'  render')
    return render(request, 'editor.html', context)  # execute the "editor.html" template with context data

# track the document changes

##@login_required
def track(request):
    print ('  start Track')
    response = {}

    try:
        print ( ' start trackManager actions')
        body = trackManager.readBody(request)  # read request body
        print ( ' end trackManager actions')
        status = body['status']  # and get status from it
        print (str(status)+'  status body track')
        if (status == 1): # editing
            if (body['actions'] and body['actions'][0]['type'] == 0):  # finished edit
                user = body['actions'][0]['userid']  # the user who finished editing
                if (not user in body['users']):
                    trackManager.commandRequest('forcesave', body['key'])  # create a command request with the forcasave method

        filename = fileUtils.getFileName(request.GET['filename'])
        #usAddr = '192.168.1.5'
        #usAddr = request.META['REMOTE_ADDR']
        print (filename+'   filename trackManager actions')
        usAddr = request.GET['userAddress']
        print (usAddr+'  track action')

        if (status == 2) | (status == 3):  # mustsave, corrupted
            print ( '  Status 2 3')
            trackManager.processSave(body, filename, usAddr)
        if (status == 6) | (status == 7):  # mustforcesave, corruptedforcesave
            print ('  Status 6 7')
            trackManager.processForceSave(body, filename, usAddr)
        print ('  try track comleate action')

    except Exception as e:
        print('   Exception')
        response.setdefault('error', 1)  # set the default error value as 1 (document key is missing or no document with such key could be found)
        response.setdefault('message', e.args[0])

    response.setdefault('error', 0)  # if no exceptions are raised, the default error value is 0 (no errors)
    # the response status is 200 if the changes are saved successfully; otherwise, it is equal to 500
    
    #print (' End track')
    print (str(response)+ ' End track')
    return HttpResponse(json.dumps(response), content_type='application/json', status=200 if response['error'] == 0 else 500)

# remove a file

#@login_required
def remove(request):
    filename = fileUtils.getFileName(request.GET['filename'])

    response = {}

    docManager.removeFile(filename, request)

    response.setdefault('success', True)

    b = UserFiles.objects.get(namefile=str(filename))
    b.delete()
    return HttpResponse(json.dumps(response), content_type='application/json')

# get file information

##@login_required
def files(request):
    try:
        response = docManager.getFilesInfo(request)
    except Exception as e:
        response = {}
        response.setdefault('error', e.args[0])
    return HttpResponse(json.dumps(response), content_type='application/json')
    
# download a csv file

#@login_required
def csv(request):
    filePath = os.path.join('assets', 'sample', "csv.csv")
    response = docManager.download(filePath)
    return response
    
#@login_required
# download a file
def download(request):
    print (' Start download')
    
    try:   
        fileName = fileUtils.getFileName(request.GET['fileName'])  # get the file name
        print(fileName+'  actions download 1')
        #userAddress = '192.168.1.5'
        userAddress = request.GET.get('userAddress') if request.GET.get('userAddress') else request
        print(str(userAddress)+'  actions download 2')
        
        if (jwtManager.isEnabled()):
            jwtHeader = 'Authorization' if config.DOC_SERV_JWT_HEADER is None or config.DOC_SERV_JWT_HEADER == '' else config.DOC_SERV_JWT_HEADER
            token = request.headers.get(jwtHeader)
            if token:
                token = token[len('Bearer '):]
                try:
                    body = jwtManager.decode(token)   
                except Exception:    
                    return HttpResponse('JWT validation failed', status=403)
        #username=request.user.username
        #print(username+' username dowloand action')
        
        filePath = docManager.getForcesavePath(fileName, userAddress, False) # get the path to the forcesaved file version
        print (filePath+'  filePath 1')  
        if (filePath == ""):
            print (' start filePath 2')
            filePath = docManager.getStoragePath(fileName, userAddress)  # get file from the storage directory
            print (filePath+'  filePath 2')
        print (' start response filePath 3')
        
        response = docManager.download(filePath)  # download this file
        print (' filePath 3')
        
        return response
    except Exception:
        response = {}
        print ('error', 'File not found')
        response.setdefault('error', 'File not found')
        return HttpResponse(json.dumps(response), content_type='application/json')

