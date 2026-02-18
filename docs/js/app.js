/**
 * SPA router and view controller for the Invoice Generator web app.
 * Hash-based routing with views rendered into #main-content.
 */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let pyReady = false;
let currentInvoiceHTML = '';
let currentTimesheetHTML = '';

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

function addDays(dateStr, days) {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

function generateInvoiceNumber() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const rand = String(Math.floor(Math.random() * 900) + 100);
  return `INV-${y}${m}-${rand}`;
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

const routes = {
  '': renderDashboard,
  '#dashboard': renderDashboard,
  '#clients': renderClients,
  '#clients/new': renderClientForm,
  '#invoices': renderInvoices,
  '#invoices/new': renderInvoiceForm,
  '#timesheets': renderTimesheets,
  '#timesheets/new': renderTimesheetForm,
  '#settings': renderSettings,
};

function navigate(hash) {
  window.location.hash = hash;
}

function router() {
  const hash = window.location.hash;

  // Match client edit route: #clients/123
  const clientEdit = hash.match(/^#clients\/(\d+)$/);
  if (clientEdit) {
    renderClientForm(Number(clientEdit[1]));
    updateActiveNav(hash);
    return;
  }

  const handler = routes[hash] || routes[''];
  handler();
  updateActiveNav(hash);
}

function updateActiveNav(hash) {
  $$('.nav-item').forEach((el) => {
    const href = el.getAttribute('data-route');
    el.classList.toggle('active', hash.startsWith(href) && href !== '');
    if (href === '' || href === '#dashboard') {
      el.classList.toggle('active', hash === '' || hash === '#dashboard');
    }
  });
}

// ---------------------------------------------------------------------------
// View: Dashboard
// ---------------------------------------------------------------------------

async function renderDashboard() {
  const [clientList, invoiceList, tsList] = await Promise.all([
    db.clients.getAll(),
    db.invoices.getAll(),
    db.timesheets.getAll(),
  ]);

  const recentInvoices = invoiceList
    .sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
    .slice(0, 5);

  const main = $('#main-content');
  main.innerHTML = `
    <div class="view-header">
      <h2>Dashboard</h2>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">${clientList.length}</div>
        <div class="stat-label">Clients</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${invoiceList.length}</div>
        <div class="stat-label">Invoices</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${tsList.length}</div>
        <div class="stat-label">Timesheets</div>
      </div>
    </div>

    <div class="quick-actions">
      <button class="btn btn-primary" onclick="navigate('#invoices/new')">New Invoice</button>
      <button class="btn btn-secondary" onclick="navigate('#timesheets/new')">New Timesheet</button>
      <button class="btn btn-secondary" onclick="navigate('#clients/new')">Add Client</button>
    </div>

    ${recentInvoices.length > 0 ? `
    <div class="section-card">
      <h3>Recent Invoices</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Invoice #</th>
            <th>Client</th>
            <th>Date</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          ${recentInvoices.map((inv) => `
          <tr>
            <td>${escapeHTML(inv.invoice_number)}</td>
            <td>${escapeHTML(inv.customer_name)}</td>
            <td>${escapeHTML(inv.invoice_date)}</td>
            <td>${escapeHTML(inv.currency_symbol || '')} ${escapeHTML(inv.total || '')}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>` : `
    <div class="empty-state">
      <p>No invoices yet. Create your first invoice to get started.</p>
    </div>`}
  `;
}

// ---------------------------------------------------------------------------
// View: Clients
// ---------------------------------------------------------------------------

async function renderClients() {
  const clientList = await db.clients.getAll();

  const main = $('#main-content');
  main.innerHTML = `
    <div class="view-header">
      <h2>Clients</h2>
      <button class="btn btn-primary" onclick="navigate('#clients/new')">Add Client</button>
    </div>

    ${clientList.length > 0 ? `
    <table class="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Company</th>
          <th>Email</th>
          <th>Currency</th>
          <th>Daily Rate</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        ${clientList.map((c) => `
        <tr>
          <td>${escapeHTML(c.name)}</td>
          <td>${escapeHTML(c.company)}</td>
          <td>${escapeHTML(c.email)}</td>
          <td>${escapeHTML(c.currency || 'EUR')}</td>
          <td>${escapeHTML(c.currency_symbol || '\u20ac')} ${c.daily_rate || '0.00'}</td>
          <td class="action-cell">
            <button class="btn btn-sm" onclick="navigate('#clients/${c.id}')">Edit</button>
            <button class="btn btn-sm btn-danger" data-delete-client="${c.id}">Delete</button>
          </td>
        </tr>`).join('')}
      </tbody>
    </table>` : `
    <div class="empty-state">
      <p>No clients configured. Add your first client to get started.</p>
    </div>`}
  `;

  // Delete handlers
  main.querySelectorAll('[data-delete-client]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      const id = Number(e.target.getAttribute('data-delete-client'));
      if (confirm('Delete this client?')) {
        await db.clients.delete(id);
        showToast('Client deleted');
        renderClients();
      }
    });
  });
}

// ---------------------------------------------------------------------------
// View: Client Form
// ---------------------------------------------------------------------------

async function renderClientForm(editId) {
  let client = {
    name: '',
    company: '',
    contact: '',
    email: '',
    address: [],
    currency: 'EUR',
    currency_symbol: '\u20ac',
    daily_rate: 0,
    payment_terms_days: 30,
    payment_details: {},
  };

  if (editId) {
    const existing = await db.clients.get(editId);
    if (existing) client = existing;
  }

  const main = $('#main-content');
  main.innerHTML = `
    <div class="view-header">
      <h2>${editId ? 'Edit' : 'New'} Client</h2>
    </div>

    <form id="client-form" class="form-grid">
      <div class="form-group">
        <label>Name *</label>
        <input type="text" name="name" value="${escapeHTML(client.name)}" required>
      </div>
      <div class="form-group">
        <label>Company *</label>
        <input type="text" name="company" value="${escapeHTML(client.company)}" required>
      </div>
      <div class="form-group">
        <label>Contact Person</label>
        <input type="text" name="contact" value="${escapeHTML(client.contact)}">
      </div>
      <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" value="${escapeHTML(client.email)}">
      </div>
      <div class="form-group full-width">
        <label>Address (one line per row)</label>
        <textarea name="address" rows="3">${escapeHTML((client.address || []).join('\n'))}</textarea>
      </div>
      <div class="form-group">
        <label>Currency Code</label>
        <input type="text" name="currency" value="${escapeHTML(client.currency || 'EUR')}">
      </div>
      <div class="form-group">
        <label>Currency Symbol</label>
        <input type="text" name="currency_symbol" value="${escapeHTML(client.currency_symbol || '\u20ac')}">
      </div>
      <div class="form-group">
        <label>Daily Rate</label>
        <input type="number" name="daily_rate" value="${client.daily_rate || 0}" step="0.01" min="0">
      </div>
      <div class="form-group">
        <label>Payment Terms (days)</label>
        <input type="number" name="payment_terms_days" value="${client.payment_terms_days || 30}" min="0">
      </div>

      <h3 class="full-width">Payment Details</h3>
      <div class="form-group">
        <label>Bank</label>
        <input type="text" name="pd_bank" value="${escapeHTML((client.payment_details || {}).Bank || '')}">
      </div>
      <div class="form-group">
        <label>IBAN</label>
        <input type="text" name="pd_iban" value="${escapeHTML((client.payment_details || {}).IBAN || '')}">
      </div>
      <div class="form-group">
        <label>BIC</label>
        <input type="text" name="pd_bic" value="${escapeHTML((client.payment_details || {}).BIC || '')}">
      </div>
      <div class="form-group">
        <label>Reference</label>
        <input type="text" name="pd_reference" value="${escapeHTML((client.payment_details || {}).Reference || '')}">
      </div>

      <div class="form-actions full-width">
        <button type="submit" class="btn btn-primary">Save Client</button>
        <button type="button" class="btn btn-secondary" onclick="navigate('#clients')">Cancel</button>
      </div>
    </form>
  `;

  $('#client-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);

    const record = {
      name: fd.get('name'),
      company: fd.get('company'),
      contact: fd.get('contact'),
      email: fd.get('email'),
      address: fd.get('address').split('\n').filter((l) => l.trim()),
      currency: fd.get('currency'),
      currency_symbol: fd.get('currency_symbol'),
      daily_rate: parseFloat(fd.get('daily_rate')) || 0,
      payment_terms_days: parseInt(fd.get('payment_terms_days')) || 30,
      payment_details: {},
    };

    if (fd.get('pd_bank')) record.payment_details.Bank = fd.get('pd_bank');
    if (fd.get('pd_iban')) record.payment_details.IBAN = fd.get('pd_iban');
    if (fd.get('pd_bic')) record.payment_details.BIC = fd.get('pd_bic');
    if (fd.get('pd_reference')) record.payment_details.Reference = fd.get('pd_reference');

    if (editId) record.id = editId;

    await db.clients.put(record);
    showToast('Client saved');
    navigate('#clients');
  });
}

// ---------------------------------------------------------------------------
// View: Invoices list
// ---------------------------------------------------------------------------

async function renderInvoices() {
  const invoiceList = await db.invoices.getAll();

  const main = $('#main-content');
  main.innerHTML = `
    <div class="view-header">
      <h2>Invoices</h2>
      <button class="btn btn-primary" onclick="navigate('#invoices/new')">New Invoice</button>
    </div>

    ${invoiceList.length > 0 ? `
    <table class="data-table">
      <thead>
        <tr>
          <th>Invoice #</th>
          <th>Client</th>
          <th>Date</th>
          <th>Total</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        ${invoiceList.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || '')).map((inv) => `
        <tr>
          <td>${escapeHTML(inv.invoice_number)}</td>
          <td>${escapeHTML(inv.customer_name)}</td>
          <td>${escapeHTML(inv.invoice_date)}</td>
          <td>${escapeHTML(inv.currency_symbol || '')} ${escapeHTML(inv.total || '')}</td>
          <td class="action-cell">
            <button class="btn btn-sm" data-view-invoice="${inv.id}">View</button>
            <button class="btn btn-sm btn-danger" data-delete-invoice="${inv.id}">Delete</button>
          </td>
        </tr>`).join('')}
      </tbody>
    </table>` : `
    <div class="empty-state">
      <p>No invoices yet. Create your first invoice.</p>
    </div>`}
  `;

  main.querySelectorAll('[data-view-invoice]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      const id = Number(e.target.getAttribute('data-view-invoice'));
      const inv = await db.invoices.get(id);
      if (inv && inv.html) {
        showPreview(inv.html, `Invoice-${inv.invoice_number}.pdf`, inv.invoice_number, inv.customer_email, inv.customer_name);
      }
    });
  });

  main.querySelectorAll('[data-delete-invoice]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      const id = Number(e.target.getAttribute('data-delete-invoice'));
      if (confirm('Delete this invoice?')) {
        await db.invoices.delete(id);
        showToast('Invoice deleted');
        renderInvoices();
      }
    });
  });
}

// ---------------------------------------------------------------------------
// View: Invoice Form
// ---------------------------------------------------------------------------

async function renderInvoiceForm() {
  const [clientList, companySettings] = await Promise.all([
    db.clients.getAll(),
    db.company.get(),
  ]);

  const main = $('#main-content');
  main.innerHTML = `
    <div class="view-header">
      <h2>New Invoice</h2>
    </div>

    <form id="invoice-form">
      <div class="form-grid">
        <div class="form-group">
          <label>Client *</label>
          <select name="client_id" id="invoice-client-select" required>
            <option value="">-- Select client --</option>
            ${clientList.map((c) => `<option value="${c.id}">${escapeHTML(c.name)}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label>Invoice Number *</label>
          <input type="text" name="invoice_number" value="${generateInvoiceNumber()}" required>
        </div>
        <div class="form-group">
          <label>Invoice Date *</label>
          <input type="date" name="invoice_date" value="${todayISO()}" required>
        </div>
        <div class="form-group">
          <label>Due Date</label>
          <input type="date" name="due_date" value="${addDays(todayISO(), 30)}">
        </div>
        <div class="form-group">
          <label>Supply Date</label>
          <input type="text" name="supply_date" value="" placeholder="e.g. January 2026">
        </div>
        <div class="form-group">
          <label>Notes</label>
          <input type="text" name="notes" value="Reverse charge: VAT to be accounted for by the recipient.">
        </div>
      </div>

      <h3>Line Items</h3>
      <table class="data-table" id="items-table">
        <thead>
          <tr>
            <th>Description</th>
            <th style="width:80px">Qty</th>
            <th style="width:120px">Unit Price</th>
            <th style="width:100px">Total</th>
            <th style="width:50px"></th>
          </tr>
        </thead>
        <tbody id="items-body">
        </tbody>
        <tfoot>
          <tr>
            <td colspan="5">
              <button type="button" class="btn btn-sm" id="add-item-btn">+ Add Line Item</button>
            </td>
          </tr>
        </tfoot>
      </table>

      <div class="form-actions" style="margin-top: 16px;">
        <button type="button" class="btn btn-primary" id="preview-invoice-btn" ${!pyReady ? 'disabled title="Python is still loading..."' : ''}>Preview Invoice</button>
        <button type="button" class="btn btn-secondary" onclick="navigate('#invoices')">Cancel</button>
      </div>
    </form>
  `;

  // Auto-fill when client is selected
  $('#invoice-client-select').addEventListener('change', async (e) => {
    const clientId = Number(e.target.value);
    if (!clientId) return;
    const client = await db.clients.get(clientId);
    if (!client) return;

    const dueDate = $('[name="due_date"]');
    const invoiceDate = $('[name="invoice_date"]').value;
    if (client.payment_terms_days && invoiceDate) {
      dueDate.value = addDays(invoiceDate, client.payment_terms_days);
    }
  });

  // Add initial empty item row
  addItemRow();

  $('#add-item-btn').addEventListener('click', () => addItemRow());
  $('#preview-invoice-btn').addEventListener('click', () => previewInvoice(clientList, companySettings));
}

function addItemRow(desc = '', qty = 1, price = 0) {
  const tbody = $('#items-body');
  const row = document.createElement('tr');
  row.innerHTML = `
    <td><input type="text" name="item_desc" value="${escapeHTML(desc)}" placeholder="Description" class="table-input"></td>
    <td><input type="number" name="item_qty" value="${qty}" min="0" step="0.5" class="table-input" style="text-align:center"></td>
    <td><input type="number" name="item_price" value="${price}" min="0" step="0.01" class="table-input" style="text-align:right"></td>
    <td class="item-total" style="text-align:right; padding-top: 10px;">0.00</td>
    <td><button type="button" class="btn btn-sm btn-danger remove-item-btn">&times;</button></td>
  `;
  tbody.appendChild(row);

  // Auto-calculate row total
  const qtyInput = row.querySelector('[name="item_qty"]');
  const priceInput = row.querySelector('[name="item_price"]');
  const totalCell = row.querySelector('.item-total');

  function updateTotal() {
    const total = (parseFloat(qtyInput.value) || 0) * (parseFloat(priceInput.value) || 0);
    totalCell.textContent = total.toFixed(2);
  }
  qtyInput.addEventListener('input', updateTotal);
  priceInput.addEventListener('input', updateTotal);
  updateTotal();

  row.querySelector('.remove-item-btn').addEventListener('click', () => {
    row.remove();
  });
}

async function previewInvoice(clientList, companySettings) {
  if (!pyReady) {
    showToast('Python is still loading. Please wait.', 'error');
    return;
  }

  const form = $('#invoice-form');
  const fd = new FormData(form);

  const clientId = Number(fd.get('client_id'));
  const client = clientList.find((c) => c.id === clientId);
  if (!client) {
    showToast('Please select a client.', 'error');
    return;
  }

  // Build items from table rows
  const items = [];
  $$('#items-body tr').forEach((row) => {
    const desc = row.querySelector('[name="item_desc"]').value;
    const qty = parseFloat(row.querySelector('[name="item_qty"]').value) || 0;
    const price = parseFloat(row.querySelector('[name="item_price"]').value) || 0;
    if (desc && qty > 0) {
      items.push({
        description: desc,
        quantity: qty,
        unit_price: price,
        total: qty * price,
      });
    }
  });

  if (items.length === 0) {
    showToast('Add at least one line item.', 'error');
    return;
  }

  const data = {
    invoice_number: fd.get('invoice_number'),
    invoice_date: fd.get('invoice_date'),
    due_date: fd.get('due_date') || '',
    supply_date: fd.get('supply_date') || fd.get('invoice_date'),
    company_name: companySettings.name || 'Your Company',
    company_email: companySettings.email || '',
    company_address: companySettings.address || [],
    company_logo: companySettings.logo || '',
    company_number: companySettings.company_number || '',
    company_vat_label: companySettings.vat_label || 'VAT',
    company_vat: companySettings.vat_number || '',
    customer_name: client.name,
    customer_contact: client.contact || '',
    customer_email: client.email || '',
    customer_address: client.address || [],
    currency: client.currency || 'EUR',
    currency_symbol: client.currency_symbol || '\u20ac',
    items: items,
    payment_details: client.payment_details || {},
    notes: fd.get('notes') || '',
  };

  try {
    const jsonStr = JSON.stringify(data);
    const html = window.pyGenerateInvoice(jsonStr);
    currentInvoiceHTML = html;

    // Save to history
    const subtotal = items.reduce((s, i) => s + i.total, 0);
    await db.invoices.save({
      invoice_number: data.invoice_number,
      invoice_date: data.invoice_date,
      customer_name: data.customer_name,
      customer_email: data.customer_email,
      currency_symbol: data.currency_symbol,
      total: subtotal.toFixed(2),
      html: html,
      created_at: new Date().toISOString(),
    });

    showPreview(html, `Invoice-${data.invoice_number}.pdf`, data.invoice_number, client.email, client.name);
    showToast('Invoice generated and saved');
  } catch (err) {
    console.error('Invoice generation error:', err);
    showToast('Failed to generate invoice: ' + err.message, 'error');
  }
}

// ---------------------------------------------------------------------------
// View: Timesheets list
// ---------------------------------------------------------------------------

async function renderTimesheets() {
  const tsList = await db.timesheets.getAll();

  const main = $('#main-content');
  main.innerHTML = `
    <div class="view-header">
      <h2>Timesheets</h2>
      <button class="btn btn-primary" onclick="navigate('#timesheets/new')">New Timesheet</button>
    </div>

    ${tsList.length > 0 ? `
    <table class="data-table">
      <thead>
        <tr>
          <th>Employee</th>
          <th>Period</th>
          <th>Total Hours</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        ${tsList.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || '')).map((ts) => `
        <tr>
          <td>${escapeHTML(ts.employee_name)}</td>
          <td>${escapeHTML(ts.period_start || '')} - ${escapeHTML(ts.period_end || '')}</td>
          <td>${escapeHTML(ts.total_hours || '')}</td>
          <td class="action-cell">
            <button class="btn btn-sm" data-view-ts="${ts.id}">View</button>
            <button class="btn btn-sm btn-danger" data-delete-ts="${ts.id}">Delete</button>
          </td>
        </tr>`).join('')}
      </tbody>
    </table>` : `
    <div class="empty-state">
      <p>No timesheets yet. Create your first timesheet.</p>
    </div>`}
  `;

  main.querySelectorAll('[data-view-ts]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      const id = Number(e.target.getAttribute('data-view-ts'));
      const ts = await db.timesheets.get(id);
      if (ts && ts.html) {
        showPreview(ts.html, `Timesheet-${ts.employee_name}.pdf`);
      }
    });
  });

  main.querySelectorAll('[data-delete-ts]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      const id = Number(e.target.getAttribute('data-delete-ts'));
      if (confirm('Delete this timesheet?')) {
        await db.timesheets.delete(id);
        showToast('Timesheet deleted');
        renderTimesheets();
      }
    });
  });
}

