class CustomFooter extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
          margin-top: auto;
        }
        footer {
          background-color: #f8fafc;
          border-top: 1px solid #e2e8f0;
        }
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 3rem 2rem;
        }
        .contact-info {
          max-width: 500px;
          margin: 0 auto;
          padding: 2rem;
          background: white;
          border-radius: 0.5rem;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          text-align: center;
        }
        .contact-item {
          margin-bottom: 1rem;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }
        .contact-icon {
          color: #0ea5e9;
        }
.connect-title {
          text-align: center;
          font-size: 1.25rem;
          font-weight: 600;
          margin-bottom: 1.5rem;
          color: #1e3a8a;
        }
        .copyright {
          border-top: 1px solid #e2e8f0;
        }
      </style>
      <footer>
        <div class="container mx-auto">
          <div class="connect-title">Connect With Me</div>
          <div class="contact-info">
            <div class="contact-item">
              <i data-feather="mail" class="contact-icon"></i>
              <span>kjs@kothea.co.kr</span>
            </div>
            <div class="contact-item">
              <i data-feather="phone" class="contact-icon"></i>
              <span>+82 10-2335-1589</span>
            </div>
          </div>
<div class="copyright mt-12 pt-6 text-center text-gray-500 text-sm">
            <p>© 2025 BizDraft AI. All rights reserved.</p>
</div>
        </div>
      </footer>
    `;
  }
}
customElements.define('custom-footer', CustomFooter);