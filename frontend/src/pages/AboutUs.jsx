
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const AboutUs = () => {
  const navigate = useNavigate()
  const [navOpen, setNavOpen] = useState(false)
  const [slide1, setSlide1] = useState(0)

const nextSlide1 = () => {
  setSlide1((prev) => (prev + 1) % 3)
}

const prevSlide1 = () => {
  setSlide1((prev) => (prev - 1 + 3) % 3)
}
const [slide2, setSlide2] = useState(0)

const nextSlide2 = () => {
  setSlide2((prev) => (prev + 1) % 3)
}

const prevSlide2 = () => {
  setSlide2((prev) => (prev - 1 + 3) % 3)
}
React.useEffect(() => {

  const sections = document.querySelectorAll(".section")

  const observer = new IntersectionObserver(
    (entries, observer) => {

      entries.forEach((entry) => {

        if (entry.isIntersecting) {

          entry.target.classList.add("fade-in")

          observer.unobserve(entry.target)

        }

      })

    },
    { threshold: 0.1 }
  )

  sections.forEach((section) => {

    observer.observe(section)

  })

}, [])
  return (
    <div>
      {/* internal css  */}
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
        cursor: pointer;
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
        cursor: pointer;
      }

      .lc-nav-links a:hover { color: #8b0000; }

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

      @media (max-width: 768px) {
        .lc-nav-toggle { display: block; }
        .lc-footer { padding: 32px 24px 20px; }
      }
      body {
        font-family: "Poppins", sans-serif;
        margin: 0;
        padding: 0;
        background-color: #e7dfe2;
      }

      /* Header Styles */
      header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background: linear-gradient(90deg, #d32f2f, #b71c1c);
        color: white;
      }

      .header-logo {
        display: flex;
        align-items: center;
      }

      .header-logo img {
        width: 100px;
        height: 80px;
        margin-right: 1rem;
        border-radius: 50px;
      }

      .header-logo h1 {
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
      }

      .header-logo p {
        font-size: 1rem;
        margin: 0;
        font-style: italic;
      }

      .header-btn {
        text-decoration: none;
        color: white;
        background: white;
        color: #b71c1c;
        padding: 0.7rem 1.5rem;
        border-radius: 20px;
        font-size: 1rem;
        font-weight: bold;
        transition: background 0.3s ease, color 0.3s ease;
        margin-left: 15px;
      }

      .header-btn:hover {
        background: #0d0e0d;
        color: white;
      }
      .header-buttons{
  display: flex;
  gap: 15px;
}
      /*About Section Styles */
      .about-us {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #fff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 5px 8px rgba(0, 0, 0, 0.1);
        margin-top: 40px;
      }

      .about-us h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 1rem;
      }

      .about-content {
        display: flex;
        flex-wrap: wrap;
        gap: 1.1rem;
        align-items: center;
      }

      .about-text {
        flex: 1;
        font-family: "Open Sans", sans-serif;
        font-size: 1.2rem;
        line-height: 1.8;
        color: #333;
      }

      .about-text strong {
        color: #c62828;
      }

      /* Carousel Styles */
      .image-carousel {
            position: relative;
            width: 100%;
            height: 300px;
            overflow: hidden;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            margin-top: 1rem;
        }

        .carousel-images {
            display: flex;
            width: 300%; /* 3 images, each taking 100% of the container */
            height: 100%;
            transition: transform 0.5s ease-in-out;
        }

        .carousel-images img {
            width: 33.33%;
            height: 100%;
            object-fit: cover;
            flex-shrink: 0;
        }
      
      /* Media Queries for Mobile View */
      @media (max-width: 768px) {
            .about-content {
                flex-direction: column;
            }

            .image-carousel {
                height: 300px;
            }

            .carousel-images img {
                width: 33.33%;
                height: 100%;
            }
        }
        @media (min-width: 1024px) {
          .image-carousel {
              height: 300px; /* Adjust the height */
              width: 60%;    /* Adjust the width */
              margin: 0 auto; /* Center align the carousel */
          }

          .carousel-images img {
            width: 33.33%; /* Divide equally for 3 images */
            height: 100%;  /* Fit within the carousel height */
            object-fit: cover; /* Maintain aspect ratio */
          }
        }
        /* Arrows for Navigation */
        .prev, .next {
            position: absolute;
            top: 50%;
            transform: translateY(-30%);
            font-size: 2rem;
            color: white;
            background: rgba(156, 3, 3, 0.5);
            border-radius:12px;
            padding: 0.4rem;
            cursor: pointer;
            z-index: 10;
        }

        .prev {
            left: 10px;
        }

        .next {
            right: 10px;
        }
      
      /* Youth Red Cross Section Styles */
      .yrc-section {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #fff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .yrc-section h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 1rem;
      }

      .yrc-content {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: center;
      }

      .yrc-text {
        flex: 1;
        font-family: "Open Sans", sans-serif;
        font-size: 1.2rem;
        line-height: 1.5;
        color: #333;
      }

      .yrc-text strong {
        color: #c62828;
      }

      .yrc-image {
        flex: 1;
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
      }

      .yrc-image img {
        width: 100%;
        height: auto;
        object-fit: cover;
      }

      .process-section {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #ffffff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .process-section h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2rem;
        margin-bottom: 2rem;
      }

      .process-step {
        display: flex;
        flex-wrap: wrap;
        gap: 2rem;
        margin-bottom: 2rem;
        background: #ffffff;
        border-left: 6px solid #c62828;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
      }

      .process-step:hover {
        transform: scale(1.03);
      }

      .process-step::before {
        content: attr(data-step);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 50px;
        height: 50px;
        background: #c62828;
        color: #ffffff;
        border-radius: 50%;
        font-size: 1.2rem;
        font-weight: bold;
        margin-right: 1rem;
      }

      .process-text {
        flex: 1;
        font-family: "Open Sans", sans-serif;
        font-size: 1.1rem;
        line-height: 1.7;
        color: #333;
      }

      .process-text h3 {
        color: #d32f2f;
        font-size: 1.8rem;
        margin-bottom: 1rem;
      }

      .process-image {
        flex: 1;
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
      }

      .process-image img {
        width: 100%;
        height: auto;
        object-fit: cover;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
      }

      .process-image img:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
      }

      .process-step:nth-child(even) .process-text {
        order: 1;
      }

      .process-step:nth-child(even) .process-image {
        order: 2;
      }

      .process-step:nth-child(odd) .process-text {
        order: 2;
      }

      .process-step:nth-child(odd) .process-image {
        order: 1;
      }

      @media (max-width: 768px) {
        .process-step {
          flex-direction: column;
          align-items: center;
        }

        .process-text,
        .process-image {
          flex: none;
          max-width: 100%;
        }

        .process-text h3 {
          font-size: 1.5rem;
        }

        .process-text p {
          font-size: 1rem;
        }
      }

      /* LifeConnect Actions Section Styles */
      .actions-section {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #fff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .actions-section h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 2rem;
      }

      .action-step {
        text-align: center;
        margin-bottom: 2rem;
      }

      .button {
        display: inline-block;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-family: "Open Sans", sans-serif;
        text-align: center;
        background-color: #c62828;
        color: white;
        border-radius: 12px;
        text-decoration: none;
        margin: 10px 0;
        transition: background-color 0.3s, transform 0.2s ease-in-out;
      }

      .square-button {
        display: inline-block;
        width: 200px;
      }

      .button:hover {
        background-color: #0a0909;
        transform: scale(1.1);
      }

      .button-description {
        font-size: 0.9rem;
        color: #555;
        margin-top: 0.5rem;
      }

      @media (max-width: 768px) {
        .square-button {
          width: 150px;
        }
      }

      /* LifeConnect Vision and Mission Section Styles */
      .vision-mission-section {
        padding: 2rem 1rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #fff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .vision-mission-section h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
      }

      .vision-mission-step {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-bottom: 2rem;
        align-items: center;
        justify-content: center;
      }

      .vision-mission-text {
        flex: 1;
        font-family: "Open Sans", sans-serif;
        font-size: 1.2rem;
        line-height: 1.8;
        color: #333;
      }

      .vision-mission-text h3 {
        color: #c62828;
        font-size: 2rem;
        margin-bottom: 1.5rem;
        font-weight: bold;
      }

      .vision-mission-text p {
        color: #555;
        margin-bottom: 1.5rem;
        font-size: 1.1rem;
      }

      .vision-mission-image {
        flex: 1;
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        overflow: hidden;
      }

      .vision-mission-image img {
        width: 100%;
        height: auto;
        object-fit: cover;
        transition: transform 0.3s ease-in-out;
      }

      .vision-mission-image img:hover {
        transform: scale(1.05);
      }

      /* Media query for responsiveness */
      @media (max-width: 768px) {
        .vision-mission-step {
          flex-direction: column;
          text-align: center;
        }

        .vision-mission-image,
        .vision-mission-text {
          width: 100%;
        }

        .vision-mission-text h3 {
          font-size: 1.8rem;
        }

        .vision-mission-text p {
          font-size: 1rem;
        }
      }

      /* Donors and Donations Graph Section Styles */
      .graphs-section {
        padding: 4rem 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #fff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .graphs-section h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 3rem;
        text-transform: uppercase;
        letter-spacing: 1px;
      }

      .graph-step {
        display: flex;
        flex-wrap: wrap;
        gap: 2rem;
        margin-bottom: 3rem;
        align-items: center;
        justify-content: center;
      }

      .graph-text {
        flex: 1;
        font-family: "Open Sans", sans-serif;
        font-size: 1.2rem;
        line-height: 1.8;
        color: #333;
      }

      .graph-text h3 {
        color: #c62828;
        font-size: 2rem;
        margin-bottom: 1.5rem;
        font-weight: bold;
      }

      .graph-text p {
        color: #555;
        margin-bottom: 1.5rem;
        font-size: 1.1rem;
      }

      .graph-image {
        flex: 1;
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        overflow: hidden;
      }

      .graph-image img {
        width: 100%;
        height: auto;
        object-fit: cover;
        transition: transform 0.3s ease-in-out;
      }

      .graph-image img:hover {
        transform: scale(1.05);
      }

      /* Media query for responsiveness */
      @media (max-width: 768px) {
        .graph-step {
          flex-direction: column;
          text-align: center;
        }

        .graph-image,
        .graph-text {
          width: 100%;
        }

        .graph-text h3 {
          font-size: 1.8rem;
        }

        .graph-text p {
          font-size: 1rem;
        }
      }

      /* Blood Donation Importance Section Styles */
      .blood-donation-importance {
        padding: 4rem 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #f4f7fb, #e8f0f4);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .blood-donation-importance h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
      }

      .importance-text {
        font-family: "Open Sans", sans-serif;
        font-size: 1.2rem;
        color: #333;
        line-height: 1.8;
        margin-bottom: 2rem;
      }

      .benefits-text h3 {
        font-family: "Poppins", sans-serif;
        font-size: 1.2rem;
        color: #c62828;
        margin-bottom: 1.5rem;
        font-weight: bold;
      }

      .benefits-text ul {
        list-style: none;
        padding: 0;
      }

      .benefits-text li {
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 1rem;
      }

      .quotes-section {
        margin-top: 3rem;
        display: flex;
        flex-direction: column;
        align-items: center;
      }

      .quote {
        margin-bottom: 2rem;
        font-family: "Georgia", serif;
        font-size: 1.5rem;
        font-style: italic;
        color: #666;
        text-align: center;
        border-left: 5px solid #c62828;
        padding: 1rem;
        width: 70%;
        transition: transform 0.3s ease;
      }

      .quote:hover {
        transform: scale(1.05);
      }

      .quote blockquote {
        margin: 0;
      }

      .quote strong {
        display: block;
        margin-top: 0.5rem;
        font-size: 1rem;
        font-weight: bold;
        color: #c62828;
      }

      /* Zig-zag effect */
      .quote:nth-child(odd) {
        align-self: flex-start;
        text-align: left;
        border-left-color: #2e7d32;
        background-color: #f9f9f9;
        box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
      }

      .quote:nth-child(even) {
        align-self: flex-end;
        text-align: right;
        border-right: 5px solid #c62828;
        border-left: none;
        background-color: #fff3e0;
        box-shadow: -2px 2px 8px rgba(0, 0, 0, 0.1);
      }

      .quote:nth-child(even) blockquote {
        padding-right: 1rem;
      }

      .quote:nth-child(odd) blockquote {
        padding-left: 1rem;
      }

      /* Responsive Design */
      @media (max-width: 768px) {
        .quote {
          width: 90%;
          font-size: 1.2rem;
          text-align: center !important;
          align-self: center !important;
          border-left: 5px solid #c62828;
          border-right: none;
        }

        .quote:nth-child(even) {
          background-color: #f9f9f9;
        }
      }

      /* Meet the Team Section */
      .meet-the-team {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #fff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .meet-the-team h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 2rem;
      }

      .team-members,
      .admin-members {
        display: flex;
        flex-wrap: wrap;
        gap: 2rem;
        justify-content: center;
      }

      .team-member,
      .admin-member {
        flex: 1 1 200px;
        max-width: 300px;
        min-height: 520px;
        margin-bottom: 2rem;
        background-color: #fff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        text-align: center;
      }

      .member-img {
        width: 200px;
        height: 200px;
        object-fit: cover;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 1rem;
      }

      .member-info h3 {
        color: #c62828;
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
      }

      .role {
        font-size: 1.2rem;
        margin-bottom: 1rem;
        color: #555;
      }

      .social-media {
        display: flex;
        justify-content: center;
        gap: 1rem;
      }

      .social-btn {
        text-decoration: none;
        color: #fff;
        padding: 0.5rem 1rem;
        border-radius: 30px;
        font-size: 1rem;
      }

      .social-btn:hover {
        opacity: 0.5;
      }

      /* General Section Spacing */
      .section {
        margin-bottom: 3rem;
      }

      /* LifeConnect Process Section */
      .process-section {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #fff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 4rem;
      }

      .process-section h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 2rem;
      }

      .vision-mission-section {
        padding: 2rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 4rem;
      }

      .meet-the-team {
        padding: 4rem 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #fff, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 4rem;
      }

      .meet-the-team h2 {
        text-align: center;
        font-family: "Poppins", sans-serif;
        color: #c62828;
        font-size: 2.5rem;
        margin-bottom: 2rem;
      }

      .admin-section {
        padding: 2rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 4rem;
      }

      .other-section {
        padding: 2rem;
        background: #fff;
        margin-bottom: 4rem;
      }

      footer {
        background-color: #d32f2f; /* Red background */
        color: #ffffff; /* White text */
        padding: 10px 0;
        border-top: 3px solid #b71c1c; /* Darker red border for contrast */
        font-family: Arial, sans-serif;
      }

      .footer-content {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 20px;
      }

      .footer-text p {
        font-size: 18px;
        font-weight: bold;
        line-height: 1.8;
      }

      .footer-contact h3 {
        font-size: 20px;
        margin-bottom: 10px;
        color: #ffffff; /* White for headings */
        text-transform: uppercase;
      }

      .footer-contact p {
        font-size: 16px;
        margin: 5px 0;
      }

      .footer-contact i {
        margin-right: 10px;
        color: #ffffff; /* White icon color */
      }

      .footer-btn {
        display: inline-block;
        padding: 10px 20px;
        margin-top: 10px;
        font-size: 16px;
        color: #d32f2f; /* Red text for contrast */
        background-color: #ffffff; /* White button background */
        border: none;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        transition: background-color 0.3s ease, color 0.3s ease;
      }

      .footer-btn:hover {
        background-color: #0e0d0d; /* Darker red on hover */
        color: #ffffff; /* White text on hover */
      }

      @media screen and (max-width: 768px) {
        .footer-content {
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .footer-contact {
          margin-top: 20px;
        }
      }
      /* Animation Styles */
      .hidden {
        opacity: 0;
        transform: translateY(20px);
      }

      .fade-in {
        opacity: 1;
        transform: translateY(0);
        transition: opacity 0.9s ease, transform 0.9s ease;
      }

      @media (max-width: 768px) {
        body {
          font-size: 14px; /* Adjust font size for smaller screens */
        }
        .container {
          padding: 10px; /* Reduce padding */
        }
      }

      /* General Mobile Adjustments */
@media (max-width: 768px) {
  header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 1rem;
  }

  .header-logo {
    flex-direction: column;
    align-items: center;
    margin-bottom: 1rem;
  }

  .header-logo img {
    width: 60px; /* Smaller logo size for mobile */
    height: 50px;
    margin: 0;
  }

  .header-logo h1 {
    font-size: 1.2rem; /* Smaller text for mobile */
  }

  .header-logo p {
    font-size: 0.8rem; /* Smaller text for mobile */
  }

  .header-btn {
    padding: 0.5rem 1rem; /* Smaller button padding */
    font-size: 0.9rem;
    
  }


  .about-content {
    flex-direction: column;
    gap: 1rem;
  }

  .about-text {
    font-size: 1rem;
  }

  .image-carousel {
    height: 200px;
  }

  .yrc-content, .vision-mission-step, .graph-step {
    flex-direction: column;
    text-align: center;
  }

  .yrc-image img,
  .vision-mission-image img,
  .graph-image img {
    width: 100%;
    height: auto;
  }

  .process-step {
    flex-direction: column;
    align-items: center;
  }

  .process-text {
    font-size: 1rem;
    text-align: center;
  }

  .meet-the-team .team-member,
  .admin-members .admin-member {
    max-width: 100%;
    margin-bottom: 1rem;
  }

  footer {
    text-align: center;
  }

  .footer-content {
    flex-direction: column;
    gap: 1rem;
  }
}