// ---------------------------------------------------------------------------
// View: Timesheet Form
// ---------------------------------------------------------------------------

async function renderTimesheetForm() {
  const companySettings = await db.company.get();

  const main = $('#main-content');
  main.innerHTML = `
    <div class="view-header">
      <h2>New Timesheet</h2>
    </div>

    <form id="timesheet-form">
      <div class="form-grid">
        <div class="form-group">
          <label>Employee Name *</label>
          <input type="text" name="employee_name" required>
        </div>
        <div class="form-group">
          <label>Employee ID</label>
          <input type="text" name="employee_id" placeholder="e.g. EMP-042">
        </div>
        <div class="form-group">
          <label>Team</label>
          <input type="text" name="employee_team" placeholder="e.g. Engineering">
        </div>
        <div class="form-group">
          <label>Title</label>
          <input type="text" name="title" value="Engineering Timesheet">
        </div>
        <div class="form-group">
          <label>Period Start *</label>
          <input type="date" name="period_start" required>
        </div>
        <div class="form-group">
          <label>Period End *</label>
          <input type="date" name="period_end" required>
        </div>
        <div class="form-group">
          <label>View</label>
          <select name="view">
            <option value="day">Day View</option>
            <option value="period">Period View</option>
          </select>
        </div>
        <div class="form-group">
          <label>Header Layout</label>
          <select name="header_layout">
            <option value="default">Default</option>
            <option value="three-column">Three Column</option>
            <option value="logo-left">Logo Left</option>
            <option value="split">Split</option>
          </select>
        </div>
      </div>

      <h3>Time Entries</h3>
      <table class="data-table" id="ts-entries-table">
        <thead>
          <tr>
            <th style="width:140px">Date</th>
            <th>Description</th>
            <th style="width:150px">Project</th>
            <th style="width:80px">Hours</th>
            <th style="width:50px"></th>
          </tr>
        </thead>
        <tbody id="ts-entries-body">
        </tbody>
        <tfoot>
          <tr>
            <td colspan="5">
              <button type="button" class="btn btn-sm" id="add-ts-entry-btn">+ Add Entry</button>
            </td>
          </tr>
        </tfoot>
      </table>

      <div class="form-actions" style="margin-top: 16px;">
        <button type="button" class="btn btn-primary" id="preview-ts-btn" ${!pyReady ? 'disabled title="Python is still loading..."' : ''}>Preview Timesheet</button>
        <button type="button" class="btn btn-secondary" onclick="navigate('#timesheets')">Cancel</button>
      </div>
    </form>
  `;

  addTimesheetEntry();
  $('#add-ts-entry-btn').addEventListener('click', () => addTimesheetEntry());
  $('#preview-ts-btn').addEventListener('click', () => previewTimesheet(companySettings));
}

