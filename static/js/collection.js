collectionUtils = {
	initElements() {
		this.createLoading();
		if(error) {
			collectionUtils.showMessage('Error', 'Unexpected error. Please try again');
		} else {
			let productsTime;
			let products; 
			productsToAdd = {};

			try {
				// Manual error
				if(collectionInfo['data']['collection']['sortOrder'] != 'MANUAL') {
					document.querySelector('#manual-error').classList.remove('hide');
					// document.querySelectorAll('.display-options').forEach(function(e) { e.classList.add('hide') });
					// document.querySelectorAll('.btn').forEach(function(e) { e.classList.add('hide') });
				}

				products = collectionInfo.data.collection.products.edges;
				let productsCount = collectionInfo.data.collection.productsCount;
				if(productsCount > 50) {
					let estimatedMultiplier = limited ? 8 : 3
					let estimatedTime = productsCount / 50 * estimatedMultiplier;
					document.querySelector('#load-all-time').innerHTML = estimatedTime > 2 ? `Estimated load time: ${estimatedTime.toFixed(0)} secs` : '';
					if(estimatedTime > 2) {
						document.querySelector('#sort-all-time').innerHTML = `Quick Sort will reorder the products below based on your selection. With the size of this collection, sorting may take up to ${(estimatedTime * 1.5).toFixed(0)} secs to complete. Don't forget to Save when you're happy with your changes.`
					} else {
						document.querySelector('#sort-all-time')[0].remove();
					}
				}
				if(productsCount > 500) {
					let largeCollectionMessage = document.querySelector('#large-collection-error');
					if(largeCollectionMessage) {
						document.querySelector('#large-collection-error').classList.remove('hide');
					}
				}
			} catch(e) {
				throw e;
				collectionUtils.showMessage('Error', 'Unexpected error. Please try again');
			}
			try {
				for(let product of products) {
					try {
						productsToAdd[product.node.id] = new Product(product.node);
					} catch(e) {
						throw e;
						collectionUtils.showMessage('Error', 'Unexpected error. Please try again');
					}
				}

				window.sortHelper = new sortHelper();
				collectionUtils.createCards(productsToAdd);
				document.querySelector('#productsPerRow').addEventListener('change', function(e) {
					collectionUtils.updateRowsInfo(e.target.value);
					utils.setCookie('rows', (e.target.value).replace('%', ''), 200);
				});
				collectionUtils.updateRowsInfo();
				collectionUtils.initSortable();
				collectionUtils.initDisplayInfo();
			} catch(e) {
				console.log('Error', e);
				collectionUtils.showMessage('Error', 'Unexpected error. Please try again');
			}
		}
	},

	initTitleBar: function() {
		save.set({disabled: true});
		const saveCollection = save.subscribe(Button.Action.CLICK, data => {
			save.set({disabled: true});
			let allProductCards = document.querySelectorAll('.products__card');
			let positionChanges = [];
			let last = false;
			allProductCards.forEach(function(e, i) {
			    let defaultPosition = e.getAttribute('data-positon');
			    let productId = e.getAttribute('data-product-id');
			    if(i != defaultPosition && productId) {
			    	positionChanges.push({
			    		'newPosition': i.toString(),
			    		'id': productId
			    	})
			    };
			})

			if(positionChanges != [] && positionChanges) {
				// https://stackoverflow.com/questions/8495687/split-array-into-chunks
				// Split changes into chunks of 150
				var i,j,temparray,chunk = 150;
				for (i=0, j=positionChanges.length; i<j; i+=chunk) {
				    temparray = positionChanges.slice(i,i+chunk);
				    last = !(i+chunk < j);
				    // TODO: Return fail/success and stop if failed
				    collectionUtils.submitChanges(temparray, last, positionChanges.length)
				}
			} else {
				_this.showMessage('Error', 'Unexpected error. Some or all of the sorting has not been completed successfully. Please try again or contact support if this issue persists');
			}
		});


		const titleBarOptions = {
		  title: 'Collection',
		  buttons: {
		    primary: save,
		    secondary: [groupButton]
		  },
		};
		const myTitleBar = TitleBar.create(app, titleBarOptions);
	},

	formatPrice: function(currencyCode, amount) {
		let userLanguage = navigator.language ? navigator.language : 'en-US';
		const formatter = new Intl.NumberFormat('en-US', {
		  style: 'currency',
		  currency: currencyCode,
		  minimumFractionDigits: 2
		});
		return formatter.format(amount);
	},

	createLoading() {
		app.subscribe(Loading.ActionType.START, () => {
		  window['loading'] = true;
		});
		app.subscribe(Loading.ActionType.STOP, () => {
		  window['loading'] = false;
		});
	},

	initLoading(direction) {
		if(direction == 'start') {
			if(!window['loading']) { loading.dispatch(Loading.Action.START) };
			document.getElementById('full-screen-overlay').classList.add('full-screen-overlay--active');
		} else {
			loading.dispatch(Loading.Action.STOP);
			document.getElementById('full-screen-overlay').classList.remove('full-screen-overlay--active');
		}
	}, 

	submitChanges(positionChanges, last, totalChanges) {
		var _this = this;
    	$.ajax({
    	  url: 'https://shopify-stock-app.herokuapp.com/collection-new-save',
    	  type: 'POST',
    	  contentType: 'application/json;charset=UTF-8',
    	  data: JSON.stringify({ 
    	  	'changes' : positionChanges,
    	    'collectionId': collectionId,
    	   }),
    	})
    	.done(function(res) {
    		// TODO: If certain size, say it's been scheduled and to come back
    		try {
    			if(res['data']['error']) {
    				_this.showMessage('Error', 'Unexpected error. Some or all of the sorting has not been completed successfully. Please try again or contact support if this issue persists');
    			} else {
    				if(last) {
    					_this.showMessage('Successfully Scheduled', `Your changes have been successfully scheduled, they will be live within a few minutes.`);
    				}
    			}
    		} catch {
    			_this.showMessage('Error', 'Unexpected error. Some or all of the sorting has not been completed successfully. Please try again or contact support if this issue persists');
    		}
    	})
    	.fail(function(xhr, status, error) {
    		_this.showMessage('Error', 'Unexpected error. Some or all of the sorting has not been completed successfully. Please try again or contact support if this issue persists');
    	  console.log('Error: ' + error);
    	});
    },
    showMessage(title, message) {
		document.querySelector('#completion-modal .modal-title').innerHTML = title;
		document.querySelector('#completion-modal .modal-body').innerHTML = `<p>${message}</p>`;
		$('#completion-modal').modal()
	},

	showDeleteModal(name, id) {
		document.querySelector('#delete-product-name').innerHTML = name;
		document.querySelector('#delete-product-data').setAttribute('data-product', id);
		$('#delete-product-modal').modal()
	},

	removeProduct() {
		let productId = document.querySelector('#delete-product-data').getAttribute('data-product');
		let _this = this;
		$.ajax({
			url: 'https://shopify-stock-app.herokuapp.com/product-remove',
			contentType: 'application/json;charset=UTF-8',
			type: 'POST',
			data: JSON.stringify({
				'productId': productId,
				'collectionId': collectionId, 
			})
		})
		.done(function(res) {
			let errorMessage = 'Unexpected error. There has been an issue removing this product from the collection. Please try again or contact support if this issue persists'
			console.log(res)
			try {
				if(res['data']['data']['collectionRemoveProducts']['userErrors'].length > 0) {
					console.log(res['data']['collectionRemoveProducts']['userErrors'])
					_this.showMessage('Error 1', errorMessage);
				} else {
					_this.showMessage('Successfully Scheduled', `The product removal has been scheduled, this will be live within a few minutes.`);
					let removedProduct = document.querySelector(`[data-product-id="${productId}"]`);
					removedProduct.parentNode.removeChild(removedProduct);
				}
			} catch(e) {
				console.log(e);
				_this.showMessage('Error 2', errorMessage);
			}
		})
		.fail(function(xhr, status, error) {
			console.log('Error: ' + error);
			_this.showMessage('Error 3', errorMessage);
		});
	},

	updateRowsInfo(width=false) {
		if(!width) {
			width = utils.getCookie('rows') ? utils.getCookie('rows') + '%' : width;
		}
		width = !width ? '20%' : width;
		window['rows'] = !width ? '20%' : width;
		document.querySelector('#productsPerRow').value = width;
		let productCards = document.querySelectorAll('.products__card');
		for(let card of productCards) {
			card.style.width = width;
		}
	},

	initDisplayInfo() {
		for(let option of displayOptions) {
			let tempCookie = utils.getCookie(option);
			window[option] = !tempCookie ? 'false' : tempCookie;
			if(!tempCookie) {
				utils.setCookie(option, 'false', 300);
			}
			let tempOptionSelector = document.querySelector('#' + option);
			if(tempCookie == 'true') {
				tempOptionSelector.setAttribute('checked', true);
			}
		}
		this.updateDisplayInfo(displayOptions);
	},

	updateDisplayInfo(updatingDisplayOptions) {
		for(let option of updatingDisplayOptions) {
			let tempValue = window[option] ? window[option] : utils.getCookie(option);
			let tempButtonSelector = document.querySelector('#button-' + option);
			if(tempButtonSelector) {
				if(tempValue == 'true') {
					tempButtonSelector.classList.add('card-display-off');
				} else {
					tempButtonSelector.classList.remove('card-display-off');
				}
			}
			let tempElements = document.querySelectorAll('.products__' + option);
			for(let element of tempElements) {
				if(tempValue == 'true') {
					element.classList.add('d-none');
				} else {
					element.classList.remove('d-none');
				}
			}
		}
	},

	displayButton(option) {
		let tempOptionSelector = document.querySelector('#' + option);
		if(window[option] == 'true') {
			window[option] = 'false';
			if(tempOptionSelector) {
				tempOptionSelector.removeAttribute('checked');
			}
		} else {
			window[option] = 'true';
			if(tempOptionSelector) {
				tempOptionSelector.setAttribute('checked', window[option]);
			}
		}
		utils.setCookie(option, window[option], 200);
		this.updateDisplayInfo([option]);
	},

	createCards(elements, callback=null) {
		let productsToAdd = '';
		let counter = 0;
		for(let product of Object.values(elements)) {
			productsToAdd += product.element;
			counter++
		}
		document.querySelector('#products__container').innerHTML += productsToAdd;

		if(!callback) { collectionUtils.initLoading('stop'); }
		// If not init call
		collectionUtils.updateDisplayInfo(displayOptions);
		collectionUtils.initSortable(callback);

	   // Enable popovers
	  $(function () {
	    $('[data-toggle="tooltip"]').tooltip()
	  })
	},


	addCards(callback=null) {
		const _this = this;
		let productsToAdd = {};
		let interations = window.responses.length;
		for(let response of window.responses) {
			for(let product of response) {
				try {
					let tempProductObj = new Product(product.node);
					productsToAdd[product.node.id] = tempProductObj;
				} catch(e) {
					console.log('Error', e)
					throw e;
					collectionUtils.showMessage('Error', 'Unexpected error. Please try again');
				}
			}
			interations--
			if(interations == 0) {
				_this.createCards(productsToAdd, callback);	
				window.responses = []
			}
		}
	},

	async initSortable(callback=null) {
		var el = document.getElementById('products__container');
		window.sortable = await new Sortable.create(el, {
			easing: "cubic-bezier(1, 0, 0, 1)",
			multiDrag: true,
			dataIdAttr: 'data-product-id',
			selectedClass: 'multiple-sortable-selected', 
			onEnd: function(evt) {
				collectionUtils.updateRowsInfo(window['rows']);
				save.set({disabled: false});
			},
		});
		if(callback) { callback(); }
	},

	loadAll(callback=null) {
		loadRemaining = false;
		window.sortable.option("disabled", true);

		collectionUtils.initLoading('start');
		this.loadMore(true, callback, null);
	},

	loadMore(rerun=false, callback=null, cursor=null) {
		window.responses = window.responses || [];
		const _this = this;
		save.set({disabled: true})
		document.querySelector('#load-more').setAttribute('disabled', true);
		document.querySelector('#load-all').setAttribute('disabled', true);

		cursor = cursor || document.querySelector('#load-more').getAttribute('data-next-link');
		if(cursor) {
			$.ajax({
			  url: 'https://shopify-stock-app.herokuapp.com/collection-new-load',
			  type: 'GET',
			  data: { 
			  	'limited': limited,
			  	'cursor' : cursor,
			    'csrfmiddlewaretoken': csrfToken,
			    'collectionId': collectionId
			   },
			})
			.done(function(res) {
				products = JSON.parse(res['data']['js_collection_data'])
				window.responses.push(products);
				if(res['data']['error']) {
					collectionUtils.initLoading('stop');
					// TODO: Error
				} else {
					if(res['data']['next_page'] && rerun) {
							_this.disableLoadMore();
							_this.loadMore(limited, true, callback, res['data']['cursor']);
							document.querySelector('#load-more').setAttribute('data-next-link', res['data']['cursor']);
					} else {
						if(res['data']['next_page']) { 
							document.querySelector('#load-more').setAttribute('data-next-link', res['data']['cursor']); 
							document.querySelector('#load-more').removeAttribute('disabled');
							document.querySelector('#load-all').removeAttribute('disabled');
						} else {
							loadRemaining = false;
							collectionUtils.initLoading('stop');
						}
						_this.addCards(callback);
					}
				}
			})
			.fail(function(err) {
			  console.log('Error: ' + err);
			  collectionUtils.initLoading('stop');
			});
		} else {
			collectionUtils.initLoading('stop');
			// TODO: Error
		}
	},


	disableLoadMore() {
		try { 
			collectionUtils.initLoading('start');
			window.sortable.option('disabled', false); 
			document.querySelector('#load-more').setAttribute('disabled', true);
			document.querySelector('#load-all').setAttribute('disabled', true);
			document.querySelector('#load-all-time').innerHTML = '';
			document.getElementById('sort-all-time').classList.add('hide')
		} catch(e) {
			console.log(e);
		}
	}
}

