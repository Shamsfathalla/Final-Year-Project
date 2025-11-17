# Weekly Supervision Meeting Minutes

## Weekly Supervision Meeting 1 Minutes

### Meeting Details

| | |
| :--- | :--- |
| **Project Title:** | Car World Website |
| **Student:** | Shams Abdelaziz |
| **Date:** | 2025-10-21 |
| **Attendees:** | Mostafa Badr, Shams Abdelaziz |

---

### 1. Agenda

*Brief points we planned to discuss.*

1. Discuss the project idea and goals.
2. Set goals and action items for the coming week.

---

### 2. Student's Progress This Week

*Student's summary of work completed since the last meeting, tracked by deliverable.*

* **Proposal & Thesis:**
  * None yet, this was the first meeting.
* **Research Paper:**
  * None yet, this was the first meeting.
* **Software Application:**
  * None yet, this was the first meeting.

---

### 3. Discussion Points & Blockers

*Key topics discussed, decisions made, and problems identified.*

* **Discussion:**
  * Explored the importance of building a layered application that can be scalable and maintainable.
  * Explored data collection steps and ways to build a data access and validation layer as a base for the project and any ML/DL models.
  * Explored examples of the ML/DL models we plan to integrate into the application.
* **Blockers:**
  * Current datasets are not updated with the car market's evolution.
  * Uncertinaty of what could be the first model we build and how can we put this work into a research paper.

---

### 4. Action Items (Student)

*Specific, achievable tasks for the student to complete by the next meeting.*

* **Deliverable: Proposal & Thesis**
    1. None yet, the idea is still raw.
* **Deliverable: Research Paper**
    1. None yet, the idea is still raw.
* **Deliverable: Software Application**
    1. Set up a github repo and add me as collaborator.
    2. Initaily ask claude for the best organization of your repo so that the project is layered and scalable.
    3. Create a list for the car brands and their official websites that we can scrape.

---

### 5. Action Items (Supervisor)

*Tasks for me to complete to support the student.*

1. Create the meeting minutes and share it on the student's repo as an .MD file.
2. Create my own list of car brands in egypt and their official websites, taking into consideration the top selling ones.
3. Propose more than 1 technical stack for implementing this project and checking with the student about the most fit with his knowledge.

---

### 6. Goals for Next Meeting

*The main objective(s) for the next session.*

* **Primary Goal:** Complete a list of the column names needed to be scraped for collecting our dataset.

---

### 7. Long-Term Milestone Check-in

*Brief status update on the overall project plan.*

* **Current Phase:** Initail project exploration.
* **Status:** On track.
* **Next Major Milestone:** Builing our dataset.

---

**Date of Next Meeting:** [2025-10-27]

---
---
---

## Weekly Supervision Meeting 2 Minutes

### Meeting Details

| | |
| :--- | :--- |
| **Project Title:** | Car World Website |
| **Student:** | Shams Abdelaziz |
| **Date:** | 2025-10-27 |
| **Attendees:** | Mostafa Badr, Shams Abdelaziz |

---

### 1. Agenda

*Brief points we planned to discuss.*

1. Review progress on last week's action items.
2. Discuss the sources we will scrape car data from (Car brands sheet).
3. Discuss the technical stack to use.
4. Discuss the AI Models to build in order (Car price prediction, 2 Tower user-car recommendation, AI search Agents)
5. Review the roadmap for the whole project.

---

### 2. Student's Progress This Week

*Student's summary of work completed since the last meeting, tracked by deliverable.*

* **Proposal & Thesis:**
  * Will start searching for papers on Car price predictions, car-user recommendations, and search agent for cars.
* **Research Paper:**
  * Will start searching for papers on Car price predictions, car-user recommendations, and search agent for cars.
* **Software Application:**
  * We greed on the stack to use, started scraping Nissan's official webpage.

---

### 3. Discussion Points & Blockers

*Key topics discussed, decisions made, and problems identified.*

* **Discussion:**
  * Which models we will try to build in order (car prediction, car-user recommendation twin-tower model, and AI search agent for Cars)
