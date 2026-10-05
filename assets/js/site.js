(function () {
  var parts = ['ozonwoyechima', 'gmail.com'];
  document.querySelectorAll('.mail').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      window.location.href = 'mail' + 'to:' + parts[0] + '@' + parts[1];
    });
  });
  var btn = document.querySelector('.menu-btn');
  var drawer = document.getElementById('drawer');
  btn.addEventListener('click', function () {
    var open = drawer.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  drawer.addEventListener('click', function (e) {
    if (e.target.closest('a')) {
      drawer.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
    }
  });
  var q = document.getElementById('q');
  if (q) {
    var rows = document.querySelectorAll('.posts .post');
    var none = document.getElementById('no-results');
    q.value = '';
    q.addEventListener('input', function () {
      var term = q.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (row) {
        var match = !term || row.getAttribute('data-title').indexOf(term) !== -1 || row.getAttribute('data-content').indexOf(term) !== -1;
        row.style.display = match ? '' : 'none';
        if (match) shown++;
      });
      none.hidden = shown !== 0;
    });
  }
})();
