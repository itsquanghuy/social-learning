const shareBtn = $("#share-knowledge-btn");
const cancelBtn = $("#cancel-knowledge-btn");
const shareForm = $("#share-form");

function displayShare() {
	shareBtn.addClass("hidden");
	shareForm.removeClass("hidden");
	shareForm.addClass("block");
}

function closeShare() {
	shareForm.removeClass("block");
	shareForm.addClass("hidden")
	shareBtn.removeClass("hidden");
}

shareBtn.click(displayShare);
cancelBtn.click(closeShare);

shareForm.submit(function(evt) {
	const fd = new FormData();

	$(this).serializeArray().forEach((obj, index) => (index !== 2 && fd.append(obj.name, obj.value)));
	fd.append("content", CKEDITOR.instances["content"].getData());

	$.ajax({
		url: "/create_post",
		data: fd,
		cache: false,
		processData: false,
		contentType: false,
		type: "POST",
		success: function(data) {
			shareForm.trigger("reset");
			CKEDITOR.instances["content"].setData("");
			closeShare();
			posts.refresh();
		}
	});

	evt.preventDefault();
});