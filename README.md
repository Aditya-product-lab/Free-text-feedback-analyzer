# Free-text-feedback-analyzer
A Streamlit-based product feedback analysis tool powered by Google Gemini. It automates classifying free-text user feedback into a controlled taxonomy and generates an actionable product-owner summary.

## 1. Overview

Customer feedback is one of the most valuable inputs for product teams. It provides direct insight into customer experiences, unmet needs, product limitations, and opportunities for improvement.

However, as products grow, feedback starts coming from multiple sources and in different formats. Product teams often end up with large spreadsheets containing hundreds or thousands of unstructured customer comments.

Making sense of this feedback manually is time-consuming, difficult to scale, and often inconsistent. More importantly, valuable product insights can get lost in the volume of comments.

**Feedback Analyzer** is a lightweight, AI-powered tool designed to bridge this gap by converting unstructured customer feedback into structured, categorized, and actionable product insights.

The tool allows users to upload an Excel file, identify the column containing customer feedback, and use Google's Gemini API to automatically classify individual responses based on their nature and product impact area. It also generates a consolidated summary to help product teams quickly understand recurring themes, customer pain points, and potential areas of product improvement.

## 2. The Problem We're Solving

Product teams continuously receive feedback such as:

- "The application takes too long to load."
- "I wish there was an option to export reports in PDF."
- "I cannot figure out how to configure my notification settings."

Although each comment provides useful information, the feedback is unstructured.

A Product Owner or Product Manager needs to manually review each response, understand the underlying intent, categorize it, identify the affected product area, and consolidate recurring themes.

## 3. The Proposed Solution (the application)

To get the application up and running do the following: 

**Step 1** - Clone / download the repository (one time process)

**Step 2** - Create a virtual environment Run (on windows, one time process): python -m venv .venv

**Step 3** - Activate the virtual environment (on windows, need to do this every time you run the application locally): .venv\Scripts\Activate.ps1

Note: If you see an execution policy error on Windows, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first

**Step 4** - Install all requirenment from requirenments.txt (on windows, one time process): pip install -r requirements.txt

**Step 5** - Run the application: streamlit run app.py


**Once the tool is running it follows a simple workflow:**

**Step 1 – Upload customer feedback**

Users upload an Excel file containing customer feedback alongside other relevant information.

**Step 2 – Identify the feedback column**

The application examines the column headers and recommends the most likely column containing customer feedback.

The user remains in control and can change the recommended column before proceeding.

**Step 3 – AI-powered feedback classification**

Using Google's Gemini API, the tool analyzes each non-empty feedback response and assigns two classifications.

**Primary Tag – What is the nature of the feedback?**

| Category | Description |
|---|---|
| Bug | Something is broken or not working as expected. |
| Feature request | The customer is requesting an entirely new capability. |
| Enhancements | The customer wants to improve an existing feature. |
| Education | The customer is confused or unclear about how a feature works. |
| Compliment | The customer likes a feature and shares their views about it |
| Others | Feedback that does not fit into the above categories. |

**Secondary Tag – Which product area is impacted?**

| Category | Description |
|---|---|
| UI/UX | Frontend, interface, design, and usability. |
| Backend/logic | Backend functionality and business logic. |
| Performance | Speed, latency, and application responsiveness. |
| Integrations | Connections with external systems and services. |
| Billing/pricing | Payments, subscriptions, invoices, and pricing. |
| Data | Data quality, records, reporting, and data management. |
| Onboarding (signup) | Registration, account setup, and initial user experience. |
| Other | Product areas outside the above categories. |

**Step 4 – Structured output**

The application appends two new columns, `Primary tag` and `Secondary tag`, to the uploaded Excel worksheet, preserving the original feedback and associated data.

Users can preview the categorized feedback directly within the application and download the enriched Excel file.

**Step 5 – AI-generated feedback summary**

Beyond individual classification, the tool generates a consolidated summary of the analyzed feedback.

The summary highlights:
- Recurring customer pain points.
- Common feature requests and enhancement opportunities.
- Distribution of feedback across primary categories.
- Product areas attracting the most feedback.
- Potential follow-up areas for product teams to investigate.

Users can copy the summary directly from the application for use in product discussions, reviews, and planning sessions.

## 4. Product Thinking Behind the Solution

The objective was not simply to build an AI tool that categorizes text. The focus was on solving a practical problem in the Product Owner's workflow.

Some of the key product decisions behind the application include:

- **Human-in-the-loop approach:** The application recommends the feedback column but allows the user to validate or change it. This avoids making assumptions about the user's data.
- **Controlled classification taxonomy:** Predefined categories ensure that feedback is classified consistently rather than allowing AI to generate arbitrary labels. Additionally, separating the nature of feedback from the impacted product area provides a more useful view of the product backlog.
- **Scalability considerations:** Batch processing and configurable row limits help manage API requests and prevent unnecessarily large analysis jobs.
- **Actionable output:** The tool goes beyond tagging individual comments by generating a consolidated summary that helps product teams identify themes and potential opportunities.
- **Simplicity of experience:** The interface is intentionally minimal, allowing users to focus on uploading, validating, and analyzing feedback without needing to understand the underlying AI configuration.

## 5. Expected Product Value

The tool aims to help product teams:

- Reduce the manual effort involved in reviewing customer feedback.
- Bring greater consistency to feedback categorization.
- Identify recurring customer problems and unmet needs.
- Understand which product areas generate the most feedback.
- Accelerate the conversion of customer feedback into potential product opportunities.
- Spend more time interpreting insights and making product decisions rather than manually organizing data.

**Important:** AI-generated classifications and summaries are intended to support product discovery and decision-making, not replace Product Owner judgment. Feedback should still be reviewed in context before being translated into roadmap priorities or development commitments.

## 6. Future Enhancements

Potential areas for future development:

- Ability to manually correct AI-generated tags.
- Trend analysis across multiple feedback uploads.
- Visual dashboards showing feedback distribution over time.
