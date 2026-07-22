import { useState } from "react";

function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="flex justify-between items-center bg-white shadow w-full p-0">
        <a href="/" className="flex items-center gap-2 text-red-700 font-bold">
          <img
            src="/images/index/LifeConnect_Logo.png"
            alt="Logo"
            className="w-12"
          />
          Life Connect
        </a>

        <button
          className="md:hidden text-2xl"
          onClick={() => setOpen(!open)}
        >
          ☰
        </button>

        <nav
          className={`fixed md:static top-0 right-0 h-full md:h-auto w-64 md:w-auto bg-white md:bg-transparent transform ${
            open ? "translate-x-0" : "translate-x-full"
          } md:translate-x-0 transition p-6 md:p-0`}
        >
          <ul className="flex flex-col md:flex-row gap-6 font-semibold">
            <NavLink href="/queries" />
            <NavLink href="/about" />
            <NavLink href="/admin/login" />
            <NavLink href="/donor/login" />
            <NavLink href="/blood-banks" />
          </ul>
        </nav>
    </header>
  );
}

function NavLink({ href }) {
  return (
    <li>
      <a href={href} className="hover:text-red-700">
        {href.replace("/", "").replace("-", " ")}
      </a>
    </li>
  );
}

export default Header