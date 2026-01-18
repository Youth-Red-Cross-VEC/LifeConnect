function Footer() {
  return (
    <footer className="bg-gray-900 text-white w-full p-0">
      <div className="mx-auto flex flex-col md:flex-row gap-10">
        <div className="md:w-2/3">
          <div className="flex items-center gap-2 mb-4">
            <img
              src="/images/index/LifeConnect_mini_logo.png"
              alt="Logo"
              className="w-10"
            />
            <h2 className="text-xl font-bold">Life Connect</h2>
          </div>

          <p className="text-gray-300">
            Life Connect is developed by the YRC team of Velammal Engineering
            College to seamlessly connect blood donors and recipients.
          </p>
        </div>

        <div>
          <h4 className="font-semibold mb-3">Contact</h4>
          <p>📞 +91 9150450401</p>
          <p>✉️ yrclifeconnect@gmail.com</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer