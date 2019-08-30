from flask import Flask, render_template, request, redirect, Response, session
from flask_wtf.csrf import CSRFProtect
import urllib
import hmac
import hashlib
import random
import string

import requests
import json
import os
import validators

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET")
SECRET = os.environ.get("SHOPIFY_SECRET")

csrf = CSRFProtect()
csrf.init_app(app)

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

# Get products and collects through AJAX
@app.route('/ajax-collects', methods=['GET', 'POST'])
def ajax_collects():

    next_link = request.args.get('next_link', '')
    
    headers = {
        "X-Shopify-Access-Token": session.get("access_token"),
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
    products_response = requests.get("https://{0}{1}".format(session.get("shop"),
                                                    endpoint), headers=headers)
    products = json.loads(products_response.text)

    collect_products = {}
    for counter, collect in enumerate(collects['collects']):
        for product in products['products']:
            if product['id'] == collect['product_id']:
                total_variants = 0
                avail_variants = 0
                for variant in product['variants']:
                    if variant['inventory_quantity'] > 0:
                        avail_variants = avail_variants + 1
                    total_variants = total_variants + variant['inventory_quantity']
                availability = 'Available' if product['published_at'] else 'Unavailable'
                temp_product_collect = {
                    'product_id': product['id'],
                    'collect_id': collect['id'],
                    'position': collect['position'],
                    'product_title': product['title'],
                    'product_image': product['images'][0],
                    'product_available': availability,
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
        "X-Shopify-Access-Token": session.get("access_token"),
        "Content-Type": "application/json"
    }

    endpoint = "/admin/api/2019-07/" + apiSource +".json?collection_id=%s&limit=10" % collection_id
    response = requests.get("https://{0}{1}".format(session.get("shop"),
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

# # Install app route
# @app.route('/', methods=['GET'])
# def install():

#     headers = {
#         "X-Shopify-Access-Token": session.get("access_token"),
#         "Content-Type": "application/json"
#     }

#     return render_template('install.html')

# Display products from collection for sort
@app.route('/collection/<collection_id>', methods=['GET', 'POST'])
def collection(collection_id):

    response_status = 'unchanged'

    headers = {
                "X-Shopify-Access-Token": session.get("access_token"),
                "Content-Type": "application/json"
            }

    # Check is smart or custom
    endpoint = '/admin/api/2019-07/smart_collections/{0}.json'.format(collection_id)
    smart_collections = requests.get("https://{0}{1}".format(session.get("shop"),
                                                    endpoint), headers=headers)
    if smart_collections.status_code != 200:
        endpoint = '/admin/api/2019-07/custom_collections/{0}.json'.format(collection_id)
        custom_collections = requests.get("https://{0}{1}".format(session.get("shop"),
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

            response = requests.put("https://" + session.get("shop")
                                     + "/admin/api/2019-07/custom_collections/" + collection_id + ".json",
                                     data=json.dumps(payload), headers=headers)
        # Sort for smart collection
        else:
            response = requests.put("https://" + session.get("shop") + '/admin/api/2019-07/smart_collections/' + collection_id + '/order.json?' + request.form["products-switch"]
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
    products_response = requests.get("https://{0}{1}".format(session.get("shop"),
                                                    endpoint), headers=headers)
    products = json.loads(products_response.text)

    shop = request.args.get("shop")

    if collects and products:
        return render_template('collection.html', collects=collects, products=products.get("products"), response_status=response_status, custom_collection=custom_collection, manual_sort_order=manual_sort_order, next_link=next_link, next_active=next_active, shop=shop)
    else:
        return False

# Install route
@app.route('/install', methods=['GET'])
def install():

    # Create nonce
    global nonce
    nonce = randomword(12)

    shop = request.args.get("shop")

    if authenticate_hmac(request):
        return render_template('install.html', nonce=nonce, shop=shop)

# Contact page
@app.route('/contact', methods=['GET'])
def contact():

    shop = request.args.get("shop")

    return render_template('contact.html', shop=shop)

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
            "client_id": os.environ.get("SHOPIFY_SECRET"),
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

            session['access_token'] = resp_json.get("access_token")
            session['shop'] = request.args.get("shop")

            return redirect('/home')
    else:
        print(resp.status_code, resp.text)
        raise Exception("Cannot connect to app")

# Homepage
@app.route('/home')
def index():

    shop = request.args.get("shop")

    return render_template('index.html', shop=shop)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), port=int(os.environ.get("PORT")), debug=True)