* **Blockers:**
  * Some websites don't contain all the data and some don't allow traditional scraping methods.
  * We still don't have research papers to use for lit. review.

---

### 4. Action Items (Student)

*Specific, achievable tasks for the student to complete by the next meeting.*

* **Deliverable: Proposal & Thesis**
    1. Create your NotebookLM notebook based on the research paper I (Mostafa) will provide as a start.
    2. Build on the sheet for research papers and try to increase their number.
* **Deliverable: Research Paper**
    1. Same as **Deliverable: Proposal & Thesis**
* **Deliverable: Software Application**
    1. Write 3 scraping scripts for the top selling new cars from their official websites.
    2. Compare the different scraping tools (scrapy, Playwright, selenium, others) through videos.
    3. Look at FastAPI and React.js crash courses.

---

### 5. Action Items (Supervisor)

*Tasks for me to complete to support the student.*

1. Update the meeting minutes shared on the student's repo as an .MD file.
2. Create a list of research papers on Car price prediction, car-user recommendation (2 tower), AI search agent for cars.  
3. Look for scraping tools.

---

### 6. Goals for Next Meeting

*The main objective(s) for the next session.*

* **Primary Goal:** Start using NotebookLM to find the gaps in research to address.

---

### 7. Long-Term Milestone Check-in

*Brief status update on the overall project plan.*

* **Current Phase:** Inital backend development.
* **Status:** On track.
* **Next Major Milestone:** Building our dataset.

---

**Date of Next Meeting:** [2025-11-3]

---
---
---

## Weekly Supervision Meeting 3 Minutes

### Meeting Details

| | |
| :--- | :--- |
| **Project Title:** | Car World Website |
| **Student:** | Shams Abdelaziz |
| **Date:** | [2025-11-3] |
| **Attendees:** | Mostafa Badr, Shams Abdelaziz |

---

### 1. Agenda

*Brief points we planned to discuss.*

1. Review progress on last week's action items.
2. Discussed the car brands websites scraped.
3. Discussed the technical stack to use.
4. Discussed the AI models to build.

---

### 2. Student's Progress This Week

*Student's summary of work completed since the last meeting, tracked by deliverable.*

* **Proposal & Thesis:**
  * Decided on 3 models to try to build in order:
    1. The "Multi-Modal Valuation" System (Car Damage/Condition Detection (Computer Vision) + Used Car Price Prediction (Regression)).
    2. Advanced AI Search Agent (LLM/RAG) (API based).
    3. The "Guided Purchase" System (Recommender System (Content-Based) + Monthly Ranking Model (Learning-to-Rank)).
    4. New Car Price Prediction (Unannounced).
* **Research Paper:**
  * Same as **Proposal & Thesis:**
* **Software Application:**
  * Scraped websites for 5 brands.
  * Compared the different scraping tools.

---

### 3. Discussion Points & Blockers

*Key topics discussed, decisions made, and problems identified.*

* **Discussion:**
  * The order of AI models implementations.
  * The research process and NotebookLm usage.
* **Blockers:**
  * None.

---

### 4. Action Items (Student)

*Specific, achievable tasks for the student to complete by the next meeting.*

* **Deliverable: Proposal & Thesis**
    1. Sheet of papers on Car Damage/Condition Detection (Computer Vision) using SciSpace.
* **Deliverable: Research Paper**
    1. Same as **Deliverable: Proposal & Thesis**
* **Deliverable: Software Application**
    1. Search for a javascript course online.

---

### 5. Action Items (Supervisor)

*Tasks for me to complete to support the student.*

1. Create the meeting minutes and share it on the student's repo as an .MD file.
2. Filter the Used Car Price Prediction (Regression) papers listed in the sheet.
3. Download the Used Car Price Prediction (Regression) papers listed in the sheet.

---

### 6. Goals for Next Meeting

*The main objective(s) for the next session.*

* **Primary Goal:** Using NotebookLm for literature review + Evaluating our progress on the javascript course.

---

### 7. Long-Term Milestone Check-in

*Brief status update on the overall project plan.*