class sortHelper {
	inventoryBottom() {
		if(loadRemaining) {
			collectionUtils.loadAll(this.inventoryBottomSort);
		} else {
			this.inventoryBottomSort();
		}
	}

	inventoryBottomSort() {
		let sortOrderChanged = false;
		let currentOrder = sortable.toArray();
		let begArray = [];
		let endArray = [];

		currentOrder.forEach(function(e, i) {
			let inventoryElement = document.querySelector('[data-product-id="' + e + '"] .products__totalInventory');
			if(inventoryElement) {
				let totalInventory = inventoryElement.getAttribute('data-inventory');
				if(totalInventory != 'unset') {
					if(totalInventory < 1) {
						sortOrderChanged = true;
						endArray.push(e);
					} else {
						begArray.push(e);
					}
				} else {
					begArray.push(e);
				}
			}
		});
		if(sortOrderChanged) {
			save.set({disabled: false});
		}
		sortable.sort(begArray.concat(endArray));
		collectionUtils.initLoading('stop');
		// TODO: Add completed message
	}

	inventoryNumSort() {
		let inventoryCountCompare = document.querySelector('#inventoryCountCompare').value;
		let inventoryCountSelect = document.querySelector('#inventoryCountSelect').value;
		let inventoryCountInput = document.querySelector('#inventoryCountInput').value;
		let currentOrder = window.sortable.toArray().slice(0);
		let begArray = [];
		let endArray = [];
		let inventoryElement;
		// Loop from bottom if adding products to start (so it remains in order)
		let sortOrderChanged = false;

		currentOrder.map((e, i) => {
			let inventoryElement = document.querySelector('[data-product-id="' + e + '"] .products__totalInventory');
			if(inventoryElement) {
				let totalInventory = inventoryElement.getAttribute('data-inventory');
				// Build comparison formula
				let inventoryComparison = `${totalInventory}${inventoryCountCompare}${inventoryCountInput}`
				if(totalInventory != 'unset') {
					// Check if comaparison is true
					if(eval(inventoryComparison)) {
						sortOrderChanged = true;
						endArray.push(e);
					} else {
						begArray.push(e);
					}
				} else {
					begArray.push(e);
				}
			}
		});
		if(sortOrderChanged) {
			save.set({disabled: false});
		}
		let fullArray = inventoryCountSelect == 'bottom' ? begArray.concat(endArray) : endArray.concat(begArray)
		window.sortable.sort(fullArray);
		collectionUtils.initLoading('stop');
		// TODO: Add completed message
	}

