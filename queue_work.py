import requests
import json
from utils import checkCollection
from flask import Response
from app import loopProducts

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
	            all_products = loopProducts('', False, collect['collection_id'], shop, access_token, product_id, 'smart')
	            # Add product ID to the front
	            all_products = 'products[]={0}&{1}'.format(product_id, all_products).rstrip('&')
	            # Sort smart collection
	            response = requests.put("https://" + shop + '/admin/api/2019-07/smart_collections/' + collectionId + '/order.json?' + all_products
	                        , headers=headers)
	               
	    elif collectionInfo['manual_sort_order'] and collectionInfo['custom_collection']:

	        endpoint = '/admin/api/2019-07/collects.json?product_id={0}&collection_id={1}'.format(product_id, collectionId)
	        collect_reponse = requests.get("https://{0}{1}".format(shop,
	                                                            endpoint), headers=headers)

	        collect_reponse = json.loads(collect_reponse.text)
	        if collect_reponse['collects']:
	            collect, = collect_reponse['collects']
	            # If exists, find all collect ids of collection
	            all_products = {
	                'custom_collection': {
	                    'id': collect['collection_id'],
	                    'collects': []
	                }
	            }
	            all_products = loopProducts(all_products, False, collect['collection_id'], shop, access_token, product_id, 'custom')
	            # Add collect ID to the front
	            all_products['custom_collection']['collects'].append({
	                'id': collect['id'],
	                'position': 1
	            })
	            # Sort for custom collection
	            print(all_products)
	            response = requests.put("https://" + shop
	                             + "/admin/api/2019-07/custom_collections/" + collectionId + ".json",
	                             data=json.dumps(all_products), headers=headers)


	return True