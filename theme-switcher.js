(function() {
    var saved = localStorage.getItem('theme') || 'original';
    document.documentElement.setAttribute('data-theme', saved);

    document.addEventListener('DOMContentLoaded', function() {
        var div = document.createElement('div');
        div.className = 'theme-switcher';
        div.innerHTML =
            '<select id="theme-select" aria-label="Choose theme">' +
            '<option value="original">Original</option>' +
            '<option value="midnight-ocean">Midnight Ocean</option>' +
            '<option value="charcoal-ember">Charcoal Ember</option>' +
            '<option value="nordic-frost">Nordic Frost</option>' +
            '<option value="obsidian-neon">Obsidian Neon</option>' +
            '<option value="warm-earth">Warm Earth</option>' +
            '</select>';
        document.body.appendChild(div);

        var select = document.getElementById('theme-select');
        select.value = saved;
        select.addEventListener('change', function() {
            document.documentElement.setAttribute('data-theme', this.value);
            localStorage.setItem('theme', this.value);
        });
    });
})();
