class CustomFooter extends HTMLElement {
    connectedCallback() {
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                footer {
                    background-color: #f9fafb;
                    border-top: 1px solid #e5e7eb;
                }
                .container {
                    max-width: 1280px;
                    margin: 0 auto;
                    padding: 2rem 1rem;
                }
                .footer-links {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 2rem;
                }
                .footer-title {
                    font-weight: 600;
                    color: #111827;
                    margin-bottom: 1rem;
                }
                .footer-link {
                    color: #6b7280;
                    margin-bottom: 0.5rem;
                    display: block;
                    transition: color 0.2s ease;
                }
                .footer-link:hover {
                    color: #4f46e5;
                }
                .copyright {
                    color: #9ca3af;
                    font-size: 0.875rem;
                    text-align: center;
                    margin-top: 3rem;
                    padding-top: 2rem;
                    border-top: 1px solid #e5e7eb;
                }
                @media (min-width: 768px) {
                    .footer-links {
                        grid-template-columns: repeat(4, 1fr);
                    }
                }
            </style>
            <footer class="py-8">
                <div class="container mx-auto">
                    <div class="copyright">
                        © 2026 MeetNote Magic Wand. All rights reserved.
                    </div>
                </div>
            </footer>
        `;
    }
}

customElements.define('custom-footer', CustomFooter);