/* Smaller Devices (e.g., phones) */
@media (max-width: 480px) {
  body {
    font-size: 12px;
  }

  header h1 {
    font-size: 1.2rem;
  }

  .about-text {
    font-size: 0.9rem;
  }

  .button {
    font-size: 0.9rem;
    padding: 0.7rem 1rem;
  }

  .square-button {
    width: 120px;
  }

  .footer-contact h3, .footer-contact p {
    font-size: 14px;
  }

  .footer-btn {
    font-size: 14px;
    padding: 8px 16px;
  }
}

/* Adjust carousel image size for desktop */
@media (min-width: 769px) {
  .image-carousel {
    height: 300px;
    width:50%;
    margin:0 auto; /* Reduced height for desktop */
  }

  .carousel-images img {
    width: 33.33%; /* Maintain the same width */
    height: 100%;
    object-fit: cover;
    
  }
}

/* Maintain current style for mobile */
@media (max-width: 768px) {
  .image-carousel {
    height: 200px; /* Keep mobile size */
  }
}
`}</style>
{/* Header */}
<header className="lc-header">
  <div className="lc-logo" onClick={() => navigate('/')}>
    <img src="/images/aboutus/LifeConnect_Logo.png" alt="LifeConnect Logo" />
    Life Connect
  </div>

  <button
    className="lc-nav-toggle"
    onClick={() => setNavOpen(!navOpen)}
    aria-label="Toggle navigation"
  >
    ☰
  </button>

  <nav>
    <ul className="lc-nav-links" style={{ display: navOpen ? 'flex' : undefined }}>
      <li><a onClick={() => navigate('/donor/query')}>Queries</a></li>
      <li><a onClick={() => navigate('/about')}>About Us</a></li>
      <li><a onClick={() => navigate('/admin/login')}>Admin Login</a></li>
      <li><a onClick={() => navigate('/donor/login')}>Donor Login</a></li>
      <li><a onClick={() => navigate('/blood-banks')}>Blood Bank</a></li>
    </ul>
  </nav>

  {navOpen && (
    <div
      style={{ position: 'fixed', inset: 0, zIndex: 150, background: 'rgba(0,0,0,0.3)' }}
      onClick={() => setNavOpen(false)}
    />
  )}
</header>
{/* About Section */}
<div className="section about-us">

  <h2>Who We Are</h2>

  <div className="about-content">

    {/* Text Section */}
    <div className="about-text">

      <p>
        At <strong>LifeConnect</strong>, we strive to make life-saving blood
        donations accessible to everyone. Our platform bridges the gap
        between blood donors and recipients, ensuring timely assistance for
        those in need.
      </p>

      <p>
        We are a dedicated team of individuals working under the guidance of
        the Youth Red Cross. Our major focus is to create a seamless
        experience for managing blood requests, validating donor details,
        and facilitating connections between hospitals, donors, and
        recipients.
      </p>

      <p>
        With thousands of lives impacted, we aim to create a system where no
        one has to wait for a life-saving donation. From connecting donors
        to validating requests, every aspect of our work is driven by
        empathy, precision, and transparency.
      </p>

    </div>

    {/* Image Carousel */}
    <div className="image-carousel carousel1">

      <div
  className="carousel-images"
  style={{ transform: `translateX(-${slide1 * 33.33}%)` }}
>

        <img
          src="/images/aboutus/teamcollab.jpg"
          alt="Team Collaboration"
        />

        <img
          src="/images/aboutus/donorhelping.jpg"
          alt="Donor Helping"
        />

        <img
          src="/images/aboutus/hospitalsupport.jpg"
          alt="Hospital Support"
        />

      </div>

      {/* Arrows for mobile view */}
      <span className="prev" onClick={prevSlide1}>
        &#10094;
      </span>

      <span className="next" onClick={nextSlide1}>
        &#10095;
      </span>

    </div>

  </div>

</div>

{/* Youth Red Cross Section */}
<div className="section yrc-section">

  <h2>About Youth Red Cross</h2>

  <div className="yrc-content">

    {/* Text Section */}
    <div className="yrc-text">

      <p>
        The <strong>Youth Red Cross (YRC)</strong> is a global humanitarian
        organization that focuses on improving the well-being of
        communities, particularly in times of need. It is made up of young
        volunteers who are dedicated to supporting blood donation drives,
        health initiatives, and disaster relief efforts.
      </p>

      <p>
        At LifeConnect, we are proud to be working under the guidance of the
        Youth Red Cross. Their leadership, expertise, and dedication to
        social welfare have been instrumental in creating a platform that
        ensures timely blood donations.
      </p>

      <p>
        LifeConnect, guided by the YRC, ensures timely blood donations and
        supports our mission to connect donors with recipients.
      </p>

    </div>

    {/* Image Carousel */}
    <div className="image-carousel carousel2">

      <div
  className="carousel-images"
  style={{ transform: `translateX(-${slide2 * 33.33}%)` }}
>

        <img
          src="/images/aboutus/yrc volun1.jpg"
          alt="YRC volunteers"
        />

        <img
          src="/images/aboutus/yrc volun2.jpg"
          alt="YRC volunteers"
        />

        <img
          src="/images/aboutus/yrc volun3.jpg"
          alt="YRC volunteers"
        />

      </div>

      <span className="prev" onClick={prevSlide2}>
        &#10094;
      </span>

      <span className="next" onClick={nextSlide2}>
        &#10095;
      </span>

    </div>

  </div>

</div>
{/* LifeConnect Process Section */}
<div className="section process-section">

  <h2>How It Works</h2>

  {/* Step 1 */}
  <div className="process-step" data-step="1">

    <div className="process-image">
      <img
        src="/images/aboutus/finddonorimg.png"
        alt="Find a Donor"
      />
    </div>

    <div className="process-text">
      <h3>Find a Donor</h3>

      <p>
        The process begins with the recipient or hospital searching for
        available blood donors. The user can input their required blood
        group and specify the hospital's address to find the nearest
        available donors who match the blood type. This search functionality
            ensures that blood donors are easy to find based on proximity,
            improving the efficiency of blood donations in critical situations.
      </p>
    </div>

  </div>

  {/* Step 2 */}
  <div className="process-step" data-step="2">

    <div className="process-text">
      <h3>Fill the Request Form</h3>

      <p>
        Once the recipient or hospital identifies an available donor,
        they can fill out a simple form providing essential details such as
            contact information, blood group, hospital address, and additional
            requirements. This form ensures that all relevant information is
            collected for the next stage of the process. The form submission is
            then sent for administrative review.
      </p>
    </div>

    <div className="process-image">
      <img
        src="/images/aboutus/fillreqimg.jpg"
        alt="Fill Request Form"
      />
    </div>

  </div>

  {/* Step 3 */}
  <div className="process-step" data-step="3">

    <div className="process-image">
      <img
        src="/images/aboutus/admin valid img.jpg"
        alt="Admin Validation"
      />
    </div>

    <div className="process-text">
      <h3>Admin Validation and Approval</h3>

      <p>
        After receiving the request form, the admin reviews all the
        details to ensure accuracy and verify that the donor is eligible  and
            available. The admin checks the donor’s status, availability, and
            any required criteria to confirm that the request can be processed.
            Once the verification is complete, the admin approves the request,
            ensuring a smooth transition to the next step.
      </p>
    </div>

  </div>

  {/* Step 4 */}
  <div className="process-step" data-step="4">

    <div className="process-text">
      <h3>Send Notifications to Available Donors</h3>

      <p>
        Upon approval, the admin sends notifications to all available
        donors who match the blood group requested.These notifications inform the
            donors about the blood donation request, providing them with details
            about the hospital and the recipient’s needs. The notification is
            sent through the platform, ensuring donors are alerted in a timely
            manner, and can act quickly.
      </p>
    </div>

    <div className="process-image">
      <img
        src="/images/aboutus/notific.avif"
        alt="Send Notification"
      />
    </div>

  </div>

  {/* Step 5 */}
  <div className="process-step" data-step="5">

    <div className="process-image">
      <img
        src="/images/aboutus/hospitalsupp.jpg"
        alt="Donors Contact the Hospital"
      />
    </div>

    <div className="process-text">
      <h3>Donors Contact the Hospital</h3>

      <p>
        Once the notification is received, the donors reach out directly
        to the hospital or recipient to arrange the donation. Donors can
            confirm their availability and schedule the donation process at the
            specified hospital. This step ensures that the donor and recipient
            can connect seamlessly and that the blood donation can take place
            efficiently.
      </p>
    </div>

  </div>

</div>
{/* LifeConnect Actions Section */}
<div
  className="section actions-section"
  style={{
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "2rem",
    flexWrap: "wrap",
  }}
>

  {/* Left Animation */}
  <div
    id="lottie-animation-left"
    style={{
      flexShrink: 0,
      width: "300px",
      height: "400px",
    }}
  ></div>

  {/* Content Section */}
  <div
    style={{
      flexGrow: 1,
      textAlign: "center",
      maxWidth: "400px",
    }}
  >

    <h2>Take Action</h2>

    {/* Button 1 */}
    <div className="action-step">

      <a
        href="/find-donors"
        className="button square-button"
      >
        Look for Donors
      </a>

      <p className="button-description">
        Click here to search for available blood donors based on your needs.
      </p>

    </div>

    {/* Button 2 */}
    <div className="action-step">

      <a
        href="/donor/generate-request"
        className="button square-button"
      >
        Generate a Request
      </a>

      <p className="button-description">
        Click here to create a blood request for your requirements.
      </p>

    </div>

  </div>

  {/* Right Animation */}
  <div
    id="lottie-animation-right"
    style={{
      flexShrink: 0,
      width: "300px",
      height: "400px",
    }}
  ></div>

</div>

{/* LifeConnect Vision and Mission Section */}
<div className="section vision-mission-section">

  <h2>Our Vision and Mission</h2>

  {/* Vision Section */}
  <div className="vision-mission-step">

    <div className="vision-mission-image">

      <img
        src="/images/aboutus/vision.jpg"
        alt="Our Vision"
      />

    </div>

    <div className="vision-mission-text">

      <h3>
      Our Vision: A Future Where No One is Left Behind
      </h3>

      <p>
        At LifeConnect, we envision a future where blood donation is not
        just a service, but a movement.A world where individuals across all
            communities come together to support each other, ensuring that no
            one ever faces a shortage of blood when they need it most. By
            creating a seamless connection between donors and hospitals, we aim
            to make blood donation a regular part of everyday life.
      </p>

      <p>
        Our vision is rooted in the belief that together, we can create a
        compassionate, self-sustaining ecosystem that empowers both donors
            and recipients. With this vision, we hope to redefine healthcare
            collaboration, making it easier for donors to give and for hospitals
            to receive.
      </p>

    </div>

  </div>

{/* Mission Section */}
<div className="vision-mission-step">

  <div className="vision-mission-text">

    <h3>Our Mission: Saving Lives Through Connectivity and Care</h3>

    <p>
      Our mission is simple yet powerful – to connect willing blood donors
      with hospitals in urgent need. By providing an intuitive platform
      that facilitates blood requests, we are committed to removing
      barriers between those who are in need of life-saving blood and
      those who can provide it. Every donation matters, and every step we
      take brings us closer to a world with better health and well-being
      for all.
    </p>

    <p>
      LifeConnect’s mission is driven by technology, compassion, and
      community. We are not just connecting donors with hospitals; we are
      creating a lasting impact on people’s lives. By ensuring timely
      communication, easy navigation, and a constant flow of support, we
      make sure that blood donations are always just a click away.
    </p>

  </div>

  <div className="vision-mission-image">

    <img
      src="/images/aboutus/mission.jpg"
      alt="Our Mission"
    />

  </div>

</div>

</div>

{/* Donors and Donations Graph Section */}
<div className="section graphs-section">

  <h2>Our Impact in Numbers</h2>

  {/* Graph 1 */}
  <div className="graph-step">

    <div className="graph-text">

      <h3>Total Donors</h3>

      <p>
        As of today, LifeConnect has successfully connected thousands of
        individuals who are willing to donate blood. This graph represents
        the growth in the number of registered donors over time,
        highlighting the increasing awareness and participation in this
        life-saving cause.
      </p>

      <p>
        We continue to expand our network of donors, ensuring that we can
        meet the needs of hospitals and recipients across the region. Each
        donor makes a difference, and with every new addition to our
        network, we get closer to a world with zero blood shortages.
      </p>

    </div>

    <div className="graph-image">

      <img
        src="/images/aboutus/totdonorgrp.jpg"
        alt="Total Donors Graph"
      />

    </div>

  </div>

  {/* Graph 2 */}
  <div className="graph-step">

    <div className="graph-image">

      <img
        src="/images/aboutus/totdonationgrp.jpg"
        alt="Total Donations Graph"
      />

    </div>

    <div className="graph-text">

      <h3>Total Donations</h3>

      <p>
        The total donations graph showcases the incredible impact that
        LifeConnect has made by connecting donors with hospitals in need.
        This graph tracks the number of successful donations made through
        our platform, representing the lives saved and the hope provided
        through every donation.
      </p>

      <p>
        With each donation, we get one step closer to building a world where
        everyone has access to the blood they need in critical moments. The
        number of donations continues to rise, reflecting the commitment of
        both donors and hospitals working together for a healthier future.
      </p>

    </div>

  </div>

</div>

{/* Importance of Blood Donation Section */}
<div className="section blood-donation-importance">

  <h2>The Importance of Blood Donation</h2>

  <div className="importance-text">

    <p>
      Blood donation is a life-saving act that goes beyond just giving a
      part of yourself – it’s a gift of life to someone in need. With every
      donation, you become a hero to those who require blood in times of
      critical health conditions, surgeries, accidents, or medical
      treatments.
    </p>

    <p>
      Every year, millions of lives are saved through blood donation. It’s
      the most selfless and simplest act of kindness, which makes a massive
      difference. By donating blood, you are contributing to a community
      that is united in the fight against disease and disaster.
    </p>

  </div>

  <div className="benefits-text">

    <h3>Benefits of Donating Blood</h3>

    <ul>

      <li>
        <strong>Saves Lives:</strong> One donation can help save up to three
        lives.
      </li>

      <li>
        <strong>Improves Health:</strong> Donating blood can reduce the risk
        of certain health conditions such as heart disease and cancer.
      </li>

      <li>
        <strong>Boosts Blood Circulation:</strong> Regular donation
        stimulates the production of new blood cells, improving overall
        circulation.
      </li>

      <li>
        <strong>Gives a Sense of Fulfillment:</strong> Knowing you have
        helped others brings emotional satisfaction and a sense of purpose.
      </li>

      <li>
        <strong>Acts as a Community Bond:</strong> Blood donation creates a
        sense of unity and camaraderie in the community, helping people come
        together for a greater cause.
      </li>

    </ul>

  </div>

  <div className="quotes-section">

    <h3>Words of Wisdom on Blood Donation</h3>

    <div className="quote">
      <blockquote>
        "The best way to find yourself is to lose yourself in the service of
        others." - <strong>Mahatma Gandhi</strong>
      </blockquote>
    </div>

    <div className="quote">
      <blockquote>
        "Donating blood is not just a responsibility, it’s a gift of life.
        It is a simple act that saves a life, and that life could be someone
        you love." - <strong>Unknown</strong>
      </blockquote>
    </div>

    <div className="quote">
      <blockquote>
        "We make a living by what we get, but we make a life by what we
        give." - <strong>Winston Churchill</strong>
      </blockquote>
    </div>

    <div className="quote">
      <blockquote>
        "Every blood donation counts. When you donate, you become a part of
        a life-saving team. One small act can make all the difference." -
        <strong>Unknown</strong>
      </blockquote>
    </div>

  </div>

</div>
{/* Meet the Team Section */}
<div className="section meet-the-team">

  <h2>Meet the Team</h2>

  <div className="team-members">

    {/* Developer 1 */}
    <div className="team-member">

      <img
        src="/images/aboutus/siddharth.jpg"
        alt="Siddharth M"
        className="member-img"
      />

      <div className="member-info">

        <h3>Siddharth M</h3>

        <p className="role">Lead Developer</p>

        <div className="social-media">

          <a
            href="https://instagram.com/siddharth_magesh"
            target="_blank"
            className="social-btn instagram"
          >
            <i
              className="fab fa-instagram"
              style={{ fontSize: "35px", color: "#e4405f" }}
            ></i>
          </a>

          <a
            href="https://github.com/Siddharth-magesh"
            target="_blank"
            className="social-btn github"
          >
            <i
              className="fab fa-github"
              style={{ fontSize: "35px", color: "#333" }}
            ></i>
          </a>

          <a
            href="https://linkedin.com/in/siddharth-magesh-76688a246"
            target="_blank"
            className="social-btn linkedin"
          >
            <i
              className="fab fa-linkedin"
              style={{ fontSize: "35px", color: "#0a66c2" }}
            ></i>
          </a>

        </div>

      </div>

    </div>

    {/* Developer 2 */}
    <div className="team-member">

      <img
        src="/images/aboutus/tarakesh.jpg"
        alt="Tarakeshwaran S"
        className="member-img"
      />

      <div className="member-info">

        <h3>Tarakeshwaran S</h3>

        <p className="role">Backend Developer</p>

        <div className="social-media">

          <a
            href="https://instagram.com/life_of_tarakesh"
            target="_blank"
            className="social-btn instagram"
          >
            <i
              className="fab fa-instagram"
              style={{ fontSize: "35px", color: "#e4405f" }}
            ></i>
          </a>

          <a
            href="https://github.com/Tarakesh-sampath"
            target="_blank"
            className="social-btn github"
          >
            <i
              className="fab fa-github"
              style={{ fontSize: "35px", color: "#333" }}
            ></i>
          </a>

          <a
            href="https://linkedin.com/in/tarakeshwaran-sampath"
            target="_blank"
            className="social-btn linkedin"
          >
            <i
              className="fab fa-linkedin"
              style={{ fontSize: "35px", color: "#0a66c2" }}
            ></i>
          </a>

        </div>

      </div>

    </div>

    {/* Developer 3 */}
    <div className="team-member">

      <img
        src="/images/aboutus/vishvaa.jpg"
        alt="Vishvaa K"
        className="member-img"
      />

      <div className="member-info">

        <h3>Vishvaa K</h3>

        <p className="role">Backend Developer</p>

        <div className="social-media">

          <a
            href="https://instagram.com/_.vishvaa.sh"
            target="_blank"
            className="social-btn instagram"
          >
            <i
              className="fab fa-instagram"
              style={{ fontSize: "35px", color: "#e4405f" }}
            ></i>
          </a>

          <a
            href="https://github.com/vishvaa-vsk"
            target="_blank"
            className="social-btn github"
          >
            <i
              className="fab fa-github"
              style={{ fontSize: "35px", color: "#333" }}
            ></i>
          </a>

          <a
            href="https://linkedin.com/in/vishvaa-k"
            target="_blank"
            className="social-btn linkedin"
          >
            <i
              className="fab fa-linkedin"
              style={{ fontSize: "35px", color: "#0a66c2" }}
            ></i>
          </a>

        </div>

      </div>

    </div>

    {/* Developer 4 */}
    <div className="team-member">

      <img
        src="/images/aboutus/dakshan.jpg"
        alt="Dakshan B"
        className="member-img"
      />

      <div className="member-info">

        <h3>Dakshan B</h3>

        <p className="role">Frontend Developer</p>

        <div className="social-media">

          <a
            href="https://instagram.com/dakshan01_"
            target="_blank"
            className="social-btn instagram"
          >
            <i
              className="fab fa-instagram"
              style={{ fontSize: "35px", color: "#e4405f" }}
            ></i>
          </a>

          <a
            href="https://github.com/Dakshan45"
            target="_blank"
            className="social-btn github"
          >
            <i
              className="fab fa-github"
              style={{ fontSize: "35px", color: "#333" }}
            ></i>
          </a>

          <a
            href="https://linkedin.com/in/dakshan-b-1b9401329"
            target="_blank"
            className="social-btn linkedin"
          >
            <i
              className="fab fa-linkedin"
              style={{ fontSize: "35px", color: "#0a66c2" }}
            ></i>
          </a>

        </div>

      </div>

    </div>

    {/* Developer 5 */}
    <div className="team-member">

      <img
        src="/images/aboutus/andal.jpg"
        alt="Andalpriyadharshini A"
        className="member-img"
      />

      <div className="member-info">

        <h3>Andalpriyadharshini</h3>

        <p className="role">Frontend Developer</p>

        <div className="social-media">

          <a
            href="https://instagram.com/itzmy_steriousgurl"
            target="_blank"
            className="social-btn instagram"
          >
            <i
              className="fab fa-instagram"
              style={{ fontSize: "35px", color: "#e4405f" }}
            ></i>
          </a>

          <a
            href="https://github.com/anspriya"
            target="_blank"
            className="social-btn github"
          >
            <i
              className="fab fa-github"
              style={{ fontSize: "35px", color: "#333" }}
            ></i>
          </a>

          <a
            href="https://linkedin.com/in/andalpriyadharshini-a-b94519297"
            target="_blank"
            className="social-btn linkedin"
          >
            <i
              className="fab fa-linkedin"
              style={{ fontSize: "35px", color: "#0a66c2" }}
            ></i>
          </a>

        </div>

      </div>

    </div>

    {/* Developer 6 */}
    <div className="team-member">

      <img
        src="/images/aboutus/sujhan.jpg"
        alt="Sujhan S"
        className="member-img"
      />

      <div className="member-info">

        <h3>Sujhan S</h3>

        <p className="role">Frontend Developer</p>

        <div className="social-media">

          <a
            href="https://instagram.com/sujh__an"
            target="_blank"
            className="social-btn instagram"
          >
            <i
              className="fab fa-instagram"
              style={{ fontSize: "35px", color: "#e4405f" }}
            ></i>
          </a>

          <a
            href="https://github.com/Sujhan-64"
            target="_blank"
            className="social-btn github"
          >
            <i
              className="fab fa-github"
              style={{ fontSize: "35px", color: "#333" }}
            ></i>
          </a>

          <a
            href="https://linkedin.com/in/sujhan-s-6987han"
            target="_blank"
            className="social-btn linkedin"
          >
            <i
              className="fab fa-linkedin"
              style={{ fontSize: "35px", color: "#0a66c2" }}
            ></i>
          </a>

        </div>

      </div>

    </div>

  </div>

</div>
{/*
<h2>Meet the Admins</h2>

<div className="admin-members">

  <div className="admin-member">

    <img
      src="/images/test2.jpg"
      alt="Ramesh Kumar"
      className="member-img"
    />

    <div className="member-info">

      <h3>Ramesh Kumar</h3>

      <p className="role">YRC Coordinator</p>

      <div className="social-media">

        <a
          href="https://facebook.com/rameshkumar"
          target="_blank"
          className="social-btn facebook"
        >
          <i
            className="fab fa-facebook"
            style={{ fontSize: "35px", color: "#1877f2" }}
          ></i>
        </a>

        <a
          href="https://twitter.com/rameshkumar"
          target="_blank"
          className="social-btn twitter"
        >
          <i
            className="fab fa-twitter"
            style={{ fontSize: "35px", color: "#1da1f2" }}
          ></i>
        </a>

        <a
          href="https://linkedin.com/in/rameshkumar"
          target="_blank"
          className="social-btn linkedin"
        >
          <i
            className="fab fa-linkedin"
            style={{ fontSize: "35px", color: "#0a66c2" }}
          ></i>
        </a>

      </div>

    </div>

  </div>

  <div className="admin-member">

    <img
      src="/images/test2.jpg"
      alt="Satish Kumar"
      className="member-img"
    />

    <div className="member-info">

      <h3>Satish Kumar</h3>

      <p className="role">YRC Head</p>

      <div className="social-media">

        <a
          href="https://facebook.com/satishkumar"
          target="_blank"
          className="social-btn facebook"
        >
          <i
            className="fab fa-facebook"
            style={{ fontSize: "35px", color: "#1877f2" }}
          ></i>
        </a>

        <a
          href="https://twitter.com/satishkumar"
          target="_blank"
          className="social-btn twitter"
        >
          <i
            className="fab fa-twitter"
            style={{ fontSize: "35px", color: "#1da1f2" }}
          ></i>
        </a>

        <a
          href="https://linkedin.com/in/satishkumar"
          target="_blank"
          className="social-btn linkedin"
        >
          <i
            className="fab fa-linkedin"
            style={{ fontSize: "35px", color: "#0a66c2" }}
          ></i>
        </a>

      </div>

    </div>

  </div>

  <div className="admin-member">

    <img
      src="/images/test2.jpg"
      alt="Admin 3"
      className="member-img"
    />

    <div className="member-info">

      <h3>Admin 3</h3>

      <p className="role">Admin Role</p>

      <div className="social-media">

        <a
          href="https://facebook.com/admin3"
          target="_blank"
          className="social-btn facebook"
        >
          <i
            className="fab fa-facebook"
            style={{ fontSize: "35px", color: "#1877f2" }}
          ></i>
        </a>

        <a
          href="https://twitter.com/admin3"
          target="_blank"
          className="social-btn twitter"
        >
          <i
            className="fab fa-twitter"
            style={{ fontSize: "35px", color: "#1da1f2" }}
          ></i>
        </a>

        <a
          href="https://linkedin.com/in/admin3"
          target="_blank"
          className="social-btn linkedin"
        >
          <i
            className="fab fa-linkedin"
            style={{ fontSize: "35px", color: "#0a66c2" }}
          ></i>
        </a>

      </div>

    </div>

  </div>

</div>
*/}

<footer className="lc-footer">
  <div className="lc-footer-content">
    <div className="lc-footer-left">
      <div className="lc-footer-logo">
        <img src="/images/index/LifeConnect_mini_logo.png" alt="Mini Logo" />
        <h2>Life Connect</h2>
      </div>
      <p className="lc-footer-about">
        <strong>Life Connect</strong> is a web app developed by the{' '}
        <strong>YRC team</strong> of{' '}
        <strong>Velammal Engineering College</strong> to connect blood
        donors and recipients seamlessly.
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
        <a href="/donor/query">
          <i className="fas fa-question-circle" /> Submit a Query
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
    </div>
  )
}

export default AboutUs
