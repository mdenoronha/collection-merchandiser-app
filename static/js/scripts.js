// AutoSmart
scripts = {
	init: function() {
		let template = document.querySelector('meta[name="template"]');
		if(template) {
			let templateName = template.getAttribute('content');
			let templateNameStripped = templateName.replace('.html', '')
			if(this[templateNameStripped]) {
				this[templateNameStripped]()
			}
		}
	},

	collection: function() {
		collectionUtils.initTitleBar();
		collectionUtils.initElements();
		$('[data-toggle="tooltip"]').tooltip();
	},

	contact: function() {
		const titleBarOptions = {
		  title: 'Contact',
		  buttons: {
		    secondary: [groupButton]
		  },
		};
		const myTitleBar = TitleBar.create(app, titleBarOptions);
	},

	error: function() {
		// Title bar
		const titleBarOptions = {
		  title: 'Error',
		  buttons: {
		    secondary: [groupButton]
		  },
		};
		const myTitleBar = TitleBar.create(app, titleBarOptions);
	},

	instructions: function() {
		// Title bar
		const titleBarOptions = {
		  title: 'Instructions',
		  buttons: {
		    secondary: [groupButton]
		  },
		};
		const myTitleBar = TitleBar.create(app, titleBarOptions);
	},

	privacy_policy: function() {
		// Title bar
		const titleBarOptions = {
		  title: 'Privacy Policy',
		  buttons: {
		    secondary: [groupButton]
		  },
		};
		const myTitleBar = TitleBar.create(app, titleBarOptions);
	},

	auto_smart: function() {

		// Init CSFF Token
		$.ajaxSetup({
		    beforeSend: function(xhr, settings) {
		        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
		            xhr.setRequestHeader("X-CSRFToken", csrf_token);
		        }
		    }
		});

		// Init menu
		const save = Button.create(app, {label: 'Save'});
		const saveCollection = save.subscribe(Button.Action.CLICK, data => {
		var formData = {};
		$.each($('form').serializeArray(), function() {
		    formData[this.name] = this.value;
		});

		// Clean up obj names and add to rules array
		let count = 1;
		let tempRule = {};
		for(let ruleData of Object.keys(formData)) {
			for(let formRuleType of Object.keys(formObj['rules'])) {
				if(ruleData.includes(formRuleType)) {
					let newObjName = ruleData.split('Id')[1];
					tempRule[newObjName] = formData[ruleData];
					if(count % 6 == 0 && count != 0) {
						formObj['rules'][formRuleType].push(tempRule);
						tempRule = {};
					}
					count++;
					break
				};
			};
		};


		$.ajax({
			  url: 'https://shopify-stock-app.herokuapp.com/post-auto-smart',
			  type: 'POST',
			  contentType: "application/json",
			  data: JSON.stringify(formObj),
			  success: function(result) {
				console.log(result);
				}
			})
		});

		const titleBarOptions = {
		  title: 'Collection',
		  buttons: {
		  	primary: save,
		    secondary: [groupButton]
		  },
		};

		const myTitleBar = TitleBar.create(app, titleBarOptions);


		$('.dropdown-toggle').dropdown();

		// Init rules
		document.querySelectorAll('.automation__add:not(.disbaled)').forEach(function(el) {
			el.addEventListener('click', function() {
				let rule = el.getAttribute('data-rule');
				let limit = el.getAttribute('data-rule-limit');
				let ruleToAdd = rules[rule];
				let ruleInputLine = document.querySelector('.rule-input');
				let currentRulesLength = document.querySelectorAll(`[data-rule-block="${rule}"]`).length
				let jumbotron = document.querySelector('.jumbotron');

				// Update IDs
				let replaceId = new RegExp(rule + 'Id', 'g');
				ruleToAdd = ruleToAdd.replace(replaceId, `${rule}${currentRulesLength}Id`);

				if(limit <= currentRulesLength + 1) {
					el.classList.add('disabled');
				} else {
					el.classList.remove('disabled');
				};
				ruleInputLine.insertAdjacentHTML('beforeend', ruleToAdd);
				jumbotron.classList.add('d-none');
			});
		});
	},

	index: function() {
		// Collection selector
		const collectionPicker = ResourcePicker.create(app, {
		  resourceType: ResourcePicker.ResourceType.Collection,
		  options: {
		    selectMultiple: false,
		  },
		});
		const collectionButton = Button.create(app, {label: 'Collections'});
		const viewCollections = collectionButton.subscribe(Button.Action.CLICK, data => {
		  collectionPicker.dispatch(ResourcePicker.Action.OPEN);
		});

		// Redirects
		$('#instructions-alert-redirect').on('click', function() {
		  redirect.dispatch(Redirect.Action.APP, '/instructions');
		})

		// Instructions close 
		var instructionsState = sessionStorage.getItem("instructions-alert") ? 'none' : 'block'
		$('#instructions-alert').css('display', instructionsState)

		$('#instructions-alert-close').on('click', function() {
		  sessionStorage.setItem('instructions-alert', 'close')
		  $('#instructions-alert').css('display', 'none')
		})

		collectionPicker.subscribe(ResourcePicker.Action.SELECT, ({selection}) => {
		  var idArray = selection[0].id.split('/')
		  var id = idArray[idArray.length - 1]
		  $('#collection-name').text(selection[0].title);
		  $('#collection-description').html(selection[0].description.substring(0, 300));
		  if(selection[0].image) { 
		    $('#collection-image').attr('src', selection[0].image.originalSrc) 
		  } else {
		  	var placeholder = $('#collection-image').attr('data-placeholder');
		    $('#collection-image').attr('src', placeholder) 
		  }
		  if(selection[0].sortOrder != "MANUAL") {
		    $('#manual-update').css('display', 'block');
		    $('#collection-link').attr('data-collection', id).addClass('disabled').css('display', 'none');
		    $('#collection-admin-link').attr('href', `https://{{shop}}/admin/collections/${id}`);
		  } else {
		    $('#manual-update').css('display', 'none');
		    $('#collection-link').attr('data-collection', id).removeClass('disabled').css('display', 'block');
		  }
		});

		$('#collection-link').on('click', function() {
		  if(!$(this).hasClass('disabled')) {
		    redirect.dispatch(Redirect.Action.APP, '/collection-new/' + $(this).data('collection'));
		  }
		})

		// Title bar
		const titleBarOptions = {
		  title: 'Home',
		  buttons: {
		    primary: collectionButton, 
		    secondary: [groupButton]
		  },
		};
		const myTitleBar = TitleBar.create(app, titleBarOptions);
	}
}

utils = {
	// https://stackoverflow.com/questions/6497552/number-of-days-between-two-dates-in-iso8601-date-format
	daysBetween(date1String, date2String) {
	  var d1 = new Date(date1String);
	  var d2 = new Date(date2String);
	  var daysDiff = (d2-d1)/(1000*3600*24);
	  daysDiff = daysDiff <= 0 ? 0 : daysDiff;
	  return daysDiff;
	},

	setCookie(name,value,days) {
	    var expires = "";
	    if (days) {
	        var date = new Date();
	        date.setTime(date.getTime() + (days*24*60*60*1000));
	        expires = "; expires=" + date.toUTCString();
	    }
	    document.cookie = name + "=" + (value || "")  + expires + "; cross-site-cookie=bar; SameSite=None; Secure";
	},

	getCookie(name) {
	    var nameEQ = name + "=";
	    var ca = document.cookie.split(';');
	    for(var i=0;i < ca.length;i++) {
	        var c = ca[i];
	        while (c.charAt(0)==' ') c = c.substring(1,c.length);
	        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	    }
	    return null;
	}
}

document.addEventListener("DOMContentLoaded", function(){
    scripts.init();
});