class CustomNavbar extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
        }
        nav {
          background-color: white;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 1rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .logo {
          font-weight: 700;
          font-size: 1.25rem;
          color: #0ea5e9;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .right-logo img {
          height: 36px;   /* 로고 크기 */
          cursor: pointer;
        }
        
      </style>

      <nav>
        <div class="container mx-auto flex justify-between items-center">
          <!-- ✅ 왼쪽 로고 -->
          <a href="/" class="logo flex items-center space-x-2">
            <i data-feather="zap"></i>
            <span>BizDraft AI</span>
          </a>

          <!-- ✅ 오른쪽 상단 로고 -->
          <div class="right-logo">
            <a href="https://kothea.or.kr/index" target="_blank">
              <img src="Frontend/component/images/company-logo.png" alt="Company Logo">
            </a>
          <div class="flex items-center space-x-6"></div>
        </div>
      </nav>
    `;
  }
}
customElements.define('custom-navbar', CustomNavbar);