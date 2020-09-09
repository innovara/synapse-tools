#!/usr/bin/env python3
# Copyright 2020 Innovara Ltd
# -*- coding: utf-8 -*-
# Licensed under the GNU General Public License, version 3. This file may not be
# copied, modified, or distributed except according to those terms.

import requests
import json
import sqlite3
from datetime import datetime
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
  print('Edit config.json\r')
  exit()


def log_in(user, passw):
  '''Gets a login token'''
  url = str(public_baseurl) + '/_matrix/client/r0/login'
  json = {'type':'m.login.password', 'user':  user, 'password':passw}
  request = requests.post(url, json=json)
  print('Log in: ' + str(request))
  response = request.json()
  token = response['access_token']
  return token


def log_out(headers):
  '''Logs out to invalidate the log in access_token'''
  url = str(public_baseurl) + '/_matrix/client/r0/logout'
  request = requests.post(url, headers=headers)
  print('Log out: ' + str(request))


def get_rooms(headers, target):
  '''Gets all rooms'''
  url = str(public_baseurl) + '/_synapse/admin/v1/rooms'
  request = requests.get(url, headers=headers)
  rooms = request.json()
  for room in rooms['rooms']:
    target[room['room_id']] = {}
  return target


def get_tokens(target):
  '''Gets a member's token per room'''
  conn = sqlite3.connect(database)
  c = conn.cursor()
  for room_id in target.keys():
    sql = 'SELECT token \
          FROM access_tokens \
          INNER JOIN rooms \
          ON access_tokens.user_id = rooms.creator \
          WHERE rooms.room_id = \'' + room_id + '\';'
    r_token = c.execute(sql).fetchone()
    if r_token:
      if keys_exist(target, room_id, 'token') == False:
        target[room_id]['token'] = r_token[0]
  conn.close()
  return target


def get_events(target, until):
  '''Gets events older than n hours for each room'''
  conn = sqlite3.connect(database)
  c = conn.cursor()
  for room_id in target.keys():
    sql = 'SELECT event_id \
          FROM events \
          WHERE (type=\'m.room.encrypted\' OR type=\'m.room.message\') \
          AND room_id = \'' + room_id + '\' AND origin_server_ts < ' + str(until) + ';'
    event_ids = c.execute(sql).fetchall()
    for event_id in event_ids:
      if keys_exist(target, room_id, 'events') == True:
        target[room_id]['events'].append(event_id[0])
      else:
        target[room_id]['events'] = []
        target[room_id]['events'].append(event_id[0])
  conn.close()
  return target


def redact_rooms(target):
  '''Redacts events older than n hours for each room'''
  for room_id in target.keys():
    room_token = target[room_id]['token']
    if keys_exist(target, room_id, 'events') == True:
      for event_id in target[room_id]['events']:
        redact_event(room_id, room_token, event_id)


def redact_event(room_id, room_token, event_id):
  '''Redacts an event'''
  url = str(public_baseurl) + "/_matrix/client/api/v1/rooms/" + room_id + "/redact/" + event_id
  json = {"reason": "Timeout!"}
  headers = {'Authorization': 'Bearer ' + room_token}
  requests.post(url, json=json, headers=headers)


def purge_rooms(target, headers, until):
  '''Purges events older than n hours on the database'''
  url = str(public_baseurl) + '/_synapse/admin/v1/purge_history/'
  json = {'delete_local_events': True, 'purge_up_to_ts': until}
  for room_id in target.keys():
    room_url = url + room_id
    try:
      dummy = target[room_id]['events']
      print('Purging room :' + room_id)
      request = requests.post(room_url, headers=headers, json=json)
      response = request.json()
      print('Purge id: ' + response['purge_id'])
    except KeyError:
      continue


def list_rooms(headers, txt):
  '''List all rooms on a Synapse server'''
  url= str(public_baseurl) + '/_synapse/admin/v1/rooms'
  request = requests.get(url, headers=headers)
  response = request.json()
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


# FROM: https://stackoverflow.com/questions/43491287/elegant-way-to-check-if-a-nested-key-exists-in-a-dict
def keys_exist(element, *keys):
  '''Check if *keys (nested) exists in `element` (dict).'''
  if not isinstance(element, dict):
    raise AttributeError('keys_exists() expects dict as first argument.')
  if len(keys) == 0:
    raise AttributeError('keys_exists() expects at least two arguments, one given.')
  _element = element
  for key in keys:
    try:
      _element = _element[key]
    except KeyError:
      return False
  return True


def main():
  

  # Read config.json
  config = open_config()
  global server_name
  server_name = config['server_name']
  global public_baseurl
  public_baseurl = config['public_baseurl']
  
  admin = config['admin']
  # Fully qualified users take the form @user:server_name
  admin = '@' + admin + ':' + server_name
  passw = config['password']
  
  global database
  database = config['database']

  hours = config['rp_hours']
  until = int(datetime.now().timestamp() * 1000) - hours * 3600000

  token = log_in(admin, passw)
  headers = {'Authorization': 'Bearer '+ token, 'Content-Type': 'application/json'}
  target = {}
  ######### NOTE #########
  # target will be a nested dictionary with a list of events like this
  # {
  #   $room_id: 
  #             {
  #               'token': $token,
  #               'events': [$event_ids]
  #             }
  # }
  #######################
  # Gets rooms on the server
  target = get_rooms(headers, target)
  # Gets a member's token per room 
  target = get_tokens(target)
  # Gets events older than until, per room
  target = get_events(target, until)
  # We have everything we need to start cleaning up
  # It might be a good idea to test what the script would redact and purge before doing so
  # Uncomment 'with open' block and comment redact_rooms(target) as well as purge_rooms(target, headers, until)
  #with open('target.txt', 'w') as output:
  #  output.write('Hours: ' + str(hours) + '\n')
  #  output.write(json.dumps(target,indent=4))
  # Redact events older than 'until' per room , using a member's token
  redact_rooms(target)
  purge_rooms(target, headers, until)
  log_out(headers)
  # Delete and purge all rooms with "joined_members": 0
  delete_abandoned(headers)

if __name__ == '__main__':
    main()
