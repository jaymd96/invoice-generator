/**
 * IndexedDB storage layer for the Invoice Generator web app.
 * Manages clients, company settings, invoices, and timesheets.
 */

const DB_NAME = 'InvoiceGeneratorDB';
const DB_VERSION = 1;

const STORES = {
  clients: 'clients',
  company: 'company',
  invoices: 'invoices',
  timesheets: 'timesheets',
};

let _db = null;

function openDB() {
  if (_db) return Promise.resolve(_db);

  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);

    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORES.clients)) {
        db.createObjectStore(STORES.clients, { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(STORES.company)) {
        db.createObjectStore(STORES.company, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(STORES.invoices)) {
        const store = db.createObjectStore(STORES.invoices, { keyPath: 'id', autoIncrement: true });
        store.createIndex('date', 'invoice_date');
      }
      if (!db.objectStoreNames.contains(STORES.timesheets)) {
        db.createObjectStore(STORES.timesheets, { keyPath: 'id', autoIncrement: true });
      }
    };

    req.onsuccess = (e) => {
      _db = e.target.result;
      resolve(_db);
    };
    req.onerror = () => reject(req.error);
  });
}

function tx(storeName, mode = 'readonly') {
  return openDB().then((db) => {
    const t = db.transaction(storeName, mode);
    return t.objectStore(storeName);
  });
}

function promisify(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// ---------------------------------------------------------------------------
// Generic CRUD
// ---------------------------------------------------------------------------

async function getAll(storeName) {
  const store = await tx(storeName);
  return promisify(store.getAll());
}

async function getById(storeName, id) {
  const store = await tx(storeName);
  return promisify(store.get(id));
}

async function put(storeName, record) {
  const store = await tx(storeName, 'readwrite');
  return promisify(store.put(record));
}

async function deleteRecord(storeName, id) {
  const store = await tx(storeName, 'readwrite');
  return promisify(store.delete(id));
}

// ---------------------------------------------------------------------------
// Public API: Clients
// ---------------------------------------------------------------------------

const clients = {
  getAll: () => getAll(STORES.clients),
  get: (id) => getById(STORES.clients, id),
  put: (client) => put(STORES.clients, client),
  delete: (id) => deleteRecord(STORES.clients, Number(id)),
};

// ---------------------------------------------------------------------------
// Public API: Company settings (singleton with id = 'default')
// ---------------------------------------------------------------------------

const company = {
  async get() {
    const record = await getById(STORES.company, 'default');
    return record || {
      id: 'default',
      name: '',
      email: '',
      address: [],
      logo: '',
      company_number: '',
      vat_label: 'VAT',
      vat_number: '',
    };
  },
  save(settings) {
    return put(STORES.company, { ...settings, id: 'default' });
  },
};

// ---------------------------------------------------------------------------
// Public API: Invoices
// ---------------------------------------------------------------------------

const invoices = {
  getAll: () => getAll(STORES.invoices),
  get: (id) => getById(STORES.invoices, id),
  save: (invoice) => put(STORES.invoices, invoice),
  delete: (id) => deleteRecord(STORES.invoices, Number(id)),
};

// ---------------------------------------------------------------------------
// Public API: Timesheets
// ---------------------------------------------------------------------------

const timesheets = {
  getAll: () => getAll(STORES.timesheets),
  get: (id) => getById(STORES.timesheets, id),
  save: (ts) => put(STORES.timesheets, ts),
  delete: (id) => deleteRecord(STORES.timesheets, Number(id)),
};

// ---------------------------------------------------------------------------
// Backup: Export / Import all data
// ---------------------------------------------------------------------------

async function exportAll() {
  const [allClients, allCompany, allInvoices, allTimesheets] = await Promise.all([
    getAll(STORES.clients),
    getAll(STORES.company),
    getAll(STORES.invoices),
    getAll(STORES.timesheets),
  ]);

  const payload = {
    version: 1,
    exported_at: new Date().toISOString(),
    clients: allClients,
    company: allCompany,
    invoices: allInvoices,
    timesheets: allTimesheets,
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `invoice-generator-backup-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function importAll(jsonObj) {
  const requiredKeys = ['clients', 'company', 'invoices', 'timesheets'];
  for (const key of requiredKeys) {
    if (!Array.isArray(jsonObj[key])) {
      throw new Error(`Invalid backup: missing or invalid "${key}" array`);
    }
  }

  const database = await openDB();
  const storeNames = [STORES.clients, STORES.company, STORES.invoices, STORES.timesheets];
  const t = database.transaction(storeNames, 'readwrite');

  const clearAndPut = (storeName, records) => {
    const store = t.objectStore(storeName);
    store.clear();
    for (const record of records) {
      store.put(record);
    }
  };

  clearAndPut(STORES.clients, jsonObj.clients);
  clearAndPut(STORES.company, jsonObj.company);
  clearAndPut(STORES.invoices, jsonObj.invoices);
  clearAndPut(STORES.timesheets, jsonObj.timesheets);

  await new Promise((resolve, reject) => {
    t.oncomplete = () => resolve();
    t.onerror = () => reject(t.error);
  });

  return {
    clients: jsonObj.clients.length,
    invoices: jsonObj.invoices.length,
    timesheets: jsonObj.timesheets.length,
  };
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

window.db = { clients, company, invoices, timesheets, openDB, exportAll, importAll };