* **Current Phase:** Initial research steps and learning for implementation.
* **Status:** On track.
* **Next Major Milestone:** Writing literature review and introduction sections of the paper.

---

**Date of Next Meeting:** [2025-11-10]

---
---
---

## Weekly Supervision Meeting 4 Minutes

### Meeting Details

| | |
| :--- | :--- |
| **Project Title:** | Car World Website |
| **Student:** | Shams Abdelaziz |
| **Date:** | [2025-11-10] |
| **Attendees:** | Mostafa Badr, Shams Abdelaziz |

---

### 1. Agenda

*Brief points we planned to discuss.*

1. Review progress on last week's action items.
2. Review SciSpace outputs and how to scrape it.
3. Discuss the process to generate literature review using NotebookLm.
4. Discuss how to get a methodology using previous research and then NotebookLm.

---

### 2. Student's Progress This Week

*Student's summary of work completed since the last meeting, tracked by deliverable.*

* **Proposal & Thesis:**
  * Completed the sheet of papers on Car Damage/Condition Detection (Computer Vision) using SciSpace.
* **Research Paper:**
  * Same as **Proposal & Thesis:**
* **Software Application:**
  * A part of the JavaScript coarse we proposed was done, the rest will also be done before next Meeting.

---

### 3. Discussion Points & Blockers

*Key topics discussed, decisions made, and problems identified.*

* **Discussion:**
  * Scraping the papers collected from SciSpace.
  * How to use NotebookLm to write a complete literature review.
  * How to build a methodology.
* **Blockers:**
  * None.

---

### 4. Action Items (Student)

*Specific, achievable tasks for the student to complete by the next meeting.*

* **Deliverable: Proposal & Thesis**
    1. Filter the papers of Car Damage/Condition Detection (Computer Vision).
    2. Download them and upload them to NotebookLm in a separate notebook.
    3. Split your literature review into sections based on literature review of previous papers.
    4. For each section, write a prompt for NotebookLm to write a complete section of the literature review.
    5. Gather the sections and write the complete literature review with citations.
    6. Read and refine the literature review and share it with me.
    7. Write a sample of what we will be doing in the methodology.
* **Deliverable: Research Paper**
    1. Set an overleaf project with IEEE template of a conference paper and share it with me.
* **Deliverable: Software Application**
    1. Finish the rest of the JavaScript course.
    2. Decide which NodeJs course to take.

---

### 5. Action Items (Supervisor)

*Tasks for me to complete to support the student.*

1. Create the meeting minutes and share it on the student's repo as an .MD file.
2. Download all the papers of Used Car Price Prediction (Regression) listed in the sheet and share the folder.
3. Create another sheet of papers for the Multi-Modal Valuation System.
4. Download all the papers of Multi-Modal Valuation System listed in the sheet and share the folder.
5. Propose a methodology for the project.

---

### 6. Goals for Next Meeting

*The main objective(s) for the next session.*

* **Primary Goal:** Getting 3 literature reviews (Used car + Car Damage + Multi-Modal Valuation) and Review the methodology.

---

### 7. Long-Term Milestone Check-in

*Brief status update on the overall project plan.*

* **Current Phase:** Literature review writing and methodology ideation
* **Status:** On track
* **Next Major Milestone:** e.g., Mid-term progress report (Due: 2025-12-8)

---

**Date of Next Meeting:** [2025-11-17]

---
---
---

## Weekly Supervision Meeting 5 Minutes

### Meeting Details

| | |
| :--- | :--- |
| **Project Title:** | Car World Website |
| **Student:** | Shams Abdelaziz |
| **Date:** | [2025-11-17] |
| **Attendees:** | Mostafa Badr, Shams Abdelaziz |

---

### 1. Agenda

*Brief points we planned to discuss.*

1. Review progress on last week's action items.
2. Explain the way to filter papers.

---

### 2. Student's Progress This Week

*Student's summary of work completed since the last meeting, tracked by deliverable.*

* **Proposal & Thesis:**
  * Filter the papers of Car Damage/Condition Detection (Computer Vision).
  * Download the papers of Car Damage/Condition Detection (Computer Vision).
