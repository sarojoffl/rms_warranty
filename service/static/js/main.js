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

  // Limit intake machines to assets owned by the selected client. The form
  // still validates this on the server, so a manually altered request is safe.
  var clientSelect = document.getElementById('id_client') || document.getElementById('id_sold_to');
  var machineSelect = document.getElementById('id_machine');
  var machineSelectWrap = document.querySelector('.machine-select');
  if (clientSelect && machineSelect && machineSelectWrap) {
    var optionsUrl = machineSelectWrap.dataset.machineOptionsUrl;
    var selectedMachine = machineSelect.value;

    function setMachinePlaceholder(text, disabled) {
      machineSelect.replaceChildren(new Option(text, ''));
      machineSelect.disabled = disabled;
    }

    function loadClientMachines() {
      var clientId = clientSelect.value;
      if (!clientId) {
        setMachinePlaceholder('Select a client first', true);
        return;
      }

      machineSelect.disabled = true;
      setMachinePlaceholder('Loading machines…', true);
      fetch(optionsUrl + '?client_id=' + encodeURIComponent(clientId), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (response) {
          if (!response.ok) throw new Error('Could not load machines');
          return response.json();
        })
        .then(function (data) {
          machineSelect.replaceChildren(new Option('Select a machine', ''));
          data.machines.forEach(function (machine) {
            machineSelect.add(new Option(machine.label, machine.id, false, String(machine.id) === String(selectedMachine)));
          });
          machineSelect.disabled = false;
          selectedMachine = '';
        })
        .catch(function () {
          setMachinePlaceholder('Unable to load machines — try again', true);
        });
    }

    clientSelect.addEventListener('change', function () {
      selectedMachine = '';
      loadClientMachines();
    });
    loadClientMachines();
  }
});