	inventoryNum() {
		if(loadRemaining) {
			collectionUtils.loadAll(this.inventoryNumSort);
		} else {
			this.inventoryNumSort();
		}
	}

	daysSortWork() {
		let createdDateCompare = document.querySelector('#createdDateCompare').value;
		let createdDateSelect = document.querySelector('#createdDateSelect').value;
		let createdDateInput = document.querySelector('#createdDateInput').value;
		let currentOrder = window.sortable.toArray().slice(0);
		let begArray = [];
		let endArray = [];
		let inventoryElement;
		// Loop from bottom if adding products to start (so it remains in order)
		let sortOrderChanged = false;

		currentOrder.map((e, i) => {
			let daysElement = document.querySelector('[data-product-id="' + e + '"] .products__daysCreated');
			if(daysElement) {
				let totalDays = daysElement.getAttribute('data-days');
				// Build comparison formula
				let daysComparison = `${totalDays}${createdDateCompare}${createdDateInput}`
					// Check if comaparison is true
				if(eval(daysComparison)) {
					sortOrderChanged = true;
					endArray.push(e);
				} else {
					begArray.push(e);
				}
			} else {
				begArray.push(e);
			}
		});
		if(sortOrderChanged) {
			save.set({disabled: false});
		}
		let fullArray = createdDateSelect == 'bottom' ? begArray.concat(endArray) : endArray.concat(begArray)
		window.sortable.sort(fullArray);
		collectionUtils.initLoading('stop')
		// TODO: Add completed message
	}

