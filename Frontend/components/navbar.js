class CustomNavbar extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
          position: sticky;
          top: 0;
          z-index: 50;
          background-color: white;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .navbar-container {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem 2rem;
          max-width: 1280px;
          margin: 0 auto;
        }
        .logo {
          font-weight: 700;
          font-size: 1.5rem;
          color: #4f46e5;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .nav-links {
          display: flex;
          gap: 2rem;
        }
        .nav-link {
          color: #4b5563;
          font-weight: 500;
          transition: color 0.2s;
        }
        .nav-link:hover {
          color: #4f46e5;
        }
        .mobile-menu-btn {
          display: none;
        }
        @media (max-width: 768px) {
          .nav-links {
            display: none;
          }
          .mobile-menu-btn {
            display: block;
          }
        }
      </style>
      <div class="navbar-container">
        <a href="/" class="logo">
          <i data-feather="compass"></i>
          PlanningTeam.No1
        </a>
        <div class="nav-links">
          <a href="/" class="nav-link">홈</a>
          <a href="/tools" class="nav-link">Kothea</a>
          <a href="/templates" class="nav-link">템플릿</a>
          <a href="/team" class="nav-link">팀</a>
          <a href="/settings" class="nav-link">설정</a>
        </div>
        <button class="mobile-menu-btn">
          <i data-feather="menu"></i>
        </button>
      </div>
    `;
  }
}
customElements.define('custom-navbar', CustomNavbar);