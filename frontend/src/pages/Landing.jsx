
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Landing() {
  return (
    <>
      <Header />

      {/* Hero Section */}
      <section className="bg-red-700 text-white flex flex-col md:flex-row items-center justify-between px-6 py-10">
        <div className="relative mb-12 md:mb-0">
          <p className="text-4xl font-light absolute top-29">
            Movement
          </p>
          <p className="text-5xl font-bold absolute top-14">
            Life-Saving
          </p>
          <p className="text-4xl font-light absolute top-0">
            Join the
          </p>
        </div>

        <img
          src="/images/index/blood-donation.png"
          alt="Blood Donation"
          className="w-72 md:w-80"
        />
      </section>

      {/* Gift of Life Section */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-10">
          <div className="md:w-1/2">
            <h3 className="text-2xl font-semibold mb-4">
              Bridging the Gap Between Hope and Help
            </h3>
            <p className="text-gray-700 mb-6">
              Give blood, ignite a life. Be the light in someone&apos;s dark.
              A single drop can create a ripple of hope.
            </p>

            <div className="flex flex-wrap gap-3">
              <CTA href="/request-blood" text="Request Blood" />
              <CTA href="/find-donors" text="Find a Donor" />
              <CTA href="/donor/register" text="Join as a Donor" />
            </div>
          </div>

          <img
            src="/images/index/hand-holding-a-drop-of-blood.png"
            alt="Gift of Life"
            className="w-72"
          />
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-gray-100 py-12 flex justify-evenly text-center">
        <Stat value="100+" label="Volunteers" />
        <Stat value="500+" label="Members" />
        <Stat value="1000+" label="Total Served" />
      </section>

      <Footer />
    </>
  );
}

/* Helper Components */

function CTA({ href, text }) {
  return (
    <a
      href={href}
      className="bg-red-700 text-white px-5 py-2 rounded-xl hover:bg-red-800 transition"
    >
      {text}
    </a>
  );
}

function Stat({ value, label }) {
  return (
    <div>
      <p className="text-2xl font-bold text-red-700">{value}</p>
      <p className="text-gray-600">{label}</p>
    </div>
  );
}