	daysSort() {
		if(loadRemaining) {
			collectionUtils.loadAll(this.daysSortWork);
		} else {
			this.daysSortWork();
		}
	}

	selected() {
		if(loadRemaining) {
			collectionUtils.loadAll(this.selectedSortWork);
		} else {
			this.selectedSortWork();
		}
	}

	selectedSort() {
		let selectedCountSelect = document.querySelector('#selectedCountSelect').value;
		let currentOrder = window.sortable.toArray().slice(0);
		let begArray = [];
		let endArray = [];
		let sortOrderChanged = false;

		currentOrder.map((e, i) => {
			let variantElement = document.querySelector('[data-product-id="' + e + '"]');
			if(variantElement) {
				if(variantElement.classList.contains('multiple-sortable-selected')) {
					sortOrderChanged = true;
					endArray.push(e);
				} else {
					begArray.push(e);
				}
			} else {
				begArray.push(e);
			}
		});
		if(sortOrderChanged) {
			save.set({disabled: false});
		}
		let fullArray = selectedCountSelect == 'bottom' ? begArray.concat(endArray) : endArray.concat(begArray)
		window.sortable.sort(fullArray);
		collectionUtils.initLoading('stop')
		// TODO: Add completed message
	}
}

// Collection page product builder
class Product {
  constructor(product) {
  	this.title = product.title;
  	// TODO: Add placeholder image
  	this.featuredImage = product.featuredImage ? product.featuredImage.transformedSrc : '';
  	this.totalInventory = product.totalInventory;
  	this.tracksInventory = product.tracksInventory;
  	// this.variants = product.variants ? product.variants.edges : null;
  	this.minPrice = product.priceRange.minVariantPrice.amount;
  	this.currency = product.priceRange.minVariantPrice.currencyCode;
  	this.storeUrl = product.onlineStoreUrl;
  	this.createdDate = product.createdAt;
  	if(product.variants) { this.variants = product.variants.edges };
  	this.id = product.id;
  	window['productCount'] = window['productCount'] || 0;
  }

