function category_changed() {
	if ($('#category').val() == 'Create a new category ...') {
	    $('#new-category').show();
	} else {
	    $('#new-category').hide();
	}
}