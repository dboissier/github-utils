#!/usr/bin/env python
# -*- coding: UTF8 -*-
import urllib2, json, requests
import getpass
import sys, os
import pprint

def filter_unecessary_metadata(download_data):
    result = []
    for download in download_data:
        filtered_download = dict((key, value) for key, value in download.iteritems() if (key in ['name', 'id', 'url']))
        result.append(filtered_download)
    return result


def list_all_downloads(username, repo):
    download_url = "https://api.github.com/repos/%s/%s/downloads" % (username, repo)
    response = urllib2.urlopen(download_url)
    response_read = response.read()
    return filter_unecessary_metadata(json.loads(response_read))


def find_download(downloads, filename):
    for download in downloads:
        if download['name'] == filename:
            return download
    return None


def upload(username, repo, filename):
    password = getpass.getpass("Enter host password for user '%s':" % username)

    downloads = list_all_downloads(username, repo)
    existing_download = find_download(downloads, filename)
    if existing_download is not None:
        print "File '%s' already exists on the '%s' repo. Need to remove it before uploading" % (filename, repo)
        delete_path = "https://api.github.com/repos/%s/%s/downloads/%s" % (username, repo, existing_download['id'])
        response = requests.delete(delete_path, auth=(username, password))
        pprint.pprint(response.status_code)

    file_size = os.path.getsize(filename)
    print "Size of the file '%s': %d bytes" % (filename, file_size)

    path = "https://api.github.com/repos/%s/%s/downloads" % (username, repo)
    print "Creating metadata for '%s' on the '%s'" % (filename, path)

    data = json.dumps({'name': filename, 'size': file_size})
    response = requests.post(path, data, auth=(username, password)).json

    print "Uploading file '%s' to '%s'" % (filename, path)

    form_data = {'key': response['path'],
                 'acl': 'public-read',
                 'success_action_status': '201',
                 'Filename': response['name'],
                 'AWSAccessKeyId': response['accesskeyid'],
                 'Policy': response['policy'],
                 'Signature': response['signature'],
                 'Content-Type': response['content_type']
                 }

    file_to_upload = {'file': open(filename, 'rb')}

    pprint.pprint(form_data)

    response = requests.post(response['s3_url'], data=form_data, files=file_to_upload)
    print response.text

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "Usage: upload_file.py <username> <repo> <filepath>"
    else:
        upload(sys.argv[1], sys.argv[2], sys.argv[3])