  get element() {
  	return this.createElement();
  }

  createHeader() {
  	let cardImage = this.featuredImage ? `<img src="${this.featuredImage}" class="card-img-top">` : '';
  	let cardHeader;
  	let cardTop = `
	  				<div data-product-id="${this.id}" data-positon="${window['productCount']}" class="products__card ${this.storeUrl ? '' : 'products__unavailable'}" style="width: ${window['rows'] || '20%'};">
	  					<div class="card">
	  					<a data-toggle="tooltip" data-placement="bottom" title="View product in new tab" class="view-product-icon fa fa-eye" target="_blank" href="https://${shop}/admin/products/${this.id.replace('gid://shopify/Product/', '')}"></a>`;
	let cardRemove = '';
	if(collectionInfo.data.collection.ruleSet == null) {
		cardRemove = `<i data-toggle="tooltip" data-placement="bottom" title="Remove product from collection" onclick="collectionUtils.showDeleteModal('${this.title}', '${this.id}')" class="fa fa-times remove-product-icon" aria-hidden="true"></i>`
	}

	window['productCount']++
	return cardTop + cardRemove + cardImage;
  }

  createTitle() {
  	let cardBody = '<div class="card-body">'
  	let cardTitle = this.title ? `<p class="products__title">${this.title}</p>` : `<p class="products__title">Title Not Found</p>`;
  	let price = this.currency && this.minPrice ? collectionUtils.formatPrice(this.currency, this.minPrice / 100) : null;
  	let cardPrice = price ? `<p class="products__productPrice">${price}</p>` : ''
  	return cardBody + cardTitle + cardPrice
  }

