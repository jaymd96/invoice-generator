/**
 * PDF generation, HTML download, and email helpers.
 * Uses html2pdf.js for PDF conversion from rendered HTML.
 */

/**
 * Generate a PDF from an iframe's content and trigger download.
 * @param {HTMLIFrameElement} iframe - The iframe containing the rendered document
 * @param {string} filename - Desired PDF filename
 */
async function generatePDF(iframe, filename) {
  const content = iframe.contentDocument || iframe.contentWindow.document;
  const element = content.querySelector('.invoice-container') ||
                  content.querySelector('.timesheet-container') ||
                  content.body;

  if (!element) {
    alert('No content found to export.');
    return;
  }

  // Clone the element into the main document so html2pdf can access it
  const clone = element.cloneNode(true);

  // Copy computed styles inline from the iframe
  const iframeStyles = Array.from(content.querySelectorAll('style'))
    .map((s) => s.textContent)
    .join('\n');

  const wrapper = document.createElement('div');
  wrapper.style.position = 'absolute';
  wrapper.style.left = '-9999px';
  wrapper.style.top = '0';
  const styleEl = document.createElement('style');
  styleEl.textContent = iframeStyles;
  wrapper.appendChild(styleEl);
  wrapper.appendChild(clone);
  document.body.appendChild(wrapper);

  const opt = {
    margin: 0,
    filename: filename || 'document.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, logging: false },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
  };

  try {
    await html2pdf().set(opt).from(clone).save();
  } catch (err) {
    console.error('PDF generation error:', err);
    alert('PDF generation failed. Try using your browser\'s Print > Save as PDF instead.');
  } finally {
    document.body.removeChild(wrapper);
  }
}

/**
 * Trigger download of raw HTML as a file.
 * @param {string} html - The HTML content
 * @param {string} filename - Desired filename
 */
function downloadHTML(html, filename) {
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || 'document.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Open a mailto: link with pre-filled subject and body.
 * @param {string} invoiceNumber
 * @param {string} clientEmail
 * @param {string} clientName
 */
function emailInvoice(invoiceNumber, clientEmail, clientName) {
  const subject = encodeURIComponent(`Invoice ${invoiceNumber}`);
  const body = encodeURIComponent(
    `Dear ${clientName || 'Client'},\n\nPlease find attached invoice ${invoiceNumber}.\n\nPlease download the PDF and attach it to this email before sending.\n\nKind regards`
  );
  window.location.href = `mailto:${clientEmail || ''}?subject=${subject}&body=${body}`;
}

// Expose globally
window.pdfUtils = { generatePDF, downloadHTML, emailInvoice };
