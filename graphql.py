import requests
from python_graphql_client import GraphqlClient

def reorderProducts(store, access_token, collection_id, changes):

	headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

	client = GraphqlClient(endpoint="https://" + store + "/admin/api/2020-04/graphql.json")
	
	query = """
	mutation collectionReorderProducts($id: ID!, $moves: [MoveInput!]!) {
	  collectionReorderProducts(id: $id, moves: $moves) {
	    job {
	      id
	    }
	    userErrors {
	      field
	      message
	    }
	  }
	}
	"""

	if not 'gid://shopify/Collection/' in collection_id:
		collection_id = 'gid://shopify/Collection/{0}'.format(collection_id)
	variables = {'id': collection_id, 'moves': changes}

	data = client.execute(query=query, headers=headers, variables=variables)

	return data

def removeProducts(store, access_token, collection_id, product_id):

	headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

	client = GraphqlClient(endpoint="https://" + store + "/admin/api/2020-04/graphql.json")
	
	query = """
	mutation collectionRemoveProducts($id: ID!, $productIds: [ID!]!) {
	  collectionRemoveProducts(id: $id, productIds: $productIds) {
	    job {
	      id
	    }
	    userErrors {
	      field
	      message
	    }
	  }
	}
	"""

	if not 'gid://shopify/Collection/' in collection_id:
		collection_id = 'gid://shopify/Collection/{0}'.format(collection_id)
	variables = {'id': collection_id, 'productIds': [product_id]}

	data = client.execute(query=query, headers=headers, variables=variables)

	return data

# Used for manual sort page
def queryProducts(store, access_token, collection_id, cursor=None, withVariants=False):

	headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

	client = GraphqlClient(endpoint="https://" + store + "/admin/api/2020-04/graphql.json")
	
	if withVariants == False or withVariants == 'false':
		query = """
	    query MyQuery($collection: ID!, $cursor: String) {
		  collection(id: $collection) {
		  	productsCount
		  	sortOrder
		  	ruleSet {
	          rules {
	            column
	          }
	        }
		    products(first: 250, after: $cursor) {
		      pageInfo {
		        hasNextPage
		        hasPreviousPage
		      }
		      edges {
		        cursor
		        node {
		          title
		          onlineStoreUrl
		          id
		          createdAt
		          priceRange {
		            minVariantPrice {
		              amount
		              currencyCode
		            }
		          }
		          tracksInventory
		          totalInventory
		          featuredImage {
	                transformedSrc(maxHeight: 300)
	              }
		        }
		      }
		    }
		  }
		}
		"""
	else:
		query = """
	    query MyQuery($collection: ID!, $cursor: String) {
		  collection(id: $collection) {
		  	productsCount
		  	sortOrder
		  	ruleSet {
	          rules {
	            column
	          }
	        }
		    products(first: 30, after: $cursor) {
		      pageInfo {
		        hasNextPage
		        hasPreviousPage
		      }
		      edges {
		        cursor
		        node {
		          title
		          onlineStoreUrl
		          id
		          createdAt
		          priceRange {
		            minVariantPrice {
		              amount
		              currencyCode
		            }
		          }
		          tracksInventory
		          totalInventory
		          featuredImage {
	                transformedSrc(maxHeight: 300)
	              }
	              variants(first: 14) {
					pageInfo {
						hasNextPage
						hasPreviousPage
					}
			        edges {
					  cursor
			          node {
						compareAtPrice
						price
			            title
			            inventoryQuantity
			          }
			        }
			      }
		        }
		      }
		    }
		  }
		}
		"""
	
	variables = {'collection': 'gid://shopify/Collection/{0}'.format(collection_id), 'cursor': cursor}

	data = client.execute(query=query, headers=headers, variables=variables)
	return data

def queryVariants(store, access_token, product_id, cursor):
	headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

	client = GraphqlClient(endpoint="https://" + store + "/admin/api/2020-04/graphql.json")

	query = """
		query GetProductsById($id: ID!, $cursor: String) {
			product(id: $id) {
				variants(first: 30, after: $cursor) {
					pageInfo {
						hasNextPage
						hasPreviousPage
					}
			        edges {
					  cursor
			          node {
						compareAtPrice
						price
			            title
			            inventoryQuantity
			          }
			        }
			    }
			}
		}
	"""

	variables = {'id': product_id, 'cursor': cursor}
	data = client.execute(query=query, headers=headers, variables=variables)
	return data


def queryCollectionsOfProducts(store, access_token, product_id, cursor=None):

	headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

	client = GraphqlClient(endpoint="https://" + store + "/admin/api/2020-04/graphql.json")
	
	query = """
    query MyQuery($product: ID!, $cursor: String) {
      product(id: $product) {
        title
        collections(first: 250, after: $cursor) {
        	pageInfo {
        	  hasNextPage
        	  hasPreviousPage
        	}
	        edges {
	        	cursor
	          node {
	            id
	            sortOrder
	            productsCount
	          }
	      	}
	    	}
      }
	}
	"""

	variables = {'product': 'gid://shopify/Product/{0}'.format(product_id), 'cursor': cursor};

	data = client.execute(query=query, headers=headers, variables=variables)

	return data


def queryCollections(store, access_token, search, cursor, direction):

	headers = {
		"X-Shopify-Access-Token": access_token,
		"Content-Type": "application/json"
	}

	client = GraphqlClient(endpoint="https://" + store +
						   "/admin/api/2020-04/graphql.json")

	if direction == 'prev':
		query = """
		query MyQuery($cursor: String, $search: String) {
			collections(last: 20, before: $cursor, query:$search) {
				edges {
					cursor
					node {
						title
						id
						sortOrder
						handle
						image {
							transformedSrc(maxHeight: 200)
						}
					}
				}
				pageInfo {
					hasNextPage
					hasPreviousPage
				}
			}
		}
		"""
	else:
		query = """
		query MyQuery($cursor: String, $search: String) {
			collections(first: 20, after: $cursor, query:$search) {
				edges {
					cursor
					node {
						title
						id
						sortOrder
						handle
						image {
							transformedSrc(maxHeight: 200)
						}
					}
				}
				pageInfo {
					hasNextPage
					hasPreviousPage
				}
			}
		}
		"""

	variables = {'cursor': cursor, 'search': search}

	data = client.execute(query=query, headers=headers, variables=variables)

	return data

def updateCollection(store, access_token, collection, sortOrder):

	headers = {
		"X-Shopify-Access-Token": access_token,
		"Content-Type": "application/json"
	}

	client = GraphqlClient(endpoint="https://" + store +
						   "/admin/api/2020-04/graphql.json")

	query = """
		mutation collectionUpdate($input: CollectionInput!) {
			collectionUpdate(input: $input) {
				collection {
					id
				}
				job {
					id
				}
				userErrors {
					field
					message
				}
			}
		}
	"""

	variables = {'input': {'id': collection, 'sortOrder': sortOrder }}

	data = client.execute(query=query, headers=headers, variables=variables)

	return data

def collectionCreate(store, access_token):

	headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

	client = GraphqlClient(endpoint="https://" + store + "/admin/api/2020-04/graphql.json")
	
	query = """
	  mutation collectionCreate($input: CollectionInput!) {
	    collectionCreate(input: $input) {
	      collection {
	        id
	      }
	      userErrors {
	        field
	        message
	      }
	    }
  	}
	"""

	variables = {'input': 'gid://shopify/Product/{0}'.format(product_id), 'cursor': cursor};

	data = client.execute(query=query, headers=headers, variables=variables)

	return data


