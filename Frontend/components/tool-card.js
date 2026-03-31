class ToolCard extends HTMLElement {
  static get observedAttributes() {
    return ['title', 'icon', 'description', 'link', 'color'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    this.render();
  }

  attributeChangedCallback() {
    this.render();
  }

  render() {
    const title = this.getAttribute('title') || '';
    const icon = this.getAttribute('icon') || 'box';
    const description = this.getAttribute('description') || '';
    const link = this.getAttribute('link') || '#';
    const color = this.getAttribute('color') || 'indigo';

    /* 🎨 카드 테마별 배경 이미지 */
    const BG_MAP = {
      indigo: 'image/home1.png',
      blue: 'image/bg-meeting.jpg',
      purple: 'image/bg-meeting.jpg',
      gray: 'image/bg-default.jpg'
    };

    /* 🎨 포인트 컬러 (텍스트/버튼용) */
    const COLOR_RGB = {
      indigo: '79, 70, 229',
      blue: '37, 99, 235',
      purple: '124, 58, 237',
      gray: '148, 163, 184'
    };

    const bgImage = BG_MAP[color] || BG_MAP.gray;
    const rgb = COLOR_RGB[color] || COLOR_RGB.gray;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }

        .card {
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 1rem;
          box-shadow: 0 6px 18px rgba(0,0,0,0.06);
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .card:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 26px rgba(0,0,0,0.08);
        }

        /* 실제 콘텐츠 레이어 */
        .card-content {
          position: relative;
          z-index: 1;
          height: 100%;
          backdrop-filter: blur(8px);
          display: flex;
          flex-direction: column;
        }

        .card-link-wrapper {
          display: flex;
          flex-direction: column;
          height: 100%;
          text-decoration: none;
          color: inherit;
        }

        .card-header {
          padding: 1.5rem 1.5rem 1rem;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }

        .card-icon {
          width: 3rem;
          height: 3rem;
          color: rgba(${rgb}, 0.9);
        }

        .card-icon-label {
          font-weight: 500;
          font-size: 0.875rem;
          color: rgba(${rgb}, 0.85);
        }

        .card-body {
          padding: 0 1.5rem 1.5rem;
          display: flex;
          flex-direction: column;
          text-align: center;
          flex: 1;
        }

        .card-title {
          font-size: 1.25rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
          color: #1f2937;
        }

        .card-description {
          color: #6b7280;
          font-size: 0.95rem;
          margin-bottom: 1.25rem;
        }

        .card-link {
          margin-top: auto;
          background-color: #0a2a8a;
          color: #ffffff;

          border: none;
          border-radius: 0.5rem;

          padding: 0.6rem 1.2rem;
          font-size: 0.875rem;
          font-weight: 500;

          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 0.4rem;

          transition: background-color 0.2s ease, transform 0.2s ease;
        }

        .card-link:hover {
          background-color: #0a2a8a;
          transform: translateY(-1px);
        }

        .card-link-icon {
          width: 1rem;
          height: 1rem;
        }

        .card-icon {
          color: #0a2a8a;
        }        
      </style>

      <div class="card">

        <div class="card-content">
          <a href="${link}" class="card-link-wrapper">
            <div class="card-header">
              <i data-feather="${icon}" class="card-icon"></i>
              <span class="card-icon-label">${title}</span>
            </div>

            <div class="card-body">
              <h3 class="card-title">${title}</h3>
              <p class="card-description">${description}</p>

              <span class="card-link">
                시작하기
                <i data-feather="arrow-right" class="card-link-icon"></i>
              </span>
            </div>
          </a>
        </div>
      </div>
    `;
  }
}

customElements.define('tool-card', ToolCard);
