from flask import Flask, render_template, request, redirect, Response, session, copy_current_request_context, make_response
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

# Check is smart or custom and has manual sort order
def checkCollection(collection_id, shop, headers):

    # Check is smart or custom
    endpoint = '/admin/api/2019-07/smart_collections/{0}.json'.format(collection_id)
    smart_collections = requests.get("https://{0}{1}".format(shop,
                                                    endpoint), headers=headers)
    if smart_collections.status_code != 200:
        endpoint = '/admin/api/2019-07/custom_collections/{0}.json'.format(collection_id)
        custom_collections = requests.get("https://{0}{1}".format(shop,
                                                    endpoint), headers=headers)
        if custom_collections.status_code != 200:
            return 'Error: Failed collection retrieval'
        else:
            custom_collection = True
            manual_sort_order = False
            collection = json.loads(custom_collections.text)
            if collection['custom_collection']['sort_order'] == 'manual':
                manual_sort_order = True
    else:
        custom_collection = False
        manual_sort_order = False
        collection = json.loads(smart_collections.text)
        if collection['smart_collection']['sort_order'] == 'manual':
            manual_sort_order = True

    return {
       'custom_collection': custom_collection,
       'manual_sort_order': manual_sort_order
    }

def loopProducts(all_products, next_endpoint, collection, shop, access_token, product_to_skip, collection_type, limit=0):
    # Add limitation for first 5 pages
    if limit == 4:
        return all_products

    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    if not next_endpoint:
        endpoint = '/admin/api/2019-10/collects.json?collection_id=%s' % collection
    else:
        endpoint = next_endpoint

    collects_response = requests.get("https://{0}{1}".format(shop, endpoint), headers=headers)
    collects = json.loads(collects_response.text)

    if not collects_response.ok:
        return all_products
    try:
        response = collects_response.headers
        response['link']
    except:
        for collect in collects['collects']:
            if collect['product_id'] != product_to_skip:
                if collection_type == 'custom':
                    position = len(all_products['custom_collection']['collects']) + 2
                    all_products['custom_collection']['collects'].append({
                            'id': collect['id'],
                            'position': position
                        })
                else:
                    all_products = all_products + 'products[]=%s&' % collect['product_id']

        return all_products
    else:
        for collect in collects['collects']:
            if collection_type == 'custom':
                position = len(all_products['custom_collection']['collects']) + 2
                all_products['custom_collection']['collects'].append({
                            'id': collect['id'],
                            'position': position
                        })
            else:
                all_products = all_products + 'products[]=%s&' % collect['product_id']

        pagination = requests.utils.parse_header_links(response['link'].rstrip('>').replace('>,<', ',<'))

        # Are there more pages?
        next_true = False
        for url in pagination:
            if url['rel'] == 'next':
                next_true = True
                break

        if next_true:
            next_page = url['url'].replace('https://%s' % shop, '')
            limit += 1
            call_limit = response['X-Shopify-Shop-Api-Call-Limit'].split('/')
            if int(call_limit[0]) > 35:
                time.sleep(34)

            return loopProducts(all_products, next_page, collection, shop, access_token, product_to_skip, collection_type, limit)
        else:
            return all_products

# Get products and collects through AJAX
@app.route('/ajax-collects', methods=['GET', 'POST'])
def ajax_collects():

    next_link = request.args.get('next_link', '')
    
    headers = {
        "X-Shopify-Access-Token": request.cookies.get("access_token"),
        "Content-Type": "application/json"
    }

    response = requests.get(next_link, headers=headers)
    next_link = response.headers['link']
    collects = json.loads(response.text)

    collect_ids = ''
    for collect in collects['collects']:
        collect_ids = collect_ids + str(collect['product_id']) + ','

    # Retrieve products
    endpoint = "/admin/api/2019-07/products.json?ids=%s" % collect_ids
    products_response = requests.get("https://{0}{1}".format(request.cookies.get("shop"),
                                                    endpoint), headers=headers)
    products = json.loads(products_response.text)

    # Create dict of product information to create cards on collection page
    collect_products = {}
    for counter, collect in enumerate(collects['collects']):
        for product in products['products']:
            if product['id'] == collect['product_id']:
                total_variants = 0
                avail_variants = 0
                no_inventory_management = False
                min_price = False
                varied_price = False
                for variant in product['variants']:
                    # Set price
                    if not min_price:
                        min_price = float(variant['price'])
                    else:
                        if float(variant['price']) > float(min_price):
                            min_price = variant['price']
                            varied_price = True
                    if not variant['inventory_management']:
                        no_inventory_management = True
                    else:
                        if variant['inventory_quantity'] > 0:
                            avail_variants = avail_variants + 1
                        total_variants = total_variants + variant['inventory_quantity']

                availability = 'Available' if product['published_at'] else 'Unavailable'
                try:
                    product_image = product['images'][0]
                except:
                    product_image = ''
                temp_product_collect = {
                    'product_id': product['id'],
                    'collect_id': collect['id'],
                    'position': collect['position'],
                    'product_title': product['title'],
                    'product_image': product_image,
                    'product_available': availability,
                    'product_price': min_price,
                    'product_varied_price': varied_price,
                    'no_inventory_management': no_inventory_management,
                    'total_variants': total_variants,
                    'avail_variants': avail_variants / len(product['variants'])
                }

                collect_products[counter] = temp_product_collect

    next_link, next_active = extract_next_link(next_link)

    return {
        'next_link': next_link,
        'collect_products': collect_products,
        'next_active': next_active
    }   

