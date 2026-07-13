document.addEventListener('DOMContentLoaded', function () {
  var hamburger = document.getElementById('hamburger');
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
  }

  if (hamburger && sidebar && overlay) {
    hamburger.addEventListener('click', function () {
      sidebar.classList.add('open');
      overlay.classList.add('open');
    });
    overlay.addEventListener('click', closeSidebar);
  }

  document.querySelectorAll('.notice-close').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.closest('.notice').remove();
    });
  });

  // Conditional field reveals on entry/exit forms
  var claimable = document.getElementById('id_claimable');
  var claimReport = document.getElementById('field-report_warranty_claimed');
  function toggleClaimReport() {
    if (!claimable || !claimReport) return;
    claimReport.style.display = claimable.value === 'yes' ? '' : 'none';
  }
  if (claimable) {
    claimable.addEventListener('change', toggleClaimReport);
    toggleClaimReport();
  }

  var solved = document.getElementById('id_solved');
  var causeField = document.getElementById('field-not_solved_cause');
  function toggleCause() {
    if (!solved || !causeField) return;
    causeField.style.display = solved.value === 'not_solved' ? '' : 'none';
  }
  if (solved) {
    solved.addEventListener('change', toggleCause);
    toggleCause();
  }
});