function addTimesheetEntry(date = '', desc = '', project = '', hours = 8) {
  const tbody = $('#ts-entries-body');
  const row = document.createElement('tr');
  row.innerHTML = `
    <td><input type="date" name="entry_date" value="${date}" class="table-input"></td>
    <td><input type="text" name="entry_desc" value="${escapeHTML(desc)}" placeholder="Task description" class="table-input"></td>
    <td><input type="text" name="entry_project" value="${escapeHTML(project)}" placeholder="Project" class="table-input"></td>
    <td><input type="number" name="entry_hours" value="${hours}" min="0" max="24" step="0.5" class="table-input" style="text-align:center"></td>
    <td><button type="button" class="btn btn-sm btn-danger remove-ts-entry">&times;</button></td>
  `;
  tbody.appendChild(row);

  row.querySelector('.remove-ts-entry').addEventListener('click', () => row.remove());
}

async function previewTimesheet(companySettings) {
  if (!pyReady) {
    showToast('Python is still loading. Please wait.', 'error');
    return;
  }

  const form = $('#timesheet-form');
  const fd = new FormData(form);

  const entries = [];
  $$('#ts-entries-body tr').forEach((row) => {
    const date = row.querySelector('[name="entry_date"]').value;
    const desc = row.querySelector('[name="entry_desc"]').value;
    const project = row.querySelector('[name="entry_project"]').value;
    const hours = parseFloat(row.querySelector('[name="entry_hours"]').value) || 0;
    if (date && desc) {
      entries.push({ date, description: desc, project, hours });
    }
  });

  if (entries.length === 0) {
    showToast('Add at least one time entry.', 'error');
    return;
  }

  const data = {
    employee_name: fd.get('employee_name'),
    employee_id: fd.get('employee_id') || '',
    employee_team: fd.get('employee_team') || '',
    title: fd.get('title') || 'Engineering Timesheet',
    period_start: fd.get('period_start'),
    period_end: fd.get('period_end'),
    company_logo: companySettings.logo || '',
    entries: entries,
  };

  const view = fd.get('view') || 'day';
  const headerLayout = fd.get('header_layout') || 'default';

  try {
    const jsonStr = JSON.stringify(data);
    const html = window.pyGenerateTimesheet(jsonStr, view, headerLayout);
    currentTimesheetHTML = html;

    // Calculate total hours for record
    const totalHours = entries.reduce((s, e) => s + e.hours, 0);

    await db.timesheets.save({
      employee_name: data.employee_name,
      period_start: data.period_start,
      period_end: data.period_end,
      total_hours: totalHours.toFixed(1),
      html: html,
      created_at: new Date().toISOString(),
    });

    showPreview(html, `Timesheet-${data.employee_name}.pdf`);
    showToast('Timesheet generated and saved');
  } catch (err) {
    console.error('Timesheet generation error:', err);
    showToast('Failed to generate timesheet: ' + err.message, 'error');
  }
}

