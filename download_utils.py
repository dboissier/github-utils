#!/usr/bin/env python
# -*- coding: UTF8 -*-
import json, requests
import getpass
import pprint
import sys, os

def list(username, repo):
    response = requests.get("https://api.github.com/repos/%s/%s/downloads" % (username, repo))
    return response.json


def find_download(downloads, filename):
    for download in downloads:
        if download['name'] == filename:
            return download
    return None


def upload(username, repo, filepath):
    password = getpass.getpass("Enter host password for user '%s':" % username)

    downloads = list(username, repo)

    if not os.path.isfile(filepath):
        print "ERROR: file '%s' does not exist" % filepath
        return

    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filename)

    existing_download = find_download(downloads, filename)
    if existing_download is not None:
        requests.delete(existing_download['url'], auth=(username, password))


    path = "https://api.github.com/repos/%s/%s/downloads" % (username, repo)
    print "Step 1/2: Creating metadata for '%s' on the '%s'" % (filename, path)

    data = json.dumps({'name': filename, 'size': file_size})
    response = requests.post(path, data, auth=(username, password)).json

    print "Step 2/2: Uploading file '%s' to '%s'" % (filename, response['s3_url'])

    form_data = {'key': response['path'],
                 'acl': 'public-read',
                 'success_action_status': '201',
                 'Filename': response['name'],
                 'AWSAccessKeyId': response['accesskeyid'],
                 'Policy': response['policy'],
                 'Signature': response['signature'],
                 'Content-Type': response['content_type']
    }


    file_to_upload_data = {'file': open(filepath, 'rb')}

    response = requests.post(response['s3_url'], data=form_data, files=file_to_upload_data)

    if 201 == response.status_code:
        print "Done"


def delete(username, repo, filename):
    password = getpass.getpass("Enter host password for user '%s':" % username)

    downloads = list(username, repo)

    file_to_delete_metadata = None
    for download in downloads:
        if download['name'] == filename:
            file_to_delete_metadata = download

    if file_to_delete_metadata is None:
        print "'%s' not found on the repository" % filename
        return

    response = requests.delete(file_to_delete_metadata['url'], auth=(username, password))
    if 204 == response.status_code:
        print "File deleted"

def runListCommand():
    if len(sys.argv) == 4:
        pprint.pprint(list(sys.argv[2], sys.argv[3]), indent=2)
    else:
        print "Usage: python download_utils.py list <username> <repo>"

def runUploadCommand():
    if len(sys.argv) == 5:
        upload(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print "Usage: python download_utils.py upload <username> <repo> <filepath>"

def runDeleteCommand():
    if len(sys.argv) == 5:
        delete(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print "Usage: python download_utils.py delete <username> <repo> <filename>"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: python download_utils.py [list|upload|delete]"
    else:
        command = sys.argv[1]
        if "list" == command:
            runListCommand()
        elif "upload" == command:
            runUploadCommand()
        elif "delete" == command:
            runDeleteCommand()