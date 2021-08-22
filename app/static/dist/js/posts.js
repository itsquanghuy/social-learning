const posts = new Vue({
	el: "#posts",
	data: {
		posts: [],
		page: 1,
	},
	methods: {
		getPosts: function() {
			axios.get(`/get_posts?page=${this.page}`).then(({ data }) => {
				this.posts = [...this.posts, ...data];
				this.page++;
			});
		},
		refresh: function() {
			this.page = 1;
			axios.get(`/get_posts?page=${this.page}`).then(({ data }) => {
				this.posts = [...data];
				this.page++;
			});
		}
	},
	mounted: function() {
		const self = this;

		this.getPosts();
		$("#posts-container").on("scroll", function() {
            if ($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight) 
                self.getPosts();
        });
	}
});