// ---------------------------------------------------------------------------
// View: Settings
// ---------------------------------------------------------------------------

async function renderSettings() {
  const settings = await db.company.get();

  const main = $('#main-content');
  main.innerHTML = `
    <div class="view-header">
      <h2>Company Settings</h2>
    </div>

    <form id="settings-form" class="form-grid">
      <div class="form-group">
        <label>Company Name *</label>
        <input type="text" name="name" value="${escapeHTML(settings.name)}" required>
      </div>
      <div class="form-group">
        <label>Email *</label>
        <input type="email" name="email" value="${escapeHTML(settings.email)}" required>
      </div>
      <div class="form-group full-width">
        <label>Address (one line per row)</label>
        <textarea name="address" rows="3">${escapeHTML((settings.address || []).join('\n'))}</textarea>
      </div>
      <div class="form-group">
        <label>Company Number</label>
        <input type="text" name="company_number" value="${escapeHTML(settings.company_number || '')}">
      </div>
      <div class="form-group">
        <label>VAT Label</label>
        <input type="text" name="vat_label" value="${escapeHTML(settings.vat_label || 'VAT')}">
      </div>
      <div class="form-group">
        <label>VAT Number</label>
        <input type="text" name="vat_number" value="${escapeHTML(settings.vat_number || '')}">
      </div>
      <div class="form-group full-width">
        <label>Company Logo (paste URL or base64 data URI)</label>
        <input type="text" name="logo" value="${escapeHTML(settings.logo || '')}" placeholder="https://example.com/logo.png or data:image/png;base64,...">
        ${settings.logo ? `<img src="${escapeHTML(settings.logo)}" alt="Logo preview" style="max-width: 150px; max-height: 60px; margin-top: 8px; display: block;">` : ''}
      </div>

      <div class="form-actions full-width">
        <button type="submit" class="btn btn-primary">Save Settings</button>
      </div>
    </form>
  `;

  $('#settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const record = {
      name: fd.get('name'),
      email: fd.get('email'),
      address: fd.get('address').split('\n').filter((l) => l.trim()),
      company_number: fd.get('company_number'),
      vat_label: fd.get('vat_label'),
      vat_number: fd.get('vat_number'),
      logo: fd.get('logo'),
    };
    await db.company.save(record);
    showToast('Settings saved');
    renderSettings();
  });
}

