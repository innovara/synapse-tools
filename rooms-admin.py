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


def get(headers, url):
  '''Get url and prints json response'''
  request = requests.get(url, headers=headers)
  response = request.json()
  return response


def log_in(user):
  '''Get a Synapse login token'''
  url = str(public_baseurl) + '/_matrix/client/r0/login'
  try:
    passw = getpass.getpass(user + ' password: ')
  except KeyboardInterrupt:
    print('\r')
    exit()
  json = {'type':'m.login.password', 'user':  user, 'password':passw}
  login = requests.post(url, json=json)
  response = login.json()
  token = response['access_token']
  return token


def log_out(headers):
  '''Log out to invalidate the one-time access token'''
  url = str(public_baseurl) + '/_matrix/client/r0/logout'
  logout = requests.post(url, headers=headers)
  print('Log out: ' + str(logout))


def list_rooms(headers, txt):
  '''List all rooms on a Synapse server'''
  url= str(public_baseurl) + '/_synapse/admin/v1/rooms'
  response = get(headers, url)
  if txt == True:
    with open(str(server_name) + '_rooms.txt', 'w', encoding='utf-8') as out_file:
      json.dump(response, out_file, indent=4)
  return response


def delete_room(headers, room_id):
  '''Delete room'''
  url = str(public_baseurl) + '/_synapse/admin/v1/rooms/' + room_id + '/delete'
  json = {'purge': True}
  request = requests.post(url, json=json, headers=headers)
  return request


def delete_abandoned(headers):
  '''Delete and purge rooms with "joined_members": 0'''
  data = list_rooms(headers, False)
  rooms = data['rooms']
  for room in rooms:
    room_id = room['room_id']
    joined_members = room['joined_members']
    if joined_members == 0:
      print('Purging room ' + room_id + ' with ' + str(joined_members) + ' joined_members')
      response = delete_room(headers, room_id)
      print(response)
  

def main():
  '''Provides a command line tool to manage rooms
  in Synapse - Matrix.org’s reference server
  making use of its administration APIs'''
  parser = argparse.ArgumentParser(description='Synapse server room admin.', add_help=False)
  required = parser.add_argument_group('Action arguments')
  exclusive = required.add_mutually_exclusive_group()
  exclusive.add_argument('-d', metavar='room_id', help='delete room', type=str)
  exclusive.add_argument('-l', help='list all rooms', action='store_true')
  exclusive.add_argument('-p', help='delete and purge rooms with "joined_members": 0', action='store_true')
  optional = parser.add_argument_group('Optional arguments')
  optional.add_argument('-au', help='alternative Synapse admin user.', type=str)
  optional.add_argument('-ad', help='alternative (sub)domain.', type=str)
  optional.add_argument('-ap', help='alternative public_baseurl i.e. https://matrix.examle.com.', type=str)
  optional.add_argument('-t', help='output all rooms list to txt file too', action='store_true')
  optional.add_argument('-h', '--help', help='show this help message and exit.', action='help')
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
  
  # Fully qualified users take the form @user:server_name
  admin = '@' + admin + ':' + server_name
  # Log in to obtain a valid admin token
  token = log_in(admin)
  # Token is added to the request headers
  headers = {'Authorization': 'Bearer '+ token, 'Content-Type': 'application/json'}
  # Deletes and purges room_id
  if args.d:
    response = delete_room(headers, args.d)
    print(response)
  # List all rooms
  elif args.l:
    response = list_rooms(headers, args.t)
    print(json.dumps(response, indent=4))
  elif args.p:
    delete_abandoned(headers)
    
  # Log out to invalidate the token 
  log_out(headers)


if __name__ == '__main__':
  main()
