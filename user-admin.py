#!/usr/bin/env python3
# Copyright 2020 Innovara Ltd
# -*- coding: utf-8 -*-
# Licensed under the GNU General Public License, version 3. This file may not be
# copied, modified, or distributed except according to those terms.

import argparse
import getpass
import requests
import json
import os

def open_config():
  '''Open config.json where settings are stored.'''
  try:
    with open('config.json', 'r') as json_file:
      config = json.load(json_file)
  # If config.json doesn't exist, create a template
  except FileNotFoundError:
    create_config()
    with open('config.json', 'r') as json_file:
      config = json.load(json_file)
  return config


def create_config():
  '''Create config.json.'''
  s = {}
  s['server_name'] = 'example.com'
  s['public_baseurl'] = 'https://matrix.example.com'
  s['admin'] = 'youradmin'
  s['password'] = 'yourpassword'
  s['database'] = '/path/to/your/homeserver.db'
  s['rp_hours'] = 12
  with open('config.json', 'w', encoding='utf-8') as config:
    json.dump(s, config, indent=4)
  os.chmod('config.json', 0o600)


def fq_user(user, server_name):
  '''Returns a fully qualified user id'''
  fq_user = '@' + user + ':' + server_name
  return fq_user


def get(headers, url):
  '''Gets url and prints json response'''
  request = requests.get(url, headers=headers)
  response = request.json()
  print(json.dumps(response, indent=4))


def post(headers, url, json):
  '''Posts to url and prints response'''
  request = requests.post(url, headers=headers, json=json)
  print(request)


def put(headers, url, json):
  '''Puts to url and prints response'''
  request = requests.put(url, headers=headers, json=json)
  print(request)


def log_in(user):
  '''Gets a Synapse login token'''
  url = str(public_baseurl) + '/_matrix/client/r0/login'
  try:
    passw = getpass.getpass(user + ' password: ')
  except KeyboardInterrupt:
    print('\r')
    exit()
  json = {'type':'m.login.password', 'user':  user, 'password':passw}
  request = requests.post(url, json=json)
  print('Log in: ' + str(request))
  response = request.json()
  token = response['access_token']
  return token


def log_out(headers):
  '''Logs out to invalidate the one-time access token'''
  url = str(public_baseurl) + '/_matrix/client/r0/logout'
  request = requests.post(url, headers=headers)
  print('Log out: ' + str(request))


def log_out_a(headers):
  '''Logs out admin user from all devices invalidating
  all access tokens including the current one-time'''
  url = str(public_baseurl) + '/_matrix/client/r0/logout/all'
  request = requests.post(url, headers=headers)
  print('Log out all: ' + str(request))
  exit()


def check_admin(headers, user):
  '''Checks if a Synapse user is an admin'''
  url = str(public_baseurl) + '/_synapse/admin/v1/users/'+ user +'/admin'
  get(headers, url)


def create_user(headers, user):
  '''Creates a Synapse user'''
  url = str(public_baseurl) + '/_synapse/admin/v2/users/' + user
  passw = getpass.getpass('Please enter password for ' + user + ': ')
  json = {'password': passw}
  put(headers, url, json)


def deactivate_user(headers, user):
  '''Deactivates a Synapse user'''
  url = str(public_baseurl) + '/_synapse/admin/v1/deactivate/' + user
  json = {'erase': True}
  post(headers, url, json)


def list_a_users(headers):
  '''Lists all Synapse users
  Limit is 100'''
  #TODO: Implement listing all/pager
  url = str(public_baseurl) + '/_synapse/admin/v2/users?deactivated=true&guests=true'
  get(headers, url)


def list_c_users(headers):
  '''Lists current Synapse users
  Limit is 100'''
  #TODO: Implement listing all/pager
  url = str(public_baseurl) + '/_synapse/admin/v2/users'
  get(headers, url)


def list_user(headers, user):
  '''Queries a Synapse user'''
  url = str(public_baseurl) + '/_synapse/admin/v2/users/' + user
  get(headers, url)


def make_admin(headers, user):
  '''Makes a Synapse user an admin'''
  url = str(public_baseurl) + '/_synapse/admin/v2/users/'+ user
  json = {'admin': True}
  put(headers, url, json)


def reset_pass(headers, user):
  '''Resets a Synapse user's password'''
  url = str(public_baseurl) + '/_synapse/admin/v2/users/' + user
  passw = getpass.getpass('Please enter new password for ' + user + ': ')
  json = {'password': passw, 'logout_devices': True}
  put(headers, url, json)