  createVariants() {
  	let cardVariants
  	if(this.variants) {
  		cardVariants = `<ul class="list-group products__productVariants">`
  		this.variants.map(x => {
  			cardVariants = cardVariants + `
  			<li class="list-group-item d-flex justify-content-between align-items-center">
  			  ${x.node.title == 'Default Title' ? 'Default' : x.node.title}
  			  <span class="badge ${x.node.inventoryQuantity < 1 ? 'badge-danger' : x.node.inventoryQuantity < 5 ? 'badge-warning' : 'badge-primary'} badge-pill">${x.node.inventoryQuantity}</span>
  			</li>
  			`
  		})
  		cardVariants = cardVariants + `</ul>`
  	}
  	return cardVariants
  }

  createStandardInfo() {
  	let cardDate = '';
  	let cardAvailable = `<p class="products__availability"><i class="fa ${this.storeUrl ? 'fa-check' : 'fa-times'}" aria-hidden="true"></i> <span data-toggle="tooltip" data-placement="top" title="Available to purchase through the online store sales channel">${this.storeUrl != null ? 'Available' : 'Unavailable'}</span></p>`;
  	if(this.createdDate) {
  		let daysDiff = (utils.daysBetween(this.createdDate, Date.now())).toFixed(0);
  		cardDate = daysDiff ? `<p class="products__daysCreated" data-days="${daysDiff}"><i class="fa fa-calendar" aria-hidden="true"></i> <span data-toggle="tooltip" data-placement="top" title="Days since product was created">${daysDiff} days</span></p>` : '';
  	}
		let cardInventory = this.totalInventory != null ? `<p class="products__totalInventory" data-inventory="${this.tracksInventory ? this.totalInventory : 'unset'}"><i class="fa fa-barcode" aria-hidden="true"></i> <span data-toggle="tooltip" data-placement="top" title="Number left in stock at all locations (if inventory is tracked)">${this.tracksInventory ? this.totalInventory : 'Not tracked'}</span></p>` : '';

  	return cardAvailable + cardDate + cardInventory;
  }

  createElement() {
  	let card = '';
  	let cardHeader = this.createHeader();
  	let cardTitle = this.createTitle();
  	let cardStandardInfo = this.createStandardInfo();
  	let cardVariants = this.createVariants();
  	let cardBodyFooter = `</div>`
	let cardEnd = '</div></div></div>'
	let cardElements = [cardHeader, cardTitle, cardStandardInfo, cardBodyFooter, cardVariants, cardEnd];
	for(let element of cardElements) {
		if(element) {
			card = card + element;
		};
	};

  	return card;
  }
}