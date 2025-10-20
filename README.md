# End-to-End A/B Testing Data Analysis

## 1. Project Overview

This project simulates a real-world e-commerce A/B testing scenario, aiming to optimize user conversion rates through a data-driven approach. We designed and implemented a complete end-to-end data pipeline, covering the entire process from front-end data collection, multi-source data integration, cloud data warehouse processing, and in-depth analysis to final business intelligence (BI) reporting.

**Business Problem:** To increase the click-through rate of a "Buy Now" button on a simulated product page, we designed two versions (Version A: blue button, Version B: green button). An A/B test was conducted to scientifically determine which design yields a higher user conversion rate.

## 2. Technical Architecture

### Final Technical Architecture Diagram

*<img width="886" height="622" alt="flow" src="https://github.com/user-attachments/assets/4bf3d3bb-bd51-4548-ab49-11c8e214d7f9" />*

### Technology Stack

- **Data Simulation:** Python (Selenium)
- **Data Collection:** Google Analytics 4 (GA4), Google Tag Manager (GTM)
- **Raw Data Landing & EDA:**
  - Structured/Event Data: Google BigQuery
  - Semi-structured/Qualitative Data: MongoDB Atlas
  - Cloud Storage: Google Cloud Storage (GCS)
- **Data Warehouse:** Snowflake
- **Data Transformation & Analysis:** Snowflake SQL, Python (SciPy)
- **Data Visualization:** Power BI

## 3. Project Workflow

### Phase 1: Data Collection and Simulation

- **A/B Test Website Setup:** Created two HTML pages (`index.html` and `version_b.html`) on GitHub Pages, representing Version A (blue button) and Version B (green button) respectively.

- **Tracking Deployment:** Deployed GA4 tracking code using GTM and configured custom events (`purchase_click`) and custom dimensions (`test_version`) to capture and differentiate user behavior across versions.

- **Simulating Quantitative Data:** Developed a Python Selenium script to automate nearly a thousand user visits. The script is capable of:
  - Randomly assigning users to either Group A or Group B.
  - Simulating different devices and browsers via User-Agents.
  - Randomly deciding whether to click the "Buy Now" button based on preset conversion rates. *(Note: Due to multiple rounds of testing with different parameters, the final observed conversion rates for both versions were around 5%).*
  
  All user behavior data was captured by GA4 and automatically exported to Google BigQuery.

- **Simulating Qualitative Data:** Enhanced the Selenium script to generate detailed user feedback with a certain probability after a simulated conversion. This semi-structured data, stored in MongoDB Atlas, includes:
  - `comment_text` (Textual comments)
  - `star_rating` (1-5 star ratings)
  - `tags` (Array of feedback tags)
  - `time_to_convert_seconds` (Time to conversion)

### Phase 2: Data Extraction and Loading (ELT)

- **Extract (E) from BigQuery:**
  - Used SQL in BigQuery to perform initial flattening (`UNNEST`) and cleaning of the raw, nested GA4 event data, extracting key fields like `user_pseudo_id`, `event_name`, and `test_version`.
  - Exported this clean intermediate table, `ab_test_base_data`, as a CSV file to Google Cloud Storage (GCS).

- **Extract (E) from MongoDB:**
  - To bypass the instability of the MongoDB Atlas web UI export feature, we adopted the more professional `mongoexport` command-line tool to export all documents from the `user_comments` collection into a local `user_comments.json` file.

- **Load (L) into Snowflake:**
  - **Quantitative Data:** Created a Storage Integration and an External Stage in Snowflake pointing to GCS. The `COPY INTO` command was then used to efficiently bulk-load the CSV data from GCS into the `AB_TEST_BASE_DATA` table.
  - **Qualitative Data:** Used Snowflake's intuitive Load Data web wizard to upload the local `user_comments.json` file into a `USER_FEEDBACK` table, leveraging the `VARIANT` data type to handle the semi-structured JSON.

### Phase 3: Data Transformation and Analysis (within Snowflake)

- **Transform (T) Quantitative Data:** Used SQL Common Table Expressions (CTEs) within Snowflake to perform the final transformation on the `AB_TEST_BASE_DATA` table. This generated a clean `AB_TEST_RESULTS` table where each row represents a unique visitor, marked with a boolean field `IS_CONVERTED`.

- **Transform (T) Qualitative Data:** Leveraged Snowflake's native JSON parsing capabilities to flatten the `VARIANT` column in the `USER_FEEDBACK` table, extracting fields like `star_rating` and `tags` into a new `USER_FEEDBACK_PARSED` table.

