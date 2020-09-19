rules = {
	outOfStockRule : `
    	<!-- OOS -->
    	<div data-rule-block="outOfStockRule" class="card text-center mt-3">
    	  <div class="automations__card-header card-header">
    	    <ul class="nav nav-pills card-header-pills">
    	    	<li class="nav-item">
    	    		<p class="text-muted small text-left mb-0">Automation</p>
    	    	  <h4 class="text-left mb-0">Out of Stock</h4>
    	    	  <p class="card-text text-muted">For hiding products without stock.</p>
    	    	</li>
    	    	<li class="ml-auto d-flex align-items-center">
    				<a class="mr-4" type="button" data-toggle="collapse" data-target="#outOfStockIdCollapse" aria-expanded="false" aria-controls="outOfStockIdCollapse">
    				    <span class="mb-0">Edit</span> <i class="fa fa-pencil edit-icon" aria-hidden="true"></i>
    				  </a>
    				<a class="mr-4" type="button" onClick="rulesUtils.removeRule(this)">
    					 <span class="mb-0">Delete</span> <i class="fa fa-trash-o" aria-hidden="true"></i>
    				</a>
    	    	</li>
    	    </ul>
    	  </div>
    	  <div class="collapse" id="outOfStockIdCollapse">
    	  	<div class="p-3">
    	  		<p class="text-muted text-left mb-1">Rule:</p>
    	  		<h5 class="card-title">Send products with inventory <strong>below or equal to 0</strong> to the <strong>bottom</strong> of their collections
    	  		<select read-only class="d-none form-control inline-input-medium" name="outOfStockIdCompare" id="outOfStockIdCompare">
    	  		  <option value="<">Below</option>
    	  		  <option selected value="<=">Below or equal to</option>
    	  		  <option value="==">Exactly</option>
    	  		  <option value=">=">Above or equal to</option>
    	  		  <option value=">">Above</option>
    	  		</select> 
    	  		<input read-only type="number" value="0" class="d-none form-inline inline-input form-control" name="outOfStockIdInput" id="outOfStockIdInput">
    	  		<select read-only class="d-none form-control inline-input-medium" name="outOfStockIdSelect" id="outOfStockIdSelect">
    	  		  <option value="bottom" selected>Bottom</option>
    	  		  <option value="top">Top</option>
    	  		</select></h5>
    		  </div>
    		  <div class="p-3">
    	  		<p class="text-muted text-left mb-1">Exclude/Include Collections (Max 25):</p>
    	  		<div class="automations__exclude-container">
    			    <h5>
    				   <select class="form-control inline-input-medium" name="outOfStockIdExcludeInclude" id="outOfStockIdExcludeInclude">
    			      <option value="exclude">Do not</option>
    			      <option value="include">Only</option>
    			    </select> 
    		     	sort these collections: <span class="exclude-line"></span><span class="badge badge-secondary exclude-add" onClick="rulesUtils.excludeCollection(this)">Add Collections +</span></h5>
    			    <input name="outOfStockIdCollections" class="d-none exclude-input" type="text">
    			    <input name="outOfStockIdHandles" class="d-none exclude-handle-input" type="text">
    		  	</div>
    		  </div>
    	  </div>
    	</div>
	`,
	customInventoryRule: `
		<!-- Inventory -->
			<div data-rule-block="customInventoryRule" class="card text-center mt-3">
			  <div class="automations__card-header card-header">
			    <ul class="nav nav-pills card-header-pills">
			    	<li class="nav-item">
			    		<p class="text-muted small text-left mb-0">Automation</p>
			    	  <h4 class="text-left mb-0">Custom Inventory Level</h4>
			    	  <p class="card-text text-muted">For hiding/promoting products with low/high stock.</p>
			    	</li>
			    	<li class="ml-auto d-flex align-items-center">
		    				<a class="mr-4" type="button" data-toggle="collapse" data-target="#customInventoryRuleIdCollapse" aria-expanded="false" aria-controls="customInventoryRuleIdCollapse">
		    				    <span class="mb-0">Edit</span> <i class="fa fa-pencil edit-icon" aria-hidden="true"></i>
		    				  </a>
		    				<a class="mr-4" type="button" onClick="rulesUtils.removeRule(this)">
		    					   <span class="mb-0">Delete</span> <i class="fa fa-trash-o" aria-hidden="true"></i>
		    					 </a>
			    	</li>
			    </ul>
			  </div>
			  <div class="collapse" id="customInventoryRuleIdCollapse">
			  	<div class="p-3">
			  		<p class="text-muted text-left mb-1">Rule:</p>
				    <h5 class="card-title">Send products with inventory
				    <select class="form-control inline-input-medium" name="customInventoryRuleIdCompare" id="customInventoryRuleIdCompare">
				      <option value="<">Below</option>
				      <option value="<=">Below or equal to</option>
				      <option value="==">Exactly</option>
				      <option value=">=">Above or equal to</option>
				      <option value=">">Above</option>
				    </select> 
				    <input type="number" value="10" class="form-inline inline-input form-control" name="customInventoryRuleIdInput" id="customInventoryRuleIdInput"> to the 
				    <select class="form-control inline-input-medium" name="customInventoryRuleIdSelect" id="customInventoryRuleIdSelect">
				      <option value="bottom" selected>Bottom</option>
				      <option value="top">Top</option>
				    </select> of their collections</h5>
				  </div>
				  <div class="p-3">
			  		<p class="text-muted text-left mb-1">Exclude/Include Collections (Max 25):</p>
			  		<div class="automations__exclude-container">
					    <h5>
						   <select class="form-control inline-input-medium" name="customInventoryRuleIdExcludeInclude" id="customInventoryRuleIdExcludeInclude">
					      <option value="exclude">Do not</option>
					      <option value="include">Only</option>
					    </select> 
				     	sort these collections: <span class="exclude-line"></span><span class="badge badge-secondary exclude-add" onClick="rulesUtils.excludeCollection(this)">Add Collections +</span></h5>
					    <input name="customInventoryRuleIdCollections" class="d-none exclude-input" type="text">
					    <input name="customInventoryRuleIdHandles" class="d-none exclude-handle-input" type="text">
				  	</div>
				  </div>
			  </div>
			</div>
    `,
    createdDateRule: `
    	<!-- Date -->
			<div data-rule-block="createdDateRule" class="card text-center mt-3">
			  <div class="automations__card-header card-header">
			    <ul class="nav nav-pills card-header-pills">
			    	<li class="nav-item">
			    		<p class="text-muted small text-left mb-0">Automation</p>
			    		<h4 class="text-left mb-0">Created Date</h4>
			    		<p class="card-text text-muted">For promoting new products/hiding old products.</p>
			    	</li>
			    	<li class="ml-auto d-flex align-items-center">
		    				<a class="mr-4" type="button" data-toggle="collapse" data-target="#createdDateRuleIdCollapse" aria-expanded="false" aria-controls="createdDateRuleIdCollapse">
		    				    <span class="mb-0">Edit</span> <i class="fa fa-pencil edit-icon" aria-hidden="true"></i>
		    				  </a>
		    				<a class="mr-4" type="button" onClick="rulesUtils.removeRule(this)">
		    					   <span class="mb-0">Delete</span> <i class="fa fa-trash-o" aria-hidden="true"></i>
		    					 </a>
			    	</li>
			    </ul>
			  </div>
			  <div class="collapse" id="createdDateRuleIdCollapse">
			  	<div class="form-group p-3">
			  		<p class="text-muted text-left mb-0">Rule:</p>
				    <h5 class="card-title">Send products created
				    <select class="form-control inline-input-medium" name="createdDateRuleIdCompare" id="createdDateRuleIdCompare">
				      <option selected value="<">Less than</option>
				      <option value="<=">Less than or exactly</option>
				      <option value=">=">More than or exactly</option>
				      <option value=">">More than</option>
				    </select> 
				    <input type="number" min="0" value="1" class="form-inline inline-input form-control" name="createdDateRuleIdInput" id="createdDateRuleIdInput"> day(s) ago to the 
				    <select class="form-control inline-input-medium" name="createdDateRuleIdSelect" id="createdDateRuleIdSelect">
				      <option value="bottom">Bottom</option>
				      <option value="top" selected>Top</option>
				    </select> of their collections</h5>
				  </div>

				  <div class="p-3">
			  		<p class="text-muted text-left mb-1">Exclude/Include Collections (Max 25):</p>
			  		<div class="automations__exclude-container">
					    <h5>
						   <select class="form-control inline-input-medium" name="createdDateRuleIdExcludeInclude" id="createdDateRuleIdExcludeInclude">
					      <option value="exclude">Do not</option>
					      <option value="include">Only</option>
					    </select> 
				     	sort these collections: <span class="exclude-line"></span><span class="badge badge-secondary exclude-add" onClick="rulesUtils.excludeCollection(this)">Add Collections +</span></h5>
					    <input name="createdDateRuleIdCollections" class="d-none exclude-input" type="text">
					    <input name="createdDateRuleIdHandles" class="d-none exclude-handle-input" type="text">
				  	</div>
				  </div>
			  </div>
			</div>
    `
}

