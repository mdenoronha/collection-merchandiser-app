from flask import Flask, render_template, request, redirect, Response, session, copy_current_request_context, make_response, url_for
from flask_wtf.csrf import CSRFProtect
import urllib
import hmac
import hashlib
import random
import string
import base64
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from flask_mail import Mail, Message

import requests
import json
import os
import validators
import time
from datetime import timedelta

import threading

from flask_cors import CORS
from flask_pymongo import PyMongo

# Redis
from redis import Redis
from rq_scheduler import Scheduler

#GraphQL
import graphql


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET")
SECRET = os.environ.get("SHOPIFY_SECRET")

redis_pass = os.environ.get("REDIS_PASS")
redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")

# Flask Mail
app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER")
app.config['MAIL_PORT'] = os.environ.get("MAIL_PORT")
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE=None,
)

# MongoDB
CORS(app)
app.config["MONGO_URI"] = os.environ.get("MONGO_URL")
mongo = PyMongo(app)

csrf = CSRFProtect()
csrf.init_app(app)
mail = Mail(app)

nonce = ''

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

# https://stackoverflow.com/questions/49244170/shopify-hmac-parameter-verification-failing-in-python
def authenticate_hmac(request):

    # Rereieve qs 
    qs = str(request.url.split('?')[1])
    params = urllib.parse.parse_qsl(qs)
    cleaned_params = []
    hmac_value = dict(params)['hmac']

    # Sort parameters
    for (k, v) in sorted(params):
        if k in ['hmac', 'signature']:
            continue

        cleaned_params.append((k, v))

    new_qs = urllib.parse.urlencode(cleaned_params, safe=":/")
    secret = SECRET.encode("utf8")
    h = hmac.new(secret, msg=new_qs.encode("utf8"), digestmod=hashlib.sha256)

    # Compare digests
    return hmac.compare_digest(h.hexdigest(), hmac_value)

# Authenticate webhook
def verify_webhook(data, hmac_header):

    secret = SECRET.encode("utf8")
    data = data.decode("utf-8") 
    digest = hmac.new(secret, data.encode('utf-8'), hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)

    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))

# Extract next link from requests 
def extract_next_link(link):

    next_active = True
    if not 'rel="next"' in link:
        next_active = False
        link = ''
    else:
        if 'rel="previous"' in link:
            link = link.split(',')[1].split('<')[1].split('>')[0]
        else:
            link = link.split('<')[1].split('>')[0]
        
    return link, next_active

def getShop(request):

  shop = request.cookies.get("shop") if request.cookies.get("shop") != None else request.args.get("shop")

  return shop

# Get items from specified apiSource
def returnFromCollection(collection_id, apiSource):
    headers = {
        "X-Shopify-Access-Token": request.cookies.get("access_token"),
        "Content-Type": "application/json"
    }

    endpoint = "/admin/api/2019-07/" + apiSource +".json?collection_id=%s&limit=30" % collection_id
    response = requests.get("https://{0}{1}".format(getShop(request),
                                                    endpoint), headers=headers)

    response_status = response.status_code
    # Save the next link
    try:
        next_link = response.headers['link']
    except:
        next_link = ''

    if response.status_code == 200:
        return json.loads(response.text), next_link
    else: 
        return False


@app.route('/error', methods=['GET'])
def error():

    shop = request.args.get("shop")

    return render_template('error.html', shop=shop)

# Install route
@app.route('/install', methods=['GET'])
def install():

    # Create nonce
    global nonce
    nonce = randomword(12)

    shop = request.args.get("shop")

    if authenticate_hmac(request):
        return render_template('install.html', nonce=nonce, shop=shop)
    else:
        return 'Authentication failed. Please contact support at help@matthewdenoronha.com'

