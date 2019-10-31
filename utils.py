import requests
import json
import time
from flask import Response
from app import loopProducts

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

def sort_collection(data):

	shop = data['shop']
	access_token = data['access_token']
	product_id = data['product_id']
	collectionId = data['collectionId']
	headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

	for collection in data['collectionId']:
	    collectionId = collection['collectionId']
	    collectionInfo = checkCollection(collectionId, shop, headers)

	    if collectionInfo == 'Error: Failed collection retrieval':
	        return Response(status=500)
	    # If smart collection
	    if collectionInfo['manual_sort_order'] and not collectionInfo['custom_collection']:
	    
	        endpoint = '/admin/api/2019-07/collects.json?product_id={0}&collection_id={1}'.format(product_id, collectionId)
	        collect_reponse = requests.get("https://{0}{1}".format(shop,
	                                                            endpoint), headers=headers)

	         # Check collect of collection if and product id
	        collect_reponse = json.loads(collect_reponse.text)
	        if collect_reponse['collects']:
	            collect, = collect_reponse['collects']
	             # If exists, find all products ids of collection
	            all_products = loopProductsSmart('', False, collect['collection_id'], shop, access_token, product_id)
	            # Add product ID to the front
	            all_products = 'products[]={0}&{1}'.format(product_id, all_products).rstrip('&')
	            # Sort smart collection
	            response = requests.put("https://" + shop + '/admin/api/2019-07/smart_collections/' + collectionId + '/order.json?' + all_products
	                        , headers=headers)
	               
	    elif collectionInfo['manual_sort_order'] and collectionInfo['custom_collection']:

	        endpoint = '/admin/api/2019-07/collects.json?product_id={0}&collection_id={1}'.format(product_id, collectionId)
	        collect_reponse = requests.get("https://{0}{1}".format(shop,
	                                                            endpoint), headers=headers)

	        try:
	            collect_reponse = json.loads(collect_reponse.text)
	            collect, = collect_reponse['collects']
	        except:
	            return Response(status=200)
	        else:
	            # If exists, find all collect ids of collection
	            all_products_dict = {
	                'custom_collection': {
	                    'id': collect['collection_id'],
	                    'collects': []
	                }
	            }
	            all_products = loopProductsCustom(all_products_dict, False, collect['collection_id'], request.headers.get('X-Shopify-Shop-Domain'), access_token_response['store']['access_token'], product_id)
	            # Add collect ID to the front
	            all_products['custom_collection']['collects'].append({
	                'id': collect['id'],
	                'position': 1
	            })
	            # Sort for custom collection
	            response = requests.put("https://" + shop
	                             + "/admin/api/2019-07/custom_collections/" + collectionId + ".json",
	                             data=json.dumps(all_products), headers=headers)

	return True


	