- **Quantitative Analysis:**
  - Calculated the total visitors, total conversions, and conversion rates for both versions using SQL aggregate queries.
  - Performed a Chi-Squared Test on the query results using a local Python script to determine if the observed difference in conversion rates was statistically significant.

- **Qualitative Analysis:**
  - Calculated the average star rating for each version using SQL aggregate queries.
  - Utilized the `LATERAL FLATTEN` function to expand the `tags` array and identify the most frequently mentioned feedback tags for each version.

### Phase 4: Data Visualization

Created an interactive dashboard in Power BI by connecting directly to Snowflake, visualizing the A/B test results from various dimensions.

<img width="1646" height="794" alt="image" src="https://github.com/user-attachments/assets/da51abe3-ee12-4655-9302-97f528760922" />

## 4. Challenges & Learnings

During the project's exploration phase, our initial plan was to adopt a classic ETL architecture: Source -> Databricks (PySpark) -> Warehouse. However, we encountered two significant blockers:

First, the latest Databricks Free Trial version could not support our intended PySpark ETL workflow. After in-depth investigation, I identified two core technical limitations:

1. **Inability to Create General-Purpose Clusters:** The new Free Trial has removed the functionality to create All-Purpose Clusters, which are essential for running Python and PySpark and form the basis of traditional Databricks workflows.

2. **Limited SQL Warehouse Functionality:** We attempted to attach an interactive Notebook to the provided Serverless SQL Warehouse, but the system explicitly stated that this compute resource is strictly limited to executing SQL commands and cannot run non-SQL (e.g., PySpark) code cells.

Therefore, to continue attempting the project with PySpark, I decided to deploy a local PySpark environment.

While I initially faced and successfully resolved several environment configuration challenges (such as implicit dependency version conflicts between connectors), a second major obstacle emerged: when configuring the connection to Snowflake, despite smooth connections to BigQuery and MongoDB, we consistently encountered connection timeouts and SSL certificate errors due to incorrect account identifier formats.

<details>
<summary>Click to expand for details on the Snowflake connection errors.</summary>

We tried multiple URL combinations, including formats recommended by official documentation and those found in community forums, but none could establish a connection to Snowflake. The error messages were varied and included:

- `ERROR RestRequest: Error response: HTTP Response code: 404`
- `net.snowflake.client.jdbc.SnowflakeSQLException: JDBC driver encountered communication error. Message: HTTP status=404`
- `ERROR RestRequest: Stop retrying since elapsed time due to network issues has reached timeout.`
- And, most revealingly, a certificate mismatch error: `javax.net.ssl.SSLPeerUnverifiedException: Certificate for <...> doesn't match any of the subject alternative names: [...]`

These errors proved that despite trying multiple URL formats that included server provider and geographic location information, the client was consistently unable to correctly resolve the server for the Snowflake account.
</details>

Given these persistent issues, and to ensure the robust delivery of the project, I made a decisive architectural pivot, bypassing the PySpark step. I moved the transformation (T) phase downstream, allowing it to be performed entirely within the Snowflake data warehouse using SQL.

This experience not only resolved all environment configuration problems but also better simulated the "decoupling" philosophy of modern data pipelines, enhancing the stability and efficiency of the entire process. I have archived the final PySpark code as part of the project, with the aim of identifying the root cause of the bottleneck in the future.

## 5. Project Code and Replication

- `/simulation_scripts`: Contains the Python Selenium script for data simulation.
- `/sql_scripts`: Contains all SQL analysis code used in BigQuery and Snowflake.
- `/analysis_scripts`: Contains the Python script for the Chi-Squared Test.
- `/bi_reports`: Contains the Power BI (.pbix) report file.
- `/other`: Contains other files, such as the PySpark code.

## 6. Final Conclusion

**Quantitative Analysis Conclusion:** Version A had a conversion rate of 5.98%, while Version B had 5.19%. The Chi-Squared Test yielded a P-value of 0.9407, which is much greater than 0.05. Therefore, there is not enough statistical evidence to conclude that Version A is better than Version B; the observed difference is likely due to random chance.

**Qualitative Analysis Insights:**

- The average star rating for Version B was significantly higher than for Version A.
- Feedback tags for Version B were predominantly positive, such as "good_design" and "easy_to_use", whereas Version A received more negative tags like "plain_design" and "confusing".

**Final Business Recommendation:** Although the quantitative test was inconclusive, the strong qualitative evidence leads to a strong recommendation to adopt the design of Version B (the green button). It demonstrates clear advantages in user satisfaction and perception, suggesting greater potential for positive business impact in a larger-scale or longer-term test.
