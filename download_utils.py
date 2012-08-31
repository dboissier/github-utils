#!/usr/bin/env python
# -*- coding: UTF8 -*-
import json, requests
import getpass
import pprint
import sys, os

def list_downloads(username, repo):
    return requests.get("https://api.github.com/repos/%s/%s/downloads" % (username, repo)).json


def find_download(downloads, filename):
    return next((download for download in downloads if download['name'] == filename), None)


def upload(username, repo, filepath):
    password = getpass.getpass("Enter host password for user '%s':" % username)

    downloads = list_downloads(username, repo)

    if not os.path.exists(filepath):
        print "ERROR: file '%s' does not exist" % filepath
        return

    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filename)

    download = find_download(downloads, filename)
    if download:
        requests.delete(download['url'], auth=(username, password))

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

    with open(filepath, 'rb') as f:
        upload_response = requests.post(response['s3_url'], data=form_data, files={'file': f})

        if 201 == upload_response.status_code:
            print "Done"


def delete(username, repo, filename):
    password = getpass.getpass("Enter host password for user '%s':" % username)

    download = find_download(list_downloads(username, repo), filename)
    if download:
        response = requests.delete(download['url'], auth=(username, password))
        if 204 == response.status_code:
            print "File deleted"
    else:
        print "'%s' not found on the repository" % filename


def run_list_command():
    if len(sys.argv) == 4:
        pprint.pprint(list_downloads(sys.argv[2], sys.argv[3]), indent=2)
    else:
        print "Usage: python download_utils.py list <username> <repo>"


def run_upload_command():
    if len(sys.argv) == 5:
        upload(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print "Usage: python download_utils.py upload <username> <repo> <filepath>"


def run_delete_command():
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
            run_list_command()
        elif "upload" == command:
            run_upload_command()
        elif "delete" == command:
            run_delete_command()
