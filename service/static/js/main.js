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
  var selectedMachine = machineSelect ? machineSelect.value : '';

  function setMachinePlaceholder(text, disabled) {
    if (!machineSelect) return;
    machineSelect.replaceChildren(new Option(text, ''));
    machineSelect.disabled = disabled;
  }

  function loadClientMachines() {
    if (!clientSelect || !machineSelect || !machineSelectWrap) return;
    var clientId = clientSelect.value;
    var optionsUrl = machineSelectWrap.dataset.machineOptionsUrl;
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
        // Sync searchable combobox text input
        machineSelect.dispatchEvent(new Event('change'));
      })
      .catch(function () {
        setMachinePlaceholder('Unable to load machines — try again', true);
      });
  }

  if (clientSelect && machineSelect && machineSelectWrap) {
    clientSelect.addEventListener('change', function () {
      selectedMachine = '';
      loadClientMachines();
    });
    loadClientMachines();
  }

  // Modal logic for Quick Add
  var modal = document.getElementById('quick-add-modal');
  var modalTitle = document.getElementById('modal-title');
  var modalBody = document.getElementById('modal-body-content');
  var modalCloseBtn = document.getElementById('modal-close-btn');

  if (modal && modalBody) {
    function openModal(title, url, targetSelectSelector, clientId) {
      modalTitle.textContent = title;
      modalBody.innerHTML = '<div class="loading-spinner">Loading form…</div>';
      modal.style.display = 'flex';

      var fetchUrl = url;
      if (clientId) {
        fetchUrl += (url.includes('?') ? '&' : '?') + 'client_id=' + encodeURIComponent(clientId);
      }

      fetch(fetchUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (response) {
          if (!response.ok) throw new Error('Could not load form');
          return response.json();
        })
        .then(function (data) {
          if (data.status === 'success' || data.html) {
            modalBody.innerHTML = data.html;
            bindModalFormSubmit(url, targetSelectSelector);
          } else {
            modalBody.innerHTML = '<div class="notice error">Failed to load form content.</div>';
          }
        })
        .catch(function (error) {
          modalBody.innerHTML = '<div class="notice error">Error loading form. Please try again.</div>';
        });
    }

    function closeModal() {
      modal.style.display = 'none';
      modalBody.innerHTML = '';
    }

    if (modalCloseBtn) {
      modalCloseBtn.addEventListener('click', closeModal);
    }

    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        closeModal();
      }
    });

    function bindModalFormSubmit(actionUrl, targetSelectSelector) {
      var form = modalBody.querySelector('form');
      if (!form) return;

      var closeBtn = form.querySelector('.modal-close-btn');
      if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
      }

      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var formData = new FormData(form);

        fetch(actionUrl, {
          method: 'POST',
          body: formData,
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
          .then(function (response) {
            if (!response.ok) throw new Error('Server error');
            return response.json();
          })
          .then(function (data) {
            if (data.status === 'success') {
              var select = document.querySelector(targetSelectSelector);
              if (select) {
                if (targetSelectSelector === '#id_client' || targetSelectSelector === '#id_sold_to') {
                  var exists = Array.from(select.options).some(function (opt) {
                    return String(opt.value) === String(data.id);
                  });
                  if (!exists) {
                    var newOpt = new Option(data.name, data.id, true, true);
                    select.add(newOpt);
                  } else {
                    select.value = data.id;
                  }
                  select.dispatchEvent(new Event('change'));
                } else if (targetSelectSelector === '#id_machine') {
                  selectedMachine = data.id;
                  loadClientMachines();
                }
              }
              closeModal();
            } else if (data.status === 'error') {
              modalBody.innerHTML = data.html;
              bindModalFormSubmit(actionUrl, targetSelectSelector);
            }
          })
          .catch(function (error) {
            alert('An error occurred. Please try again.');
          });
      });
    }

    document.querySelectorAll('.quick-add-link').forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        var url = link.getAttribute('href');
        var title = link.getAttribute('data-modal-title') || 'Quick Add';
        var targetSelectSelector = link.getAttribute('data-target-select');
        var needsClient = link.getAttribute('data-needs-client') === 'true';

        var clientId = null;
        if (needsClient) {
          var clientSelectEl = document.getElementById('id_client') || document.getElementById('id_sold_to');
          if (clientSelectEl) {
            clientId = clientSelectEl.value;
          }
          if (!clientId) {
            alert('Please select a client first before adding a machine.');
            return;
          }
        }

        openModal(title, url, targetSelectSelector, clientId);
      });
    });
  }

  // Helper to convert any standard select to a premium searchable select
  function makeSelectSearchable(selectId) {
    var select = document.getElementById(selectId);
    if (!select) return;

    // Create wrapper
    var wrap = document.createElement('div');
    wrap.className = 'combobox-wrap';
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(select);

    // Hide original select
    select.style.display = 'none';

    // Create search input
    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'combobox-input';
    input.placeholder = 'Type to search...';
    input.autocomplete = 'off';
    wrap.appendChild(input);

    // Create dropdown container
    var dropdown = document.createElement('div');
    dropdown.className = 'combobox-dropdown';
    wrap.appendChild(dropdown);

    // Sync disabled state from original select to combobox input
    function syncDisabledState() {
      input.disabled = select.disabled;
      if (select.disabled) {
        // Show placeholder option text in combobox input
        var placeholderOpt = select.options[0];
        input.value = placeholderOpt ? placeholderOpt.text : '';
        input.style.opacity = '0.55';
        input.style.cursor = 'not-allowed';
        dropdown.style.display = 'none';
      } else {
        input.style.opacity = '';
        input.style.cursor = '';
      }
    }

    // Helper to refresh dropdown options
    function refreshDropdown() {
      if (select.disabled) return;
      var filter = input.value.toLowerCase();
      dropdown.innerHTML = '';
      var matchedCount = 0;

      Array.from(select.options).forEach(function(opt) {
        if (!opt.value) return; // skip empty option placeholder
        var label = opt.text;
        if (label.toLowerCase().includes(filter)) {
          var item = document.createElement('div');
          item.className = 'combobox-item';
          item.textContent = label;
          item.dataset.value = opt.value;
          if (String(select.value) === String(opt.value)) {
            item.classList.add('selected');
          }
          item.addEventListener('mousedown', function(e) {
            e.preventDefault(); // prevent input blur before click registers
            select.value = opt.value;
            input.value = label;
            dropdown.style.display = 'none';
            select.dispatchEvent(new Event('change'));
          });
          dropdown.appendChild(item);
          matchedCount++;
        }
      });

      if (matchedCount === 0) {
        var noResults = document.createElement('div');
        noResults.className = 'combobox-item no-results';
        noResults.textContent = filter ? 'No matching items found' : 'No options available';
        dropdown.appendChild(noResults);
      }
    }

    // Set initial input value
    function syncInputValue() {
      var selected = select.options[select.selectedIndex];
      if (selected && selected.value) {
        input.value = selected.text;
      } else {
        input.value = '';
      }
    }

    syncInputValue();
    syncDisabledState();

    // Event listeners
    input.addEventListener('focus', function() {
      if (select.disabled) return;
      document.querySelectorAll('.combobox-dropdown').forEach(function(d) {
        d.style.display = 'none';
      });
      input.value = ''; // Clear to allow fresh searching
      refreshDropdown();
      dropdown.style.display = 'block';
    });

    input.addEventListener('input', function() {
      refreshDropdown();
    });

    input.addEventListener('blur', function() {
      // Slight delay so mousedown on item fires first
      setTimeout(function() {
        dropdown.style.display = 'none';
        syncInputValue(); // Restore displayed text to selected value
      }, 150);
    });

    // Close when clicking outside
    document.addEventListener('click', function(e) {
      if (!wrap.contains(e.target)) {
        dropdown.style.display = 'none';
        syncInputValue();
      }
    });

    // Re-sync when original select changes programmatically (e.g. machine options load)
    select.addEventListener('change', function() {
      syncDisabledState();
      syncInputValue();
    });

    // Watch for disabled attribute changes via MutationObserver
    var observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(m) {
        if (m.attributeName === 'disabled') {
          syncDisabledState();
          syncInputValue();
        }
      });
    });
    observer.observe(select, { attributes: true });
  }

  // Initialize Searchable selects on intake forms
  makeSelectSearchable('id_client');
  makeSelectSearchable('id_sold_to');
  makeSelectSearchable('id_machine');
});