// ---------------------------------------------------------------------------
// Preview modal
// ---------------------------------------------------------------------------

function showPreview(html, pdfFilename, invoiceNumber, clientEmail, clientName) {
  // Remove existing preview
  const existing = $('#preview-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'preview-modal';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-content preview-modal-content">
      <div class="modal-header">
        <h3>Preview</h3>
        <div class="modal-actions">
          <button class="btn btn-primary" id="download-pdf-btn">Download PDF</button>
          <button class="btn btn-secondary" id="download-html-btn">Download HTML</button>
          ${invoiceNumber ? `<button class="btn btn-secondary" id="email-btn">Email</button>` : ''}
          <button class="btn btn-secondary" id="close-preview-btn">Close</button>
        </div>
      </div>
      <iframe id="preview-iframe" sandbox="allow-same-origin"></iframe>
    </div>
  `;
  document.body.appendChild(modal);

  const iframe = $('#preview-iframe');
  iframe.addEventListener('load', () => {
    // Adjust iframe height to content
    try {
      const h = iframe.contentDocument.body.scrollHeight;
      iframe.style.height = Math.max(h + 40, 600) + 'px';
    } catch (e) { /* cross-origin fallback */ }
  });

  // Write HTML into iframe
  const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
  iframeDoc.open();
  iframeDoc.write(html);
  iframeDoc.close();

  $('#download-pdf-btn').addEventListener('click', () => {
    pdfUtils.generatePDF(iframe, pdfFilename || 'document.pdf');
  });

  $('#download-html-btn').addEventListener('click', () => {
    pdfUtils.downloadHTML(html, (pdfFilename || 'document').replace('.pdf', '.html'));
  });

  const emailBtn = $('#email-btn');
  if (emailBtn) {
    emailBtn.addEventListener('click', () => {
      pdfUtils.emailInvoice(invoiceNumber, clientEmail, clientName);
    });
  }

  $('#close-preview-btn').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

// ---------------------------------------------------------------------------
// Dark mode toggle
// ---------------------------------------------------------------------------

function initDarkMode() {
  const saved = localStorage.getItem('darkMode');
  if (saved === 'true') {
    document.body.classList.add('dark');
  }

  const toggle = $('#dark-mode-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.body.classList.toggle('dark');
      localStorage.setItem('darkMode', document.body.classList.contains('dark'));
    });
  }
}

// ---------------------------------------------------------------------------
// Mobile sidebar toggle
// ---------------------------------------------------------------------------

function initMobileSidebar() {
  const toggle = $('#sidebar-toggle');
  const sidebar = $('#sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
    // Close sidebar when a nav item is clicked on mobile
    sidebar.querySelectorAll('.nav-item').forEach((item) => {
      item.addEventListener('click', () => {
        sidebar.classList.remove('open');
      });
    });
  }
}

// ---------------------------------------------------------------------------
// Python ready callback
// ---------------------------------------------------------------------------

window._onPyReady = function () {
  pyReady = true;
  const spinner = $('#py-loading');
  if (spinner) spinner.style.display = 'none';

  // Enable any disabled buttons
  document.querySelectorAll('[disabled][title*="Python"]').forEach((btn) => {
    btn.removeAttribute('disabled');
    btn.removeAttribute('title');
  });
};

// Check if already ready (race condition guard)
if (window.pyReady) {
  window._onPyReady();
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  initDarkMode();
  initMobileSidebar();
  router();
});

window.addEventListener('hashchange', router);

// Expose navigate globally for inline onclick handlers
window.navigate = navigate;
