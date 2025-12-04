/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useState, Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

// Access Code Modal Component
class AccessCodeModal extends Component {
    static template = "gm_pos_access_code.AccessCodeModal";
    static components = { Dialog };
    
    setup() {
        this.state = this.props.state;
    }
}

// Print Dialog Component
class PrintDialog extends Component {
    static template = "gm_pos_access_code.PrintDialog";
    static components = { Dialog };
    
    setup() {
        this.state = useState({
            isPrinting: false
        });
    }
    
    async onPrint() {
        this.state.isPrinting = true;
        
        // Create print content
        const printContent = `
            <div style="text-align: center; padding: 20px; font-family: Arial, sans-serif;">
                <h2>Access Code Receipt</h2>
                <hr>
                <p><strong>Booking Code:</strong> ${this.props.bookingCode || 'N/A'}</p>
                <p><strong>Booking From:</strong> ${this.props.bookingFrom || 'N/A'}</p>
                <p><strong>Booking Price:</strong> ${this.props.bookingPrice || 'N/A'}</p>
                <p><strong>Bottle Size:</strong> ${this.props.bottleSize || 'N/A'}</p>
                <hr>
                <h3>Access Code</h3>
                <div style="font-size: 24px; font-weight: bold; letter-spacing: 2px; margin: 20px 0;">
                    ${this.props.accessCode}
                </div>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    Generated on: ${new Date().toLocaleString()}
                </p>
                <p style="font-size: 12px; color: #666;">
                    Expires on: ${this.props.expiryDate}
                </p>
            </div>
        `;
        
        // Create print window
        const printWindow = window.open('', '_blank', 'width=600,height=400');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Access Code Receipt</title>
                    <style>
                        @media print { body { margin: 0; } }
                    </style>
                </head>
                <body>
                    ${printContent}
                    <script>
                        window.onload = function() {
                            window.print();
                            window.onafterprint = function() { window.close(); };
                        };
                    <\/script>
                </body>
            </html>
        `);
        printWindow.document.close();
        
        this.state.isPrinting = false;
        this.props.close();
    }
}

// Patch ProductScreen to add booking form functionality - ONLY for custom POS
patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        
        this.dialog = useService("dialog");
        
        if (document.body.classList.contains('pos-custom')) {
            // Use logo from gm_web static assets (Option B)
            const companyLogoUrl = '/gm_web/static/src/img/logo.png';

        this.state = useState({
                // form
            bookingCode: '',
            bookingFrom: '',
            bookingPrice: '',
            bottleSize: '',
                // validity
                activeDays: 7,
                activePeriod: 'days',
                // copies
                numberOfCopies: 1,
                // bulk
                selectedFile: null,
                selectedFileObj: null,
                // preview/grid
                accessCodes: [],
                totalPages: 0,
                // branding
                companyLogoUrl,
                // legacy
            accessCodeGenerated: false,
            generatedCode: '',
            qrCodeText: '',
            expiryDate: ''
        });
        }
    },
    
    // form handlers
    onBookingCodeChange(ev) {
        if (document.body.classList.contains('pos-custom')) {
        this.state.bookingCode = ev.target.value;
        }
    },
    
    onBookingFromChange(ev) {
        if (document.body.classList.contains('pos-custom')) {
        this.state.bookingFrom = ev.target.value;
        }
    },
    
    onBookingPriceChange(ev) {
        if (document.body.classList.contains('pos-custom')) {
        this.state.bookingPrice = ev.target.value;
        }
    },
    
    onBottleSizeChange(ev) {
        if (document.body.classList.contains('pos-custom')) {
        this.state.bottleSize = ev.target.value;
        }
    },

    onActiveDaysChange(ev) {
        if (document.body.classList.contains('pos-custom')) {
            const v = parseInt(ev.target.value, 10);
            this.state.activeDays = Number.isFinite(v) ? v : 7;
        }
    },

    onActivePeriodChange(ev) {
        if (document.body.classList.contains('pos-custom')) {
            this.state.activePeriod = ev.target.value;
        }
    },

    onNumberOfCopiesChange(ev) {
        if (document.body.classList.contains('pos-custom')) {
            const v = parseInt(ev.target.value, 10);
            this.state.numberOfCopies = Number.isFinite(v) && v > 0 ? Math.min(v, 100) : 3;
        }
    },

    // bulk helpers
    onDownloadExample() {
        if (!document.body.classList.contains('pos-custom')) return;
        const payload = {
            booking_code: this.state.bookingCode || '',
            booking_from: this.state.bookingFrom || '',
            booking_price: this.state.bookingPrice || '',
            bottle_size: this.state.bottleSize || '100ml',
            validity_value: this.state.activeDays || 7,
            validity_unit: this.state.activePeriod || 'days',
            access_code: (this.state.generatedCode || (this.state.accessCodes && this.state.accessCodes[0] && this.state.accessCodes[0].code) || '')
        };
        fetch('/gm_pos_access_code/export_xlsx', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        }).then(async (res) => {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'booking_example.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        }).catch(() => {
            this.env.services.notification.add('Failed to download template', { type: 'danger' });
        });
    },

    onBrowseFile() {
        if (!document.body.classList.contains('pos-custom')) return;
        const fileRef = (this.refs && this.refs.fileInput && this.refs.fileInput.el) || document.getElementById('gm-pos-file-input');
        if (fileRef) fileRef.click();
    },

    onFileSelected(ev) {
        if (!document.body.classList.contains('pos-custom')) return;
        const file = ev.target && ev.target.files && ev.target.files[0];
        if (file) {
            this.state.selectedFile = file.name;
            this.state.selectedFileObj = file;
            this.env.services.notification.add(`File selected: ${file.name}`, { type: 'success' });
        }
    },

    async onBulkGenerate() {
        if (!document.body.classList.contains('pos-custom')) return;
        const file = this.state.selectedFileObj;
        if (!file) {
            this.env.services.notification.add('Please select an Excel file first', { type: 'warning' });
            return;
        }
        try {
            const fd = new FormData();
            fd.append('file', file, file.name);
            const res = await fetch('/gm_pos_access_code/import_xlsx', { method: 'POST', body: fd });
            const json = await res.json();
            if (json && json.success) {
                this.state.accessCodes = (json.codes || []).map((code, idx) => ({ id: idx + 1, code, pageNumber: idx + 1 }));
                this.state.totalPages = json.total || this.state.accessCodes.length;
                this.env.services.notification.add(`Imported ${this.state.totalPages} codes`, { type: 'success' });
            } else {
                this.env.services.notification.add(json && json.error ? json.error : 'Import failed', { type: 'danger' });
            }
        } catch (e) {
            this.env.services.notification.add('Import failed', { type: 'danger' });
        }
    },

    _genCode() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let result = '';
        for (let i = 0; i < 9; i++) {
            if (i === 3 || i === 6) result += '-';
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },

    async onDownloadPDF() {
        if (!document.body.classList.contains('pos-custom')) return;
        if (!this.state.accessCodes.length) {
            this.env.services.notification.add('No codes to download', { type: 'warning' });
            return;
        }
        
        try {
            // Prepare records data for bulk create
            const recordsData = this.state.accessCodes.map(codeData => ({
                name: codeData.code,
                booking_code: codeData.bookingCode || '',
                booking_from: codeData.bookingFrom || '',
                booking_price: codeData.bookingPrice || 0,
                bottle_size: codeData.bottleSize || '100ml',
                validity_value: codeData.validityValue || 7,
                validity_unit: codeData.validityUnit || 'days'
            }));
            
            // Create temporary access code records for PDF generation (bulk create)
            const accessCodeIds = await this.env.services.orm.create('pos.access.code', recordsData);
            
            // Generate PDF using Odoo report system
            const reportUrl = `/report/pdf/gm_pos_access_code.action_access_code_report/${accessCodeIds.join(',')}`;
            
            // Direct download PDF
            const today = new Date();
            const dateStr = today.toISOString().split('T')[0]; // YYYY-MM-DD format
            const fileName = `scentopia-${dateStr}.pdf`;
            
            const a = document.createElement('a');
            a.href = reportUrl;
            a.download = fileName;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            this.env.services.notification.add('PDF generated successfully!', { type: 'success' });
            
        } catch (error) {
            console.error('Error generating PDF:', error);
            this.env.services.notification.add('Error generating PDF', { type: 'danger' });
        }
    },
    
    onOpenAccessCodeModal() {
        if (!document.body.classList.contains('pos-custom')) {
            return;
        }
        
        this.dialog.add(AccessCodeModal, {
            state: this.state,
            onBookingCodeChange: (ev) => this.onBookingCodeChange(ev),
            onBookingFromChange: (ev) => this.onBookingFromChange(ev),
            onBookingPriceChange: (ev) => this.onBookingPriceChange(ev),
            onBottleSizeChange: (ev) => this.onBottleSizeChange(ev),
            onActiveDaysChange: (ev) => this.onActiveDaysChange(ev),
            onActivePeriodChange: (ev) => this.onActivePeriodChange(ev),
            onGenerateAccessCode: () => this.onGenerateAccessCode(),
            onDownloadExample: () => this.onDownloadExample(),
            onBrowseFile: () => this.onBrowseFile(),
            onFileSelected: (ev) => this.onFileSelected(ev),
            onBulkGenerate: () => this.onBulkGenerate(),
            onDownloadPDF: () => this.onDownloadPDF(),
            onPrintPreview: () => this.onPrintPreview(),
        });
    },

    async onPrintPreview() {
        if (!document.body.classList.contains('pos-custom')) {
            return;
        }
        if (!this.state.accessCodes.length) {
            this.env.services.notification.add('Please generate access code first', { type: 'warning' });
            return;
        }
        
        try {
            // Prepare records data for bulk create
            const recordsData = this.state.accessCodes.map(codeData => ({
                name: codeData.code,
                booking_code: codeData.bookingCode || '',
                booking_from: codeData.bookingFrom || '',
                booking_price: codeData.bookingPrice || 0,
                bottle_size: codeData.bottleSize || '100ml',
                validity_value: codeData.validityValue || 7,
                validity_unit: codeData.validityUnit || 'days'
            }));
            
            // Create temporary access code records for printing
            const accessCodeIds = await this.env.services.orm.create('pos.access.code', recordsData);
            
            // Generate PDF using Odoo report system (same as Download)
            const reportUrl = `/report/pdf/gm_pos_access_code.action_access_code_report/${accessCodeIds.join(',')}`;
            
            // Create hidden iframe to load PDF and trigger print dialog directly
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = reportUrl;
            document.body.appendChild(iframe);
            
            // Wait for PDF to load then trigger print dialog
            iframe.onload = function() {
                const win = iframe.contentWindow;
                if (!win) return;
                const cleanup = () => {
                    // remove listeners and iframe after print completes
                    win.removeEventListener('afterprint', cleanup);
                    window.removeEventListener('focus', cleanup);
                    if (iframe.parentNode) {
                        iframe.parentNode.removeChild(iframe);
                    }
                };
                // Cleanup when print dialog closes (best-effort across browsers)
                win.addEventListener('afterprint', cleanup);
                // Fallback: when focus returns to main window
                window.addEventListener('focus', cleanup, { once: true });
                // Trigger print
                win.print();
            };
            
            this.env.services.notification.add('Print dialog opened!', { type: 'success' });
            
        } catch (error) {
            console.error('Error opening print preview:', error);
            this.env.services.notification.add('Error opening print preview', { type: 'danger' });
        }
    },

    
    // single generate -> also fill preview grid
    async onGenerateAccessCode() {
        if (!document.body.classList.contains('pos-custom')) {
            return;
        }
        
        if (!this.state.bottleSize) {
            this.env.services.notification.add('Please select bottle size', { type: 'warning' });
            return;
        }
        
        try {
            // Use fetch API to call Odoo RPC
            const response = await fetch('/web/dataset/call_kw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        model: 'pos.access.code',
                        method: 'create',
                        args: [{
                            booking_code: this.state.bookingCode,
                            booking_from: this.state.bookingFrom,
                            booking_price: parseFloat(this.state.bookingPrice) || 0,
                            bottle_size: this.state.bottleSize,
                            validity_value: this.state.activeDays,
                            validity_unit: this.state.activePeriod
                        }],
                        kwargs: {}
                    },
                    id: Math.floor(Math.random() * 1000000)
                })
            });
            
            const data = await response.json();
            if (data.result) {
                const readResponse = await fetch('/web/dataset/call_kw', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: {
                            model: 'pos.access.code',
                            method: 'read',
                            args: [[data.result]],
                            kwargs: { fields: ['name', 'expiry_date'] }
                        },
                        id: Math.floor(Math.random() * 1000000)
                    })
                });
                const readData = await readResponse.json();
                if (readData.result && readData.result[0]) {
                    const generatedCode = readData.result[0].name;
                    this.state.generatedCode = generatedCode;
                    this.state.qrCodeText = generatedCode;
                    this.state.expiryDate = new Date(readData.result[0].expiry_date).toLocaleString();
                    this.state.accessCodeGenerated = true;
                    
                    // Fill preview grid with user-specified number of copies
                    const copies = this.state.numberOfCopies || 1;
                    this.state.accessCodes = Array.from({ length: copies }, (_, index) => ({
                        id: index + 1,
                        code: generatedCode,
                        pageNumber: index + 1
                    }));
                    this.state.totalPages = copies;
                    
                    this.env.services.notification.add('Access code generated successfully!', { type: 'success' });
                }
            }
        } catch (error) {
            console.error('Error generating access code:', error);
            this.env.services.notification.add('Error generating access code', { type: 'danger' });
        }
    }
});