* **Research Paper:**
  * Set an overleaf project with IEEE template of a conference paper and share it with me.
* **Software Application:**
  * Finish the rest of the JavaScript course.

---

### 3. Discussion Points & Blockers

*Key topics discussed, decisions made, and problems identified.*

* **Discussion:**
  * The need for a task on javascript course.
  * The way of filtering papers.
* **Blockers:**
  * None.

---

### 4. Action Items (Student)

*Specific, achievable tasks for the student to complete by the next meeting.*

* **Deliverable: Proposal & Thesis**
    1. Upload Car Damage papers to NotebookLm in a separate notebook.
    2. Split your literature review into sections based on literature review of previous papers.
    3. For each section, write a prompt for NotebookLm to write a complete section of the literature review.
    4. Gather the sections and write the complete literature review with citations.
    5. Read and refine the literature review and share it with me.
    6. Write a sample of what we will be doing in the methodology.
* **Deliverable: Research Paper**
    1. Same as **Deliverable: Proposal & Thesis**
* **Deliverable: Software Application**
    1. Decide which NodeJs course to take.
    2. Finish the Full-Stack ML Prediction App Task.

---

### 5. Action Items (Supervisor)

*Tasks for me to complete to support the student.*

1. Create the meeting minutes and share it on the student's repo as an .MD file.
2. Download all the papers of Multi-Modal Valuation System listed in the sheet and share the folder.
3. Propose a methodology for the project.

---

### 6. Goals for Next Meeting

*The main objective(s) for the next session.*

* **Primary Goal:** Getting 3 literature reviews (Used car + Car Damage + Multi-Modal Valuation) and Proposing the methodology.

---

### 7. Long-Term Milestone Check-in

*Brief status update on the overall project plan.*

* **Current Phase:** Literature review writing and methodology ideation
* **Status:** On track
* **Next Major Milestone:** e.g., Mid-term progress report (Due: 2025-12-8)

---

**Date of Next Meeting:** [2025-11-24]

---
---
---

## Weekly Supervision Meeting Minutes TEMPLATE

### Meeting Details

| | |
| :--- | :--- |
| **Project Title:** | Car World Website |
| **Student:** | Shams Abdelaziz |
| **Date:** | [YYYY-MM-DD] |
| **Attendees:** | Mostafa Badr, Shams Abdelaziz |

---

### 1. Agenda

*Brief points we planned to discuss.*

1. Review progress on last week's action items.
2. 
3. 
4. 
5. 

---

### 2. Student's Progress This Week

*Student's summary of work completed since the last meeting, tracked by deliverable.*

* **Proposal & Thesis:**
  * 
  * 
* **Research Paper:**
  * 
  * 
* **Software Application:**
  * 
  * 

---

### 3. Discussion Points & Blockers

*Key topics discussed, decisions made, and problems identified.*

* **Discussion:**
  * 
  * 
* **Blockers:**
  * 
  * 

---

### 4. Action Items (Student)

*Specific, achievable tasks for the student to complete by the next meeting.*

* **Deliverable: Proposal & Thesis**
    1. 
    2. 
* **Deliverable: Research Paper**
    1. 
* **Deliverable: Software Application**
    1. 
    2. 

---

### 5. Action Items (Supervisor)

*Tasks for me to complete to support the student.*

1. Create the meeting minutes and share it on the student's repo as an .MD file.
2. 
3. 

---

### 6. Goals for Next Meeting

*The main objective(s) for the next session.*

* **Primary Goal:** [e.g., Review the complete draft of the Methodology (Thesis) and finalize the technology stack for the web application.]

---

### 7. Long-Term Milestone Check-in

*Brief status update on the overall project plan.*

* **Current Phase:** [e.g., Phase 2: Data Acquisition & Methodology]
* **Status:** [e.g., On track / Slightly behind / Ahead of schedule]
* **Next Major Milestone:** [e.g., Mid-term progress report (Due: YYYY-MM-DD)]

---

**Date of Next Meeting:** [YYYY-MM-DD]
