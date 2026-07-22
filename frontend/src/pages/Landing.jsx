import { useState } from "react";

export default function Landing() {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <>
      <style>{`
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');

        .lc-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: white;
          padding: 12px 28px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
          position: sticky;
          top: 0;
          z-index: 100;
        }

        .lc-logo {
          display: flex;
          align-items: center;
          gap: 10px;
          text-decoration: none;
          color: #8b0000;
          font-weight: 800;
          font-size: 1.3rem;
          font-family: "Raleway", sans-serif;
        }

        .lc-logo img { width: 44px; height: 44px; object-fit: contain; }

        .lc-nav-toggle {
          display: none;
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #8b0000;
        }

        .lc-nav-links {
          display: flex;
          list-style: none;
          gap: 28px;
          margin: 0;
          padding: 0;
        }

        .lc-nav-links a {
          text-decoration: none;
          color: #333;
          font-size: 15px;
          font-weight: 600;
          transition: color 0.2s;
        }

        .lc-nav-links a:hover { color: #8b0000; }

        /* Hero */
        .lc-hero {
          background-color: #8b0000;
          color: white;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 60px 48px;
          min-height: 340px;
          gap: 40px;
          overflow: hidden;
        }

        .lc-hero-text {
          position: relative;
          min-height: 180px;
          min-width: 260px;
        }

        .lc-hero-text .line1 {
          position: absolute;
          top: 0;
          font-size: 2.4rem;
          font-weight: 400;
          font-family: "Raleway", sans-serif;
        }

        .lc-hero-text .line2 {
          position: absolute;
          top: 54px;
          font-size: 2.8rem;
          font-weight: 700;
          font-family: "Raleway", sans-serif;
        }

        .lc-hero-text .line3 {
          position: absolute;
          top: 117px;
          font-size: 2.4rem;
          font-weight: 400;
          font-family: "Raleway", sans-serif;
        }

        .lc-hero-image img {
          width: 320px;
          max-width: 100%;
          border-radius: 12px;
        }

        /* Gift of Life */
        .lc-gift {
          padding: 70px 48px;
        }

        .lc-gift-content {
          max-width: 1100px;
          margin: 0 auto;
          display: flex;
          align-items: center;
          gap: 50px;
          flex-wrap: wrap;
        }

        .lc-gift-text { flex: 1; min-width: 280px; }

        .lc-gift-text h3 {
          font-size: 1.8rem;
          font-weight: 700;
          color: #1a1a1a;
          margin-bottom: 16px;
        }

        .lc-gift-text p {
          color: #555;
          font-size: 1.05rem;
          line-height: 1.7;
          margin-bottom: 28px;
        }

        .lc-cta-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 14px;
        }

        .lc-cta-btn {
          background-color: #8b0000;
          color: white;
          padding: 12px 24px;
          border-radius: 8px;
          text-decoration: none;
          font-size: 15px;
          font-weight: 600;
          transition: background-color 0.25s, transform 0.15s;
          display: inline-block;
        }

        .lc-cta-btn:hover {
          background-color: #6a0000;
          transform: translateY(-2px);
        }

        .lc-gift-image img {
          width: 300px;
          max-width: 100%;
          border-radius: 12px;
        }

        /* Stats */
        .lc-stats {
          background-color: #f4f4f4;
          padding: 52px 48px;
          display: flex;
          justify-content: center;
          gap: 80px;
          flex-wrap: wrap;
          text-align: center;
        }

        .lc-stat-item i {
          font-size: 2.5rem;
          color: #8b0000;
          margin-bottom: 12px;
        }

        .lc-stat-item strong {
          display: block;
          font-size: 2rem;
          font-weight: 800;
          color: #8b0000;
        }

        .lc-stat-item span {
          font-size: 1rem;
          color: #666;
        }

        /* Footer */
        .lc-footer {
          background-color: #1a1a1a;
          color: white;
          padding: 44px 48px 28px;
        }

        .lc-footer-content {
          max-width: 1100px;
          margin: 0 auto;
          display: flex;
          gap: 60px;
          flex-wrap: wrap;
          justify-content: space-between;
        }

        .lc-footer-left { flex: 2; min-width: 260px; }

        .lc-footer-logo {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 14px;
        }

        .lc-footer-logo img { width: 36px; }
        .lc-footer-logo h2 { font-size: 1.2rem; font-weight: 700; }

        .lc-footer-about {
          color: #ccc;
          font-size: 14px;
          line-height: 1.7;
          margin-bottom: 16px;
        }

        .lc-footer-partner-logos {
          display: flex;
          gap: 12px;
          align-items: center;
          flex-wrap: wrap;
        }

        .lc-footer-partner-logos img { height: 42px; object-fit: contain; }

        .lc-footer-right { flex: 1; min-width: 200px; }

        .lc-footer-right h4 {
          font-size: 1rem;
          font-weight: 700;
          margin-bottom: 14px;
        }

        .lc-footer-contact {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 20px;
        }

        .lc-footer-contact a {
          color: #ccc;
          text-decoration: none;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: color 0.2s;
        }

        .lc-footer-contact a:hover { color: white; }

        .lc-social-icons { display: flex; gap: 16px; }

        .lc-social-icons a {
          color: #ccc;
          font-size: 1.4rem;
          text-decoration: none;
          transition: color 0.2s;
        }

        .lc-social-icons a:hover { color: white; }

        .lc-footer-bottom {
          text-align: center;
          border-top: 1px solid #333;
          margin-top: 28px;
          padding-top: 18px;
          color: #888;
          font-size: 13px;
        }

        /* Mobile nav */
        @media (max-width: 768px) {
          .lc-nav-toggle { display: block; }

          .lc-nav-links {
            display: ${navOpen ? "flex" : "none"};
            position: fixed;
            top: 0;
            right: 0;
            height: 100%;
            width: 240px;
            background: white;
            flex-direction: column;
            padding: 70px 28px 28px;
            box-shadow: -4px 0 20px rgba(0,0,0,0.15);
            z-index: 200;
            gap: 22px;
          }

          .lc-hero { flex-direction: column; padding: 40px 24px; text-align: center; }
          .lc-hero-text { position: static; min-height: auto; display: flex; flex-direction: column; gap: 4px; }
          .lc-hero-text .line1, .lc-hero-text .line2, .lc-hero-text .line3 { position: static; font-size: 1.8rem; }
          .lc-hero-image img { width: 220px; }
          .lc-gift { padding: 40px 24px; }
          .lc-stats { gap: 36px; padding: 40px 24px; }
          .lc-footer { padding: 32px 24px 20px; }
        }
      `}</style>

      {/* Header */}
      <header className="lc-header">
        <a href="/" className="lc-logo">
          <img src="/images/index/LifeConnect_Logo.png" alt="Life Connect Logo" />
          Life Connect
        </a>

        <button
          className="lc-nav-toggle"
          onClick={() => setNavOpen(!navOpen)}
          aria-label="Toggle navigation"
        >
          ☰
        </button>

        <nav>
          <ul className="lc-nav-links" style={{ display: navOpen ? "flex" : undefined }}>
            <li><a href="/donor/query">Queries</a></li>
            <li><a href="/about">About Us</a></li>
            <li><a href="/admin/login">Admin Login</a></li>
            <li><a href="/donor/login">Donor Login</a></li>
            <li><a href="/blood-banks">Blood Bank</a></li>
          </ul>
        </nav>

        {navOpen && (
          <div
            style={{ position: "fixed", inset: 0, zIndex: 150, background: "rgba(0,0,0,0.3)" }}
            onClick={() => setNavOpen(false)}
          />
        )}
      </header>

      {/* Hero Section */}
      <section className="lc-hero">
        <div className="lc-hero-text">
          <span className="line1">Join the</span>
          <span className="line2">Life-Saving</span>
          <span className="line3">Movement</span>
        </div>
        <div className="lc-hero-image">
          <img src="/images/index/blood-donation.png" alt="Blood Donation" />
        </div>
      </section>

      {/* Gift of Life Section */}
      <section className="lc-gift">
        <div className="lc-gift-content">
          <div className="lc-gift-text">
            <h3>Bridging the Gap Between Hope and Help</h3>
            <p>
              Give blood, ignite a life! Be the light in someone&apos;s dark. A single
              drop can create a ripple of hope, your kindness today saves a
              heartbeat tomorrow.
            </p>
            <div className="lc-cta-buttons">
              <a href="/donor/generate-request" className="lc-cta-btn">Request a Blood</a>
              <a href="/find-donors" className="lc-cta-btn">Find a Donor</a>
              <a href="/donor/register" className="lc-cta-btn">Join as a Donor</a>
            </div>
          </div>
          <div className="lc-gift-image">
            <img
              src="/images/index/hand-holding-a-drop-of-blood.png"
              alt="Gift of Life"
            />
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="lc-stats">
        <div className="lc-stat-item">
          <i className="fas fa-hands-helping" />
          <p><strong>100+</strong><br /><span>Volunteers</span></p>
        </div>
        <div className="lc-stat-item">
          <i className="fas fa-users" />
          <p><strong>500+</strong><br /><span>Members</span></p>
        </div>
        <div className="lc-stat-item">
          <i className="fas fa-chart-line" />
          <p><strong>1000+</strong><br /><span>Total Served</span></p>
        </div>
      </section>

      {/* Footer */}
      <footer className="lc-footer">
        <div className="lc-footer-content">
          <div className="lc-footer-left">
            <div className="lc-footer-logo">
              <img src="/images/index/LifeConnect_mini_logo.png" alt="Mini Logo" />
              <h2>Life Connect</h2>
            </div>
            <p className="lc-footer-about">
              <strong>Life Connect</strong> is a web app developed by the{" "}
              <strong>YRC team</strong> of{" "}
              <strong>Velammal Engineering College</strong> to connect blood
              donors and recipients seamlessly. It streamlines request
              generation, donor matching, and communication, ensuring a safe,
              transparent, and efficient donation process.
            </p>
            <div className="lc-footer-partner-logos">
              <a href="https://velammal.edu.in/" target="_blank" rel="noreferrer">
                <img src="/images/index/yrc_logo.png" alt="YRC Logo" />
              </a>
              <a href="https://velammal.edu.in/" target="_blank" rel="noreferrer">
                <img src="/images/index/vec_logo.png" alt="Velammal Engineering College" />
              </a>
            </div>
          </div>

          <div className="lc-footer-right">
            <h4>Contact</h4>
            <div className="lc-footer-contact">
              <a href="tel:+919150450401">
                <i className="fas fa-phone" /> +91 9150450401
              </a>
              <a href="mailto:yrclifeconnect@gmail.com">
                <i className="fas fa-envelope" /> yrclifeconnect@gmail.com
              </a>
            </div>
            <h4>Follow us on:</h4>
            <div className="lc-social-icons">
              <a href="https://www.instagram.com/yrc_vec" target="Instagram" rel="noreferrer">
                <i className="fab fa-instagram" />
              </a>
              <a href="https://www.youtube.com/@YouthRedCrossVEC" target="Youtube" rel="noreferrer">
                <i className="fab fa-youtube" />
              </a>
            </div>
          </div>
        </div>
        <div className="lc-footer-bottom">
          © {new Date().getFullYear()} Life Connect · Youth Red Cross, Velammal Engineering College
        </div>
      </footer>
    </>
  );
}
