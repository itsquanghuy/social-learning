new Vue({
    el: "#user-dropdown",
    data: {
        opened: false
    },
    methods: {
        toggleDropdown: function() {
            this.opened = !this.opened;
        }
    }
});