# Connect page
@app.route('/connect', methods=['GET'])
def connect():

    # get nonce
    nonce_value = request.args.get("state")

    # get hostname
    shop = request.args.get("shop")

    # Carry out oauth verification
    if authenticate_hmac(request) and nonce_value == nonce and validators.domain(shop) and shop.endswith('myshopify.com'):
        params = {
            "client_id": os.environ.get("SHOPIFY_KEY"),
            "client_secret": os.environ.get("SHOPIFY_SECRET"),
            "code": request.args.get("code")
        }
        resp = requests.post(
            "https://{0}/admin/oauth/access_token".format(
                request.args.get("shop")
                ),
            data=params
            )

        if 200 == resp.status_code:
            resp_json = json.loads(resp.text)

            index_response = make_response(redirect('home/{0}'.format(request.args.get("shop").replace('.myshopify.com', ''))))
            index_response.headers.add('Set-Cookie','shop={0}; SameSite=None; Secure'.format(request.args.get("shop")))
            index_response.headers.add('Set-Cookie','access_token={0}; SameSite=None; Secure'.format(resp_json.get("access_token")))

            return index_response
        else:
            print(resp.status_code, resp.text)
            return 'Cannot connect to app. Please contact support at help@matthewdenoronha.com. {}: {}'.format(e.message, e.description)
    else:
        return 'Authentication failed. Please contact support at help@matthewdenoronha.com'

# Contact page
@app.route('/contact', methods=['GET', 'POST'])
def contact():

    shop = request.args.get("shop")
    mail_sent = 'invalid'

    if request.method == "POST":
        name = request.form['nameFormInput']
        email = request.form['emailFormInput']
        message = request.form['messageFormInput']

        msg = Message("Collection merchadiser Email",
                          sender='collection.merchadiser@gmail.com',
                          recipients=["help@matthewdenoronha.com"])
        msg.body = "email:{0} name:{1} message:{2}".format(email, name, message)

        try:
            mail.send(msg)
        except Exception as e:
            print(e.message)
            mail_sent = 'unsuccessful'
        else:
            mail_sent = 'successful'

    return render_template('contact.html', shop=shop, mail_sent=mail_sent)

# Privacy Policy page
@app.route('/privacy-policy', methods=['GET'])
def privacy():

    shop = request.args.get("shop")

    return render_template('privacy_policy.html', shop=shop)

# Instructions page
@app.route('/instructions', methods=['GET'])
def instructions():

    shop = request.args.get("shop")

    return render_template('instructions.html', shop=shop)


# Deprecated
@csrf.exempt
@app.route('/products/create', methods=['POST'])
def product_create_sort():

    # verified = verify_webhook(data, request.headers.get('X-Shopify-Hmac-SHA256'))

    return Response(status=500)


# Homepage
@app.route('/home-2')
@app.route('/home-2/<shop>')
def index(shop=None):

  if not shop:
      shop = request.args.get("shop")
  else:
      shop = '{0}.myshopify.com'.format(shop)

  resp = make_response(render_template('index.html', shop=shop))

  return resp

# Homepage
@app.route('/home')
@app.route('/home/<shop>')
def index2(shop=None):

  if not shop:
      shop = request.args.get("shop")
  else:
    if 'myshopify.com' not in shop:
      shop = '{0}.myshopify.com'.format(shop)
  access_token = request.cookies.get("access_token")
  if access_token == None:
    return render_template("error_uninstall.html", shop=shop)

  error = False
  cursor = request.args.get('cursor')
  direction = request.args.get('direction')
  searchPar = request.args.get('search')
  search = '' if searchPar == None or searchPar == ''  else 'title:*' + searchPar + '*'
  collections = graphql.queryCollections(shop, access_token, search, cursor, direction)
  if collections == None:
    error = True
  else:
    if 'errors' in collections:
      error = True

  # stores = mongo.db.local_stores
  # rules = stores.find_one({'store.name': shop})
  rules = None

  resp = make_response(render_template('index_2.html', shop=shop, collections=collections, error=error, search=searchPar, rules=rules))

  return resp


# Update collection sort order
@csrf.exempt
@app.route('/update-sort', methods=['POST'])
def updateSort():

  response = request.get_json()
  store = getShop(request)
  collection = response['collection']
  sortOrder = response['sortMethod']
  access_token = request.cookies.get("access_token")

  result = graphql.updateCollection(store, access_token, collection, sortOrder)
  return json.dumps({'status': result}), 200, {'ContentType':'application/json'} 

