class CustomNavbar extends HTMLElement {
    connectedCallback() {
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                nav {
                    background-color: white;
                    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
                    
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                }
                .container {
                    max-width: 1280px;
                    margin: 0 auto;
                    padding: 0 1.5rem;
                }
                .logo {
                    color: #4f46e5;
                    font-weight: 700;
                    font-size: 1.7rem;
                }
                .nav-link {
                    color: #4b5563;
                    font-weight: 500;
                    transition: color 0.2s ease;
                }
                .nav-link:hover {
                    color: #4f46e5;
                }
                @media (max-width: 768px) {
                    .nav-menu {
                        display: none;
                    }
                    .mobile-menu-button {
                        display: block;
                    }
                }
            </style>
            <nav class="py-6">
                <!-- 왼쪽 로고 -->
                <div class="container mx-auto flex justify-between items-center">
                    <a href="/" class="logo">
                        <i data-feather="edit-3"></i>
                        <span>🪄MeetNote Magic Wand</span>
                    </a>
                </div>
            </nav>
        `;
    }
}

customElements.define('custom-navbar', CustomNavbar);