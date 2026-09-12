# LifeConnect - Youth Red Cross Blood Donation Platform

Welcome to **LifeConnect**! This platform was built by the Youth Red Cross (YRC) at Velammal Engineering College to streamline blood donation services and foster a community of active blood donors. Our mission is to make it easy for people in need to find blood donors quickly, while also promoting safe and efficient blood donation practices across our community.

## About LifeConnect

LifeConnect is a modern, full-stack web application designed to bring blood donors and recipients together in one place. It is a dedicated resource for those in need of blood, simplifying the donation process with user-friendly features and reliable information. We prioritize safety, transparency, and quick communication to connect blood requests with verified, willing donors.

## Tech Stack

LifeConnect has been completely rewritten into a modern split-stack architecture:
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy (Async), Alembic, Pydantic, Passlib (bcrypt), JOSE (JWT)
- **Frontend**: React, Vite, React Router, Recharts
- **Database**: PostgreSQL (Production) / SQLite (Development)

## Features

- **Request Blood Donations**: Users can submit blood requests that are then reviewed and matched with eligible donors based on blood type and location.
- **Donor Management**: Active and willing donors can register with our platform to be notified of relevant blood donation opportunities.
- **Admin Dashboard**: Comprehensive analytics and metrics powered by Recharts, allowing admins to track donations and system health.
- **Request Approval and Tracking**: Admins review each request and coordinate directly with hospitals and recipients, ensuring a smooth and timely process.
- **Secure Authentication**: JWT-based authentication with role-based access control (RBAC) separating Admin and Donor privileges. (Invited-only Admins).
- **Hospital Management**: Maintain a registry of partner hospitals to quickly associate blood requests.

## Getting Started

See the setup guide at `docs/setup.md` for detailed instructions on how to run this project locally.

## About the Youth Red Cross (YRC)

The Youth Red Cross (YRC) is a humanitarian organization that encourages students to engage in community service and health initiatives. Through LifeConnect, YRC promotes the value of voluntary blood donation as a life-saving resource and raises awareness about the significance of a connected and compassionate society.

---

**Built by the Youth Red Cross team at Velammal Engineering College. Together, let's make a difference!**

**Contact Us**  
📞 Phone: 9150450401  
📧 Email: yrcveclifeconnect@gmail.com