def reactivate_user(headers, user):
  '''Reactivates a Synapse user'''
  url = str(public_baseurl) + '/_synapse/admin/v2/users/' + user
  passw = getpass.getpass('Please enter new password for ' + user + ': ')
  json = {'password': passw, 'deactivated': False}
  put(headers, url, json)


def make_regular(headers, user):
  '''Makes an admin Synapse user a regular user'''
  url = str(public_baseurl) + '/_synapse/admin/v2/users/' + user
  json = {'admin': False}
  put(headers, url, json)


def main():
  '''Provides a command line interface to manage users
  in Synapse - Matrix.org's reference server
  making use of its administration APIs'''
  parser = argparse.ArgumentParser(description='User administration for Synapse.', epilog='Use only the localpart of the user i.e. exampleuser', add_help=False)
  required = parser.add_argument_group('Action arguments')
  exclusive = required.add_mutually_exclusive_group()
  exclusive.add_argument('-uc', metavar='user', help='create new user', type=str)
  exclusive.add_argument('-ud', metavar='user', help='deactivate user', type=str)
  exclusive.add_argument('-ur', metavar='user', help='reset user\'s password', type=str)
  exclusive.add_argument('-ux', metavar='user', help='undo user deactivation', type=str)
  exclusive.add_argument('-la', help='list all users', action='store_true')
  exclusive.add_argument('-lc', help='list current users', action='store_true')
  exclusive.add_argument('-lu', metavar='user', help='list user\'s properties', type=str)
  exclusive.add_argument('-am', metavar='user', help='make user administrator', type=str)
  exclusive.add_argument('-aq', metavar='user', help='query if user is admin', type=str)
  exclusive.add_argument('-at', help='invalidate all tokens of the admin user', action='store_true')
  exclusive.add_argument('-ax', metavar='user', help='make an admin user a regular user', type=str)
  optional = parser.add_argument_group('Optional arguments')
  optional.add_argument('-au', help='alternative Synapse admin user', type=str)
  optional.add_argument('-ad', help='alternative (sub)domain', type=str)
  optional.add_argument('-ap', help='alternative public_baseurl i.e. https://matrix.examle.com.', type=str)
  optional.add_argument('-h', '--help', help='show this help message and exit', action='help')
  args = parser.parse_args()
  
  # Read config.json
  config = open_config()
  global server_name
  server_name = config['server_name']
  global public_baseurl
  public_baseurl = config['public_baseurl']
  global admin
  admin = config['admin']

  # We need either a server_name in config.py or -ad server_name
  if server_name == '' or server_name == 'example.com' and args.ad == None:
    print('No server_name in config.json. Use -ad example.com.')
    exit()
  if args.ad != None:
    server_name = args.ad
  
  # We need either an admin user in config.py or -au user
  if admin == '' or admin == 'youradmin' and args.au == None:
    print('No admin user in config.json. Use -au user.')
    exit()
  if args.au != None:
    admin = args.au

  # We need either public_baseurl in config.py or -ap url
  if public_baseurl == '' or public_baseurl == 'https://matrix.example.com' and args.ap == None:
    print('No public_baseurl in config.json. Use -ap url.')
    exit()
  if args.ap != None:
    public_baseurl = args.ap

  # Logs in to get a token
  admin = '@' + admin + ':' + server_name
  token = log_in(admin)
  headers = {'Authorization': 'Bearer '+ token, 'Content-Type': 'application/json'}

  # TODO: How can we do this long conditional more efficient?
  # Creates user
  if args.uc:
    user = fq_user(args.uc, server_name)
    create_user(headers, user)
  # Deactivates user
  elif args.ud:
    user = fq_user(args.ud, server_name)
    deactivate_user(headers, user)
  # Resets user's password
  elif args.ur:
    user = fq_user(args.ur, server_name)
    reset_pass(headers, user)
  # Reactivates user
  elif args.ux:
    user = fq_user(args.ux, server_name)
    reactivate_user(headers, user)
  # Lists all users
  elif args.la:
    list_a_users(headers)
  # Lists current users
  elif args.lc:
    list_c_users(headers)
  # Lists a user
  elif args.lu:
    user = fq_user(args.lu, server_name)
    list_user(headers, user)
  # Makes user admin
  elif args.am:
    user = fq_user(args.am, server_name)
    make_admin(headers, user)
  # Admin query
  elif args.aq:
    user = fq_user(args.aq, server_name)
    check_admin(headers, user)
  # Invalidates all tokes of an admin
  elif args.at:
    log_out_a(headers)
  # Makes an admin user regular
  elif args.ax:
    user = fq_user(args.ax, server_name)
    make_regular(headers, user)
  else:
    log_out(headers)
    print('Nothing to do. Use a valid argument.')
    exit()
  log_out(headers)


if __name__ == '__main__':
  main()
