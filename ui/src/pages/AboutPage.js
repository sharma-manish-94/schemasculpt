import React from 'react';
import { Link } from 'react-router-dom';
import './AboutPage.css';

function AboutPage() {
    return (
        <div className="about-page-container">
            <div className="about-content">
                <h1>About SchemaSculpt</h1>
                <p>
                    SchemaSculpt began as a personal project to solve a common frustration in API development and Integration: managing complex and often messy OpenAPI specifications. The goal was to create more than just a validator—a true intelligent assistant that helps developers design, test, and perfect their APIs with less effort.
                </p>
                <p>
                    This application is built with a modern, full-stack architecture, leveraging the power of local Large Language Models (LLMs) to provide a private, cost-effective, and powerful development experience.
                </p>

                <h2>About the Creator</h2>
                <p>
                    Hi, I'm Manish Sharma, a software engineer passionate about building tools that improve developer workflows. You can find more of my work on my GitHub profile.
                </p>

                <Link to="/" className="back-link">← Back to the Editor</Link>
            </div>
        </div>
    );
}

export default AboutPage;