# Collection page
@app.route('/collection-new/<collection_id>', methods=['GET', 'POST'])
def collectionNew(collection_id):

    # from queue_work import testQueue
    collection_data = productsQuery(getShop(request), request.cookies.get("access_token"), collection_id, None, 0, True)
    if collection_data == False:
      return render_template('collection.html', 
        failed='true',
        collection_data='null', 
        error=None,
        cursor=None,
        next_page=None,
        collection_id=None,
        shop=getShop(request)
    )
    js_collection_data = (json.dumps(collection_data['js_collection_data'])
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'))

    return render_template('collection.html', 
        failed='false',
        collection_data=js_collection_data, 
        error=collection_data['error'], 
        cursor=collection_data['cursor'], 
        next_page=collection_data['next_page'], 
        collection_id=collection_id, 
        shop=getShop(request)
    )

# Collection page
@app.route('/collection-adv/<collection_id>', methods=['GET', 'POST'])
def collectionAdv(collection_id):
    
  # from queue_work import testQueue
  collection_data = productsQuery(getShop(request), request.cookies.get("access_token"), collection_id, None, 0, False)
  if collection_data == False:
    return render_template('collection_adv.html', 
      failed='true',
      collection_data='null', 
      error=None,
      cursor=None,
      next_page=None,
      collection_id=None,
      shop=getShop(request)
    )
  js_collection_data = (json.dumps(collection_data['js_collection_data'])
  .replace(u'<', u'\\u003c')
  .replace(u'>', u'\\u003e')
  .replace(u'&', u'\\u0026')
  .replace(u"'", u'\\u0027'))

  return render_template('collection_adv.html', 
      failed='false',
      collection_data=js_collection_data, 
      error=collection_data['error'], 
      cursor=collection_data['cursor'], 
      next_page=collection_data['next_page'], 
      collection_id=collection_id, 
      shop=getShop(request)
  )

# Collection page ajax
@app.route('/collection-new-load', methods=['GET', 'POST'])
def collectionNewLoad():

    cursor = request.args.get('cursor', '')
    collection_id = request.args.get('collectionId', '')
    limited = request.args.get('limited', '')
    all_products = []
    
    for i in range(10):
        print(cursor)
        collection_data = productsQuery(getShop(request), request.cookies.get("access_token"), collection_id, cursor, 0, limited)
        if collection_data == False:
          return False
        all_products = all_products + collection_data['js_collection_data']['data']['collection']['products']['edges']
        if collection_data['next_page'] == False or collection_data['error'] != None: 
            break
        cursor = collection_data['cursor']

    collection_data['js_collection_data'] = (json.dumps(all_products)
        .replace(u'<', u'\\u003c')
        .replace(u'>', u'\\u003e')
        .replace(u'&', u'\\u0026')
        .replace(u"'", u'\\u0027'))

    return {'data': collection_data }

@csrf.exempt
@app.route('/product-remove', methods=['GET', 'POST'])
def productRemove():

    print('Remove print check')
    json_data = json.loads(request.data)
    collection_id = json_data.get('collectionId')
    product_id = json_data.get('productId')
    shop = getShop(request)
    access_token = request.cookies.get("access_token")

    remove_product = graphql.removeProducts(shop, access_token, collection_id, product_id)

    return {'data': remove_product}


@csrf.exempt
@app.route('/collection-new-save', methods=['GET', 'POST'])
def collectionNewSave():
    json_data = json.loads(request.data)

    changes = json_data.get('changes')
    collection_id = json_data.get('collectionId')
    shop = getShop(request)
    access_token = request.cookies.get("access_token")

    # TODO: Change to queue
    reorder_data = reorderQuery(shop, access_token, collection_id, changes)

    return {'data': reorder_data}

# Sort Functions

def reorderQuery(shop, access_token, collection_id, changes, rerun_count=0):

    error = ''
    reorder_status = graphql.reorderProducts(shop, access_token, collection_id, changes)
    
    if 'errors' in reorder_status:
        if len(reorder_status['errors']) > 0:
            error = reorder_status['errors'][0]['message']
            # Waits and reruns function if throttled 
            if error == 'Throttled' and rerun_count < 10:
                required_time = findWaitTime(reorder_status['extensions'])
                time.sleep(required_time)
                return reorderQuery(shop, access_token, collection_id, changes, rerun_count+1)

    return {
        'error': error
    }

def productsQuery(shop, access_token, collection_id, cursor=None, rerun_count=0, withVariants=False):

    error = ''
    next_page = False
    try:
      collection_data = graphql.queryProducts(shop, access_token, collection_id, cursor, withVariants)
    except Exception as e:
      print('401 Error Print')
      print(e)
      print(shop)
      return False

    js_collection_data = collection_data

    if 'errors' in collection_data:
        if len(collection_data['errors']) > 0:
            error = collection_data['errors'][0]['message']
            # Waits and reruns function if throttled 
            if error == 'Throttled' and rerun_count < 10:
                required_time = findWaitTime(collection_data['extensions'])
                time.sleep(required_time)
                return productsQuery(shop, access_token, collection_id, cursor, rerun_count+1, withVariants)

    try:
        last_product = collection_data['data']['collection']['products']['edges'][len(collection_data['data']['collection']['products']['edges']) - 1]
        cursor = last_product['cursor']
        next_page = collection_data['data']['collection']['products']['pageInfo']['hasNextPage']
    except:
        print('Error getting cursor')

    return {
        'js_collection_data': js_collection_data,
        'error': error,
        'cursor': cursor,
        'next_page': next_page
    }

def productsCollectionsQuery(shop, access_token, product_id, collections_skip_list, cursor=None, rerun_count=0):

  error = ''
  next_page = False
  collections = []
  product_data = graphql.queryCollectionsOfProducts(shop, access_token, product_id, cursor)

  if 'errors' in product_data:
      if len(product_data['errors']) > 0:
          error = product_data['errors'][0]['message']
          # Waits and reruns function if throttled 
          if error == 'Throttled' and rerun_count < 10:
              required_time = findWaitTime(product_data['extensions'])
              time.sleep(required_time)
              return productsCollectionsQuery(shop, access_token, product_id, collections_skip_list, cursor, rerun_count+1)

  # Get cursor and next page
  try:
      last_collection = product_data['data']['product']['collections']['edges'][len(product_data['data']['product']['collections']['edges']) - 1]
      cursor = last_collection['cursor']
      next_page = product_data['data']['product']['collections']['pageInfo']['hasNextPage']
  except:
    print('Error getting cursor')

  if not 'errors' in product_data:
    for collection in product_data['data']['product']['collections']['edges']:
      if collection['node']['sortOrder'] == 'MANUAL' and not collection['node']['id'] in collections_skip_list:
        collections.append({ 
            'id': collection['node']['id'],
            'moves': {
              'id': 'gid://shopify/Product/{0}'.format(product_id),
              # Change to zero for top
              'newPosition': str(collection['node']['productsCount'])
            }
          })

  return {
        'collections': collections,
        'error': error,
        'cursor': cursor,
        'next_page': next_page
    }

def findWaitTime(extensions):

    requested_cost = extensions['cost']['requestedQueryCost']
    currently_available = extensions['cost']['throttleStatus']['currentlyAvailable']
    restore_rate = extensions['cost']['throttleStatus']['restoreRate']

    required_time = -(currently_available - requested_cost) / restore_rate
    if 0 > required_time: 
        required_time = 0

    return True

# Auto sort
@app.route('/auto-smart', methods=['GET', 'POST'])
def autoSmart():

  shop = getShop(request)
  access_token = request.cookies.get("access_token")
  stores = mongo.db.local_stores
  rules = stores.find_one({'store.name': shop})
  if rules:
    oos = rules['store']['rules']['outOfStock'] if 'outOfStock' in rules['store']['rules'] else []
    inventory = rules['store']['rules']['customInventory'] if 'customInventory' in rules['store']['rules'] else []
    date = rules['store']['rules']['createdDate'] if 'createdDate' in rules['store']['rules'] else []

  return render_template('auto_smart.html', shop=shop, access_token=access_token, oos=oos if oos else [], inventory=inventory if inventory else [], date=date if date else [])

@csrf.exempt
@app.route('/post-auto-smart', methods=['POST'])
def postAutoSmart():

    response = request.get_json()
    # Set up Mongo
    
    stores = mongo.db.local_stores
       
    store = stores.find_one({'local_stores.name': response['shop']})
    if store != None:
      if response['access'] != store['store']['access_token']:
        return json.dumps({'status': 'Authentication Failed'}), 500, {'ContentType':'application/json'} 

    try:
      stores.find_one_and_update({'store.name': response['shop']}, {
          '$set': {'store.access_token': response['access'], 'store.rules': response['rules']},
      }, upsert=True)
      return json.dumps({'status': 'Automations Updated Successfully'}), 200, {'ContentType':'application/json'} 
    except (e):
      return json.dumps({'status': 'Something Went Wrong, Please Try Again'}), 500, {'ContentType':'application/json'} 

    return json.dumps({'status': 'Something Went Wrong, Please Try Again'}), 500, {'ContentType':'application/json'} 

# Auto sort functions
def autoBasicRules():

  # Get all products
  shop = 'learning-development-store.myshopify.com' 
  access_token = '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'
  products = [
    {
      'id': '4727648714788',
      'totalInvetory': 0
    },
    {
      'id': '1403965603876',
      'totalInvetory': 0
    },
    {
      'id': '1403965571108',
      'totalInvetory': 0
    }
  ]
  collections_skip_list = ['gid://shopify/Collection/52792852516']
  rules = [
    {
      'check': 'totalInvetory',
      'comparison': '<=',
      'value': 0,
      # actions: bottom, top, hide
      'action': 'bottom'
    }
  ]
  collections = {}
  # A check that runs change sort order if collections is getting to big
  runAndRefresh = False

  # Get all rules
  # Loop products
  for product in products:

    # Reset collections if movements needed are large
    if runAndRefresh:
      runAndRefresh = False
      # For collection that needs products moved
      for collection in collections:
        reorderQuery(shop, access_token, collection, json.dumps(collections[collection]), 0)
        # reorderStatus = reorderQuery(shop, access_token, collection, json.dumps(collections[collection]), 0)
        # if reorderStatus['error'] != None:
      collections = {}

    # Loop rules
    for rule in rules:
      # If breaks rule
      if checkRule(product, rule):
        # For collections of products
        for collection in autoBasicRuleWork(shop, access_token, product['id'], collections_skip_list, None):
          # Add to master collections list
          if not collection['id'] in collections:
            collections[collection['id']] = []
          collections[collection['id']].append(collection['moves'])
          # If products to move is over 240
          if len(collections[collection['id']]) > 200:
            runAndRefresh = True
        break

  for collection in collections:
    reorderQuery(shop, access_token, collection, json.dumps(collections[collection]), 0)

  return True

def autoBasicRuleWork(shop, access_token, product_id, collections_skip_list, cursor):

  collections = []
  products_data = productsCollectionsQuery(shop, access_token, product_id, collections_skip_list, cursor, 0)
  if products_data['error'] != None:
    collections = collections + products_data['collections']
    if products_data['next_page']:
      collections = collections + autoBasicRuleWork(shop, access_token, product_id, collections_skip_list, products_data['cursor'])

  return collections

def checkRule(product, rule):

  valueToCheck = product[rule['check']]
  ruleBreak = False
  try:
    ruleBreak = eval('{0}{1}{2}'.format(valueToCheck,rule['comparison'],rule['value']))
  except: 
    print('Eval failed')

  return ruleBreak


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), port=int(os.environ.get("PORT")), debug=False)