# Get items from specified apiSource
def returnFromCollection(collection_id, apiSource):
    headers = {
        "X-Shopify-Access-Token": request.cookies.get("access_token"),
        "Content-Type": "application/json"
    }

    endpoint = "/admin/api/2019-07/" + apiSource +".json?collection_id=%s&limit=30" % collection_id
    response = requests.get("https://{0}{1}".format(request.cookies.get("shop"),
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

# Display products from collection for sort
@csrf.exempt
@app.route('/collection/<collection_id>', methods=['GET', 'POST'])
def collection(collection_id):

    response_status = 'unchanged'

    headers = {
                "X-Shopify-Access-Token": request.cookies.get("access_token"),
                "Content-Type": "application/json"
            }

    # Check is smart or custom
    endpoint = '/admin/api/2019-07/smart_collections/{0}.json'.format(collection_id)
    smart_collections = requests.get("https://{0}{1}".format(request.cookies.get("shop"),
                                                    endpoint), headers=headers)
    if smart_collections.status_code != 200:
        endpoint = '/admin/api/2019-07/custom_collections/{0}.json'.format(collection_id)
        custom_collections = requests.get("https://{0}{1}".format(request.cookies.get("shop"),
                                                    endpoint), headers=headers)
        if custom_collections.status_code != 200:
            return render_template('error.html')
        else:
            custom_collection = True
            manual_sort_order = False
            collection = json.loads(custom_collections.text)
            if collection['custom_collection']['sort_order'] == 'manual':
                manual_sort_order = True
    else:
        custom_collection = False
        manual_sort_order = False
        collection = json.loads(smart_collections.text)
        if collection['smart_collection']['sort_order'] == 'manual':
            manual_sort_order = True

    # On POST of sorted products
    if request.method == "POST":

        # Sort for custom collection
        if custom_collection:
            positionsArray = []
            positions = request.form["products-switch"].split(';')
            for position in positions:
                positionAndId = position.split(',')
                positionsArray.append({"id": int(positionAndId[0]), "position": int(positionAndId[1])})

            payload = {  'custom_collection':
                {"id": collection_id,   
                "collects": positionsArray
                }
            }

            response = requests.put("https://" + request.cookies.get("shop")
                                     + "/admin/api/2019-07/custom_collections/" + collection_id + ".json",
                                     data=json.dumps(payload), headers=headers)
        # Sort for smart collection
        else:
            response = requests.put("https://" + request.cookies.get("shop") + '/admin/api/2019-07/smart_collections/' + collection_id + '/order.json?' + request.form["products-switch"]
                , headers=headers)


        response_status = response.status_code

    # Retrieve collects from collection
    collects, next_link = returnFromCollection(collection_id, 'collects')
    next_link, next_active = extract_next_link(next_link)

    collect_ids = ''
    for collect in collects['collects']:
        collect_ids = collect_ids + str(collect['product_id']) + ','

    # Retrieve products from collects
    endpoint = "/admin/api/2019-07/products.json?ids=%s" % collect_ids
    products_response = requests.get("https://{0}{1}".format(request.cookies.get("shop"),
                                                    endpoint), headers=headers)
    products = json.loads(products_response.text)

    shop_endpoint = "/admin/api/2019-07/shop.json" 
    shop_response = requests.get("https://{0}{1}".format(request.cookies.get("shop"),
                                                    shop_endpoint), headers=headers)
    shop_json = json.loads(shop_response.text)
    shop_html = BeautifulSoup(shop_json['shop']['money_with_currency_format'])
    shop_currency = shop_html.text

    shop = request.args.get("shop")

    if collects and products:
        return render_template('collection.html', collects=collects, products=products.get("products"), response_status=response_status, custom_collection=custom_collection, manual_sort_order=manual_sort_order, next_link=next_link, next_active=next_active, shop=shop, shop_currency=shop_currency)
    else:
        return redirect('/error')

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

# Automations
@app.route('/automations', methods=['GET', 'POST'])
def automations():
    headers = {
        "X-Shopify-Access-Token": request.cookies.get("access_token"),
        "Content-Type": "application/json"
    }

    # Set up Mongo
    shop = request.cookies.get("shop")
    stores = mongo.db.stores
    mail_sent = 'invalid'


    response = requests.get('https://%s/admin/api/2019-07/webhooks.json' % request.cookies.get("shop"), 
        headers=headers)

    webhooks = json.loads(response.text)['webhooks']
    webhookIds = [webhook['id'] for webhook in webhooks if webhook['topic'] == "products/create"]

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

    return render_template('automations.html', shop=shop, webhookIds=webhookIds, access_token=request.cookies.get("access_token"), mail_sent=mail_sent)
    
@csrf.exempt
@app.route('/update_webhook', methods=['POST'])
def updateWebhook():

    reponse = json.loads(request.data)
    headers = {
        "X-Shopify-Access-Token": reponse["access_token"],
        "Content-Type": "application/json"
    }

    payload = {
        "webhook": {
        "topic": reponse["webhook"],
        "address": '{0}/{1}'.format(os.environ.get("HOST"), reponse["webhook"]),
        "format": "json"
        }
    }

    if reponse['action'] == 'create':
        
        webhookResponse = requests.post('https://%s/admin/api/2019-07/webhooks.json' % reponse["shop"],
            data=json.dumps(payload), headers=headers)

    elif reponse['action'] == 'delete':
        webhookIdCheckReponse = requests.get('https://%s/admin/api/2019-07/webhooks.json' % reponse["shop"], 
            headers=headers)

        webhookIdChecks = json.loads(webhookIdCheckReponse.text)['webhooks']
        webhookIdList = [webhook['id'] for webhook in webhookIdChecks if webhook['topic'] == reponse["webhook"]]

        try:
            webhookResponse = requests.delete('https://{0}/admin/api/2019-07/webhooks/{1}.json'.format(reponse["shop"], webhookIdList[0]),
                data=json.dumps(payload), headers=headers)
        except:
            return Response(status=200)

    response = requests.get('https://%s/admin/api/2019-07/webhooks.json' % reponse["shop"], 
        headers=headers)

    return Response(status=200)

@csrf.exempt
@app.route('/products/create', methods=['POST'])
def product_create_sort():

    data = request.get_data()

    verified = verify_webhook(data, request.headers.get('X-Shopify-Hmac-SHA256'))

    if not verified:
        print('abort')
        abort(401)

    stores = mongo.db.stores
    shop = request.headers.get('X-Shopify-Shop-Domain')
    product_id = json.loads(request.data)['id']
    access_token_response = stores.find_one({'store.name': request.headers.get('X-Shopify-Shop-Domain')}, {'store.access_token': 1})
    access_token = access_token_response['store']['access_token']
    collections = stores.find_one({'store.name': shop})
    collectionIds = collections['store']['new_products_automation']

    queue_data = {
        'collectionId': collectionIds,
        'shop': shop,
        'product_id': product_id,
        'access_token': access_token
    }

    from queue_work import sort_collection

    scheduler = Scheduler(connection=Redis(host=redis_host, port=redis_port, db=0, password=redis_pass))
    scheduler.enqueue_in(timedelta(minutes=5), sort_collection, queue_data)

    return Response(status=200)

@csrf.exempt
@app.route('/collections/update', methods=['POST'])
def collection_update_sort():

    data = request.get_data()
    verified = verify_webhook(data, request.headers.get('X-Shopify-Hmac-SHA256'))

    if not verified:
        print('abort')
        abort(401)

    collection_id = json.loads(request.data)['id']

    return Response(status=200)

    
@csrf.exempt
@app.route('/automations_delete', methods=['POST'])
def automationsDelete():

    # Set up Mongo
    stores = mongo.db.stores

    response = json.loads(request.data)
    stores.update(
        {'store.name': response['shop']},
        {'$pull': {'store.%s' % response['automation']: {'handle': str(response['collectionHandle'])}}}
    )

    # update
    return Response(status=200)

@csrf.exempt
@app.route('/automations_update', methods=['POST'])
def automationsUpdate():

    # Set up Mongo
    stores = mongo.db.stores

    response = json.loads(request.data)

    stores.find_one_and_update({'store.name': response['shop']}, {
        '$set': {'store.access_token': request.cookies.get("access_token")},
        '$push': {'store.new_products_automation': {'$each': response['update_payload']
        }}
    }, upsert=True)

    # update
    return Response(status=200)


@app.route('/automations_retrieve', methods=['GET'])
def automationsRetrieve():

    # Set up Mongo
    stores = mongo.db.stores
    
    response = request.args.to_dict()

    collections = stores.find_one({'store.name': response['shop']})
    return {'data': collections['store'][response['automation']]}

# Homepage
@app.route('/home')
@app.route('/home/<shop>')
def index(shop=None):

    if not shop:
        shop = request.cookies.get("shop")
    else:
        shop = '{0}.myshopify.com'.format(shop)

    return render_template('index.html', shop=shop)

# V2

# Collection page
@app.route('/collection-new/<collection_id>', methods=['GET', 'POST'])
def collectionNew(collection_id):

    # from queue_work import testQueue

    collection_data = productsQuery(request.cookies.get("shop"), request.cookies.get("access_token"), collection_id)
    js_collection_data = (json.dumps(collection_data['js_collection_data'])
    .replace(u'<', u'\\u003c')
    .replace(u'>', u'\\u003e')
    .replace(u'&', u'\\u0026')
    .replace(u"'", u'\\u0027'))

    return render_template('collection-new.html', 
        collection_data=js_collection_data, 
        error=collection_data['error'], 
        cursor=collection_data['cursor'], 
        next_page=collection_data['next_page'], 
        collection_id=collection_id, 
        shop=request.cookies.get("shop")
    )

# Collection page ajax
@app.route('/collection-new-load', methods=['GET', 'POST'])
def collectionNewLoad():

    cursor = request.args.get('cursor', '')
    collection_id = request.args.get('collectionId', '')
    all_products = []
    
    
    # SORT THIS
    # Go through range, add products to all_products
    # rerun with new cursor, override all collection_data (remove data), add products to all_products again
    # Return
    for i in range(10):
        collection_data = productsQuery(request.cookies.get("shop"), request.cookies.get("access_token"), collection_id, cursor)
        all_products = all_products + collection_data['js_collection_data']['data']['collection']['products']['edges']
        if collection_data['next_page'] == False or collection_data['error'] != None: 
            break
        cursor = collection_data['cursor']

    collection_data['js_collection_data'] = (json.dumps(all_products)
        .replace(u'<', u'\\u003c')
        .replace(u'>', u'\\u003e')
        .replace(u'&', u'\\u0026')
        .replace(u"'", u'\\u0027'))

    return {'data': collection_data}

@app.route('/collection-new-save', methods=['GET', 'POST'])
def collectionNewSave():

    changes = request.args.get('changes', '')
    collection_id = request.args.get('collectionId', '')
    shop = request.cookies.get("shop")
    access_token = request.cookies.get("access_token")

    # TODO: Change to queue
    reorder_data = reorderQuery(shop, access_token, collection_id, changes)

    return {'data': reorder_data}


def reorderQuery(shop, access_token, collection_id, changes, rerun_count=0):

    error = ''
    reorder_status = graphql.reorderProducts(shop, access_token, collection_id, json.loads(changes))
    js_reorder_status = (json.dumps(reorder_status)
        .replace(u'<', u'\\u003c')
        .replace(u'>', u'\\u003e')
        .replace(u'&', u'\\u0026')
        .replace(u"'", u'\\u0027'))
    
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


def productsQuery(shop, access_token, collection_id, cursor=None, rerun_count=0):

    error = ''
    next_page = False
    collection_data = graphql.queryProducts(shop, access_token, collection_id, cursor)
    js_collection_data = collection_data

    # TODO: Need collection sort method

    if 'errors' in collection_data:
        if len(collection_data['errors']) > 0:
            error = collection_data['errors'][0]['message']
            # Waits and reruns function if throttled 
            if error == 'Throttled' and rerun_count < 10:
                required_time = findWaitTime(collection_data['extensions'])
                time.sleep(required_time)
                return productsQuery(shop, access_token, collection_id, cursor, rerun_count+1)

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

# Auto Basic
@app.route('/auto-smart', methods=['GET', 'POST'])
def autoSmart():

  shop = request.cookies.get("shop")
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
    app.run(host=os.environ.get("IP"), port=int(os.environ.get("PORT")), debug=True)