rulesUtils = {
	removeRule: function(el) {
    	el.closest('.card').remove();
    },

    removeExclude(el) {
    	let removeChip = el.closest('.badge');
    	let excludeContainer = el.closest('.automations__exclude-container');
    	let exlcudeIdInput = excludeContainer.querySelector('.exclude-input');
    	let exlcudeHandleInput = excludeContainer.querySelector('.exclude-handle-input');
    	let removeId = removeChip.getAttribute('data-exclude-id');
    	let removeHandle = removeChip.getAttribute('data-exclude-handle');

    	// Remove from id input
 	   	let excludeInputValue = exlcudeIdInput.value;
    	excludeInputValue = excludeInputValue.replace(',' + removeId, '').replace(removeId + ',', '').replace(removeId, '');
    	exlcudeIdInput.value = excludeInputValue;

    	// Remove from handle input (extra checks as commas are used on either side)
    	let exlcudeHandleValue = exlcudeHandleInput.value;
    	exlcudeHandleValue = exlcudeHandleValue.replace(',' + removeHandle + ',', ',');
    	exlcudeHandleValue = exlcudeHandleValue == ',' ? '' : exlcudeHandleValue;
    	exlcudeHandleInput.value = exlcudeHandleValue;

    	// Remove from chips
    	removeChip.remove();
    	save.set({disabled: false});
    },

    excludeCollection(el) {
    	// Open the collection picker
    	let excludeContainer = el.closest('.automations__exclude-container');
    	let exlcudeInput = excludeContainer.querySelector('.exclude-input');
    	let excludeHandleInput = excludeContainer.querySelector('.exclude-handle-input');
    	let excludeLine = excludeContainer.querySelector('.exclude-line');


    	const selectUnsubscribe = rulesCollectionPicker.subscribe(ResourcePicker.Action.SELECT, ({selection}) => {
    	  selection.forEach(function(select) {
    	  	let excludeLength = excludeContainer.querySelectorAll('.exclude-badge') ? excludeContainer.querySelectorAll('.exclude-badge').length : 0;
    	  	// Add to id input
    	  	if(excludeLength + 1 > 25) {
							// TODO: Max limit error message
    	  	} else {
    	  		if(!exlcudeInput.value.includes(select.id)) {
    	  			exlcudeInput.value = exlcudeInput.value == '' ? select.id : exlcudeInput.value + ',' + select.id;
    	  			// Handle input uses commas either side
    	  			excludeHandleInput.value =  excludeHandleInput.value == '' ? ',' + select.handle + ',' : excludeHandleInput.value + select.handle + ',';
    	  		}
    	  		// Add to chips
    	  		if(!document.querySelector(`.automations__exclude-container [data-exclude-id="${select.id}"]`)) {
    	  			excludeLine.insertAdjacentHTML('afterend', `<span data-exclude-id="${select.id}" data-exclude-handle="${select.handle}" class="exclude-badge badge badge-secondary">${select.handle} <span class="exclude-delete-icon" onClick="rulesUtils.removeExclude(this)">x</span></span>`);
    	  		}
    	  	}
    	  	

    	  });
    	});
    	rulesCollectionPicker.dispatch(ResourcePicker.Action.OPEN